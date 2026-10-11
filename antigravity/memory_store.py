"""
PRUBETH IDE — Antigravity Persistent Agent Memory Store
Solves the "Context Amnesia" problem: long-running agents lose context across sessions.

Research Foundation:
  - Episodic memory in cognitive science: agents that can recall past reasoning
    episodes perform significantly better on complex multi-step tasks.
  - Retrieval-Augmented Generation (RAG): semantic search over past experiences
    allows agents to avoid re-exploring known solution paths.

Architecture:
  1. MemoryEntry:        A single episodic memory record (what happened, when, summary)
  2. WorkingMemory:      Short-term scratchpad for the active ReAct reasoning loop
  3. EpisodicMemoryStore: SQLite-backed persistent storage with metadata queries
  4. SemanticMemorySearch: Cosine similarity ranking over stored memories
"""
import time
import uuid
import sqlite3
import json
import math
import hashlib
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


# ---------------------------------------------------------------------------
# Lightweight Embedding — deterministic keyword TF-IDF style vector (no GPU)
# ---------------------------------------------------------------------------

def _text_to_vector(text: str, vocab_size: int = 256) -> List[float]:
    """
    Deterministic text-to-vector: maps text to a fixed-dimension float vector
    using character n-gram hashing. No external dependencies, no GPU needed.
    Suitable for semantic similarity ranking within an agent session.
    """
    text = text.lower()
    vec = [0.0] * vocab_size
    # Tri-gram character features
    for i in range(len(text) - 2):
        ngram = text[i:i + 3]
        idx = int(hashlib.md5(ngram.encode()).hexdigest(), 16) % vocab_size
        vec[idx] += 1.0
    # L2 normalize
    magnitude = math.sqrt(sum(v * v for v in vec))
    if magnitude > 0:
        vec = [v / magnitude for v in vec]
    return vec


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Computes cosine similarity between two L2-normalized vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    # Vectors are pre-normalized, so cosine = dot product
    return max(0.0, min(1.0, dot))


# ---------------------------------------------------------------------------
# Memory Structures
# ---------------------------------------------------------------------------

