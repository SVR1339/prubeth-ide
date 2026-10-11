"""
Gate 15: Persistent Agent Memory Store — Integration Tests
Tests: WorkingMemory, EpisodicMemoryStore, SemanticSearch, and AgentMemory façade.
"""
import time
import pytest
from pathlib import Path
from antigravity.memory_store import (
    WorkingMemory, EpisodicMemoryStore, MemoryEntry, AgentMemory
)


# ─── Test 1: WorkingMemory scratchpad with TTL expiry ─── #
def test_working_memory_set_get_expiry():
    """WorkingMemory stores values and correctly expires them after TTL."""
    wm = WorkingMemory(max_slots=10)

    wm.set("plan", {"steps": [1, 2, 3]}, ttl_seconds=60.0)
    wm.set("ephemeral", "quick note", ttl_seconds=0.01)

    assert wm.get("plan") == {"steps": [1, 2, 3]}
    assert wm.get("nonexistent", "fallback") == "fallback"

    time.sleep(0.05)  # Wait for ephemeral TTL to expire
    assert wm.get("ephemeral") is None   # Should be expired
    assert wm.get("plan") == {"steps": [1, 2, 3]}  # Still alive

    # Snapshot should only return non-expired entries
    snap = wm.snapshot()
    assert "plan" in snap
    assert "ephemeral" not in snap


# ─── Test 2: WorkingMemory max slot eviction ─── #
def test_working_memory_max_slots_eviction():
    """WorkingMemory evicts the oldest slot when max_slots is exceeded."""
    wm = WorkingMemory(max_slots=3)
    wm.set("a", 1, ttl_seconds=None)
    time.sleep(0.01)
    wm.set("b", 2, ttl_seconds=None)
    time.sleep(0.01)
    wm.set("c", 3, ttl_seconds=None)
    time.sleep(0.01)
    # Adding "d" should evict "a" (oldest)
    wm.set("d", 4, ttl_seconds=None)
    assert wm.get("a") is None    # Evicted
    assert wm.get("d") == 4
    assert len(wm) == 3


# ─── Test 3: EpisodicMemoryStore store and retrieve by task ─── #
def test_episodic_memory_store_and_retrieve(tmp_path):
    """EpisodicMemoryStore persists memories to SQLite and retrieves by task_id."""
    db_path = tmp_path / "test_memory.db"
    store = EpisodicMemoryStore(db_path=db_path)

    # Store 3 memories for a task
    m1 = store.store(MemoryEntry(
        task_id="task-001", summary="Read the spec file for auth module",
        content="Content: def authenticate(user): ...",
        tags=["auth", "read"], importance=0.6
    ))
    m2 = store.store(MemoryEntry(
        task_id="task-001", summary="Wrote unit tests for auth",
        content="def test_auth(): ...", tags=["auth", "tests"], importance=0.7
    ))
    m3 = store.store(MemoryEntry(
        task_id="task-002", summary="Refactored database layer",
        content="class DB: ...", tags=["db"], importance=0.8
    ))

    # Retrieve by task
    task1_memories = store.retrieve_by_task("task-001")
    assert len(task1_memories) == 2
    assert all(m.task_id == "task-001" for m in task1_memories)

    task2_memories = store.retrieve_by_task("task-002")
    assert len(task2_memories) == 1

    # Verify total count
    assert store.count() == 3

    # Retrieve by tags
    auth_memories = store.retrieve_by_tags(["auth"])
    assert len(auth_memories) == 2


# ─── Test 4: Semantic memory search ─── #
def test_episodic_memory_semantic_search(tmp_path):
    """SemanticMemorySearch returns relevant memories ranked by cosine similarity."""
    db_path = tmp_path / "semantic_test.db"
    store = EpisodicMemoryStore(db_path=db_path)

    store.store(MemoryEntry(
        summary="Fixed authentication bug in login module",
        content="Changed password hashing algorithm from MD5 to bcrypt",
        tags=["auth", "security", "bug"]
    ))
    store.store(MemoryEntry(
        summary="Added retry logic to HTTP client",
        content="Implemented exponential backoff for network failures",
        tags=["network", "resilience"]
    ))
    store.store(MemoryEntry(
        summary="Optimized database query performance",
        content="Added composite index on user_id and timestamp columns",
        tags=["database", "performance"]
    ))

    # Search for authentication-related memories
    results = store.search_semantic("authentication login security bug", top_k=3, min_similarity=0.0)
    assert len(results) > 0

    # The auth-related memory should have a higher similarity than the database one
    auth_result = next((r for r in results if "authentication" in r[0].summary.lower()), None)
    db_result = next((r for r in results if "database" in r[0].summary.lower()), None)

    if auth_result and db_result:
        assert auth_result[1] >= db_result[1]   # Auth should be more similar to auth query


# ─── Test 5: AgentMemory unified façade ─── #
def test_agent_memory_facade(tmp_path):
    """AgentMemory provides a unified API combining working and episodic memory."""
    db_path = tmp_path / "agent_facade.db"
    mem = AgentMemory(task_id="task-facade", db_path=db_path)

    # Working memory operations
    mem.working.set("current_file", "main.py", ttl_seconds=60.0)
    assert mem.working.get("current_file") == "main.py"

    # Episodic memory via remember()
    entry = mem.remember(
        summary="Successfully implemented user authentication endpoint",
        content="POST /api/auth returns JWT on valid credentials",
        memory_type="episodic",
        tags=["auth", "api", "jwt"],
        importance=0.9
    )
    assert entry.memory_id.startswith("mem-")
    assert entry.task_id == "task-facade"

    # Recall returns relevant memories
    recalled = mem.recall("JWT authentication API endpoint", top_k=3)
    assert len(recalled) > 0
    assert any("authentication" in r.summary.lower() for r in recalled)

    # Context string building for ReAct injection
    ctx_str = mem.build_memory_context("authentication JWT")
    assert "RELEVANT PAST MEMORIES" in ctx_str
    assert len(ctx_str) > 0