@dataclass
class MemoryEntry:
    """A single episodic memory entry in the agent's long-term store."""
    memory_id: str = field(default_factory=lambda: f"mem-{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    session_id: str = ""
    timestamp: float = field(default_factory=time.time)
    memory_type: str = "episodic"    # "episodic", "semantic", "procedural", "declarative"
    summary: str = ""                # Human-readable 1-2 sentence description of what happened
    content: str = ""                # Full detail content (tool outputs, code, etc.)
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5          # 0.0 (trivial) → 1.0 (critical)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def age_hours(self) -> float:
        return (time.time() - self.timestamp) / 3600.0

    def to_recall_text(self) -> str:
        """Returns a concise text representation for injection into agent context."""
        tag_str = f" [{', '.join(self.tags)}]" if self.tags else ""
        age_str = f"{self.age_hours:.1f}h ago"
        return f"[MEMORY {self.memory_id}]{tag_str} ({age_str}): {self.summary}"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class WorkingMemorySlot:
    """A single slot in the short-term working memory scratchpad."""
    slot_id: str
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl_seconds: Optional[float] = 300.0    # Default: expires after 5 min

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds


class WorkingMemory:
    """
    Short-term key-value scratchpad for the active ReAct reasoning loop.
    Entries expire by TTL to prevent stale data from polluting context.
    """

    def __init__(self, max_slots: int = 32):
        self.max_slots = max_slots
        self._slots: Dict[str, WorkingMemorySlot] = {}

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = 300.0):
        """Writes a value into a named scratchpad slot."""
        self._evict_expired()
        if len(self._slots) >= self.max_slots and key not in self._slots:
            # Evict oldest slot
            oldest_key = min(self._slots.keys(), key=lambda k: self._slots[k].created_at)
            del self._slots[oldest_key]
        slot = WorkingMemorySlot(
            slot_id=f"slot-{uuid.uuid4().hex[:4]}",
            key=key,
            value=value,
            ttl_seconds=ttl_seconds
        )
        self._slots[key] = slot

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a value from the scratchpad."""
        slot = self._slots.get(key)
        if slot is None or slot.is_expired:
            if key in self._slots:
                del self._slots[key]
            return default
        return slot.value

    def clear(self, key: Optional[str] = None):
        """Clears a specific key or the entire working memory."""
        if key:
            self._slots.pop(key, None)
        else:
            self._slots.clear()

    def _evict_expired(self):
        expired = [k for k, s in self._slots.items() if s.is_expired]
        for k in expired:
            del self._slots[k]

    def snapshot(self) -> Dict[str, Any]:
        """Returns all non-expired working memory as a dict."""
        self._evict_expired()
        return {k: s.value for k, s in self._slots.items()}

    def __len__(self) -> int:
        self._evict_expired()
        return len(self._slots)


# ---------------------------------------------------------------------------
# Episodic Memory Store — SQLite-backed long-term memory
# ---------------------------------------------------------------------------

class EpisodicMemoryStore:
    """
    SQLite-backed persistent memory store for multi-session agent memory.
    Stores episodic memories with metadata for retrieval by task, tag, or similarity.
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".local_ai_studio_pro" / "agent_memory.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path)
        self._in_memory_vectors: Dict[str, List[float]] = {}   # memory_id → embedding vector
        self._init_db()
        self._load_vectors()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    session_id TEXT,
                    timestamp REAL,
                    memory_type TEXT,
                    summary TEXT,
                    content TEXT,
                    tags TEXT,
                    importance REAL,
                    access_count INTEGER,
                    last_accessed REAL,
                    metadata TEXT,
                    embedding TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_id ON memories(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
            conn.commit()

    def _load_vectors(self):
        """Loads all stored embedding vectors into RAM for fast similarity search."""
        try:
            with self._conn() as conn:
                rows = conn.execute("SELECT memory_id, embedding FROM memories WHERE embedding IS NOT NULL").fetchall()
                for row in rows:
                    try:
                        self._in_memory_vectors[row["memory_id"]] = json.loads(row["embedding"])
                    except Exception:
                        pass
        except Exception:
            pass

    def store(self, entry: MemoryEntry) -> MemoryEntry:
        """Persists a memory entry with its embedding vector."""
        embedding = _text_to_vector(f"{entry.summary} {entry.content[:500]}")
        self._in_memory_vectors[entry.memory_id] = embedding

        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.memory_id, entry.task_id, entry.session_id,
                entry.timestamp, entry.memory_type, entry.summary,
                entry.content, json.dumps(entry.tags),
                entry.importance, entry.access_count, entry.last_accessed,
                json.dumps(entry.metadata), json.dumps(embedding)
            ))
            conn.commit()
        return entry

    def retrieve_by_task(self, task_id: str, limit: int = 20) -> List[MemoryEntry]:
        """Retrieves all memories for a specific task."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE task_id = ? ORDER BY timestamp DESC LIMIT ?",
                (task_id, limit)
            ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def retrieve_by_tags(self, tags: List[str], limit: int = 10) -> List[MemoryEntry]:
        """Retrieves memories matching any of the given tags."""
        results = []
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM memories ORDER BY importance DESC, timestamp DESC").fetchall()
            for row in rows:
                entry_tags = json.loads(row["tags"] or "[]")
                if any(t in entry_tags for t in tags):
                    results.append(self._row_to_entry(row))
                if len(results) >= limit:
                    break
        return results

    def search_semantic(self, query: str, top_k: int = 5,
                        min_similarity: float = 0.1) -> List[Tuple[MemoryEntry, float]]:
        """
        Semantic similarity search over all stored memories.
        Returns top_k memories ranked by cosine similarity to the query.
        """
        query_vec = _text_to_vector(query)
        scored: List[Tuple[str, float]] = []
        for memory_id, vec in self._in_memory_vectors.items():
            sim = _cosine_similarity(query_vec, vec)
            if sim >= min_similarity:
                scored.append((memory_id, sim))

        scored.sort(key=lambda x: -x[1])
        results = []
        with self._conn() as conn:
            for memory_id, sim in scored[:top_k]:
                row = conn.execute("SELECT * FROM memories WHERE memory_id = ?", (memory_id,)).fetchone()
                if row:
                    entry = self._row_to_entry(row)
                    # Update access stats
                    conn.execute("""
                        UPDATE memories SET access_count = access_count + 1, last_accessed = ?
                        WHERE memory_id = ?
                    """, (time.time(), memory_id))
                    results.append((entry, sim))
            conn.commit()
        return results

    def forget_old_memories(self, max_age_hours: float = 168.0) -> int:
        """Removes memories older than max_age_hours (default: 1 week). Returns count deleted."""
        cutoff = time.time() - max_age_hours * 3600
        with self._conn() as conn:
            result = conn.execute("DELETE FROM memories WHERE timestamp < ? AND importance < 0.8",
                                  (cutoff,))
            conn.commit()
            deleted = result.rowcount
        # Clean vectors
        with self._conn() as conn:
            live_ids = {r["memory_id"] for r in conn.execute("SELECT memory_id FROM memories").fetchall()}
        self._in_memory_vectors = {k: v for k, v in self._in_memory_vectors.items() if k in live_ids}
        return deleted

    def count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            memory_id=row["memory_id"],
            task_id=row["task_id"] or "",
            session_id=row["session_id"] or "",
            timestamp=row["timestamp"],
            memory_type=row["memory_type"] or "episodic",
            summary=row["summary"] or "",
            content=row["content"] or "",
            tags=json.loads(row["tags"] or "[]"),
            importance=row["importance"] or 0.5,
            access_count=row["access_count"] or 0,
            last_accessed=row["last_accessed"] or time.time(),
            metadata=json.loads(row["metadata"] or "{}")
        )


# ---------------------------------------------------------------------------
# Unified Agent Memory — façade combining working + episodic memory
# ---------------------------------------------------------------------------

class AgentMemory:
    """
    Unified façade providing both short-term working memory and persistent episodic memory
    for autonomous agents. Provides a simple API for storing, recalling, and context building.
    """

    def __init__(self, task_id: str = "global", db_path: Optional[Path] = None):
        self.task_id = task_id
        self.session_id = f"session-{uuid.uuid4().hex[:6]}"
        self.working = WorkingMemory()
        self.episodic = EpisodicMemoryStore(db_path=db_path)

    def remember(self, summary: str, content: str = "",
                 memory_type: str = "episodic",
                 tags: Optional[List[str]] = None,
                 importance: float = 0.5) -> MemoryEntry:
        """Commits an experience to long-term episodic memory."""
        entry = MemoryEntry(
            task_id=self.task_id,
            session_id=self.session_id,
            summary=summary,
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            importance=importance
        )
        return self.episodic.store(entry)

    def recall(self, query: str, top_k: int = 3) -> List[MemoryEntry]:
        """Retrieves the most semantically relevant memories for a given query."""
        results = self.episodic.search_semantic(query, top_k=top_k)
        return [entry for entry, _ in results]

    def build_memory_context(self, query: str, max_entries: int = 5) -> str:
        """
        Builds a context string of relevant past memories for injection into a ReAct prompt.
        """
        memories = self.recall(query, top_k=max_entries)
        if not memories:
            return ""
        lines = ["### RELEVANT PAST MEMORIES (from episodic store):"]
        for mem in memories:
            lines.append(f"  {mem.to_recall_text()}")
        return "\n".join(lines)
