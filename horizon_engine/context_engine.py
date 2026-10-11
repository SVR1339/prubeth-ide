"""
PRUBETH IDE — PRUBETH Horizon AST-Aware Context Window Manager
Solves the Token Budget & Context Pollution problem for long-running agentic tasks.

Research Foundation:
  - SWE-bench (Jimenez et al., 2023): Autonomous issue resolution requires precise
    context management — loading the entire repo into context causes hallucination.
  - Tree-sitter Skeletonization: Strip function bodies, keep signatures & docstrings,
    compressing large repos into minimal representative tokens.
  - Hierarchical summarization: Semantic chunking respects logical code boundaries
    (class definitions, function scopes) rather than raw line counts.

Architecture:
  1. ASTSkeletonizer:   Extracts symbol signatures from Python files via ast module
  2. SemanticChunker:   Splits files into logically-bounded chunks (class/function scope)
  3. ContextEntry:      A single scored, expirable context slot with token cost tracking
  4. ContextWindow:     Priority-ordered token budget manager for LLM context assembly
  5. ContextAssembler:  Builds final context string within model token limits
"""
import ast
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


# ---------------------------------------------------------------------------
# AST Skeletonizer — strips bodies, retains signatures & docstrings
# ---------------------------------------------------------------------------

@dataclass
class SkeletonSymbol:
    """Lightweight symbol extracted from AST skeleton pass."""
    name: str
    symbol_type: str           # "class", "function", "method", "async_function"
    signature: str             # Full def/class signature line
    docstring: Optional[str]
    file_path: str
    line_start: int
    line_end: int
    parent_class: Optional[str] = None
    decorators: List[str] = field(default_factory=list)

    @property
    def token_estimate(self) -> int:
        """Rough token estimate: ~4 chars per token."""
        total_chars = len(self.signature) + len(self.docstring or "") + sum(len(d) for d in self.decorators)
        return max(4, total_chars // 4)

    def to_skeleton_text(self) -> str:
        """Renders a compact skeleton representation."""
        parts = []
        for dec in self.decorators:
            parts.append(f"  {dec}" if self.parent_class else dec)
        indent = "    " if self.parent_class else ""
        parts.append(f"{indent}{self.signature}: ...")
        if self.docstring:
            short_doc = self.docstring[:120].replace("\n", " ").strip()
            parts.append(f'{indent}    """{short_doc}"""')
        return "\n".join(parts)


class ASTSkeletonizer:
    """
    Extracts lightweight function/class signatures from Python source files.
    Compresses a 5000-line module to ~200 tokens of navigable skeleton.
    """

    def skeletonize_source(self, source: str, file_path: str = "<source>") -> List[SkeletonSymbol]:
        """Parses Python source and returns list of SkeletonSymbols (no bodies)."""
        symbols: List[SkeletonSymbol] = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return symbols

        lines = source.splitlines()
        self._walk_node(tree, lines, file_path, symbols, parent_class=None)
        return symbols

    def skeletonize_file(self, file_path: Path) -> List[SkeletonSymbol]:
        """Reads a file and returns its AST skeleton."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []
        return self.skeletonize_source(source, str(file_path))

    def _walk_node(self, node: ast.AST, lines: List[str], file_path: str,
                   symbols: List[SkeletonSymbol], parent_class: Optional[str]):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym = self._extract_function(child, lines, file_path, parent_class)
                if sym:
                    symbols.append(sym)
                # Recurse into nested classes only (not nested functions to keep it shallow)
            elif isinstance(child, ast.ClassDef):
                sym = self._extract_class(child, lines, file_path)
                if sym:
                    symbols.append(sym)
                # Recurse into class body for methods
                self._walk_node(child, lines, file_path, symbols, parent_class=child.name)

    def _extract_function(self, node: ast.FunctionDef, lines: List[str],
                          file_path: str, parent_class: Optional[str]) -> Optional[SkeletonSymbol]:
        try:
            sig_line = lines[node.lineno - 1].rstrip() if node.lineno <= len(lines) else ""
            docstring = ast.get_docstring(node) or None
            decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list] if node.decorator_list else []
            sym_type = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            if parent_class:
                sym_type = "method"
            return SkeletonSymbol(
                name=node.name,
                symbol_type=sym_type,
                signature=sig_line.strip(),
                docstring=docstring,
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                parent_class=parent_class,
                decorators=decorators
            )
        except Exception:
            return None

    def _extract_class(self, node: ast.ClassDef, lines: List[str],
                       file_path: str) -> Optional[SkeletonSymbol]:
        try:
            sig_line = lines[node.lineno - 1].rstrip() if node.lineno <= len(lines) else ""
            docstring = ast.get_docstring(node) or None
            decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list] if node.decorator_list else []
            return SkeletonSymbol(
                name=node.name,
                symbol_type="class",
                signature=sig_line.strip(),
                docstring=docstring,
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                decorators=decorators
            )
        except Exception:
            return None

    def build_skeleton_text(self, symbols: List[SkeletonSymbol], file_path: str = "") -> str:
        """Renders a complete skeleton document grouped by class."""
        if not symbols:
            return ""
        parts = []
        if file_path:
            parts.append(f"# {file_path}")
        current_class: Optional[str] = None
        for sym in symbols:
            if sym.symbol_type == "class":
                current_class = sym.name
                parts.append("")
                parts.append(sym.to_skeleton_text())
            elif sym.parent_class:
                if sym.parent_class != current_class:
                    current_class = sym.parent_class
                parts.append(sym.to_skeleton_text())
            else:
                current_class = None
                parts.append("")
                parts.append(sym.to_skeleton_text())
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Semantic Chunker — splits files at logical boundaries
# ---------------------------------------------------------------------------

@dataclass
class SemanticChunk:
    """A logically-bounded segment of a source file."""
    chunk_id: str
    file_path: str
    content: str
    start_line: int
    end_line: int
    chunk_type: str        # "class_body", "function_body", "module_header", "imports"
    symbol_name: Optional[str] = None
    token_estimate: int = 0

    def __post_init__(self):
        if self.token_estimate == 0:
            self.token_estimate = max(1, len(self.content) // 4)


class SemanticChunker:
    """
    Splits source files into semantically-bounded chunks.
    Respects class and function boundaries to preserve logical coherence.
    """

    def chunk_source(self, source: str, file_path: str = "<source>",
                     max_chunk_tokens: int = 400) -> List[SemanticChunk]:
        """Parses source and splits into semantic chunks respecting AST boundaries."""
        chunks: List[SemanticChunk] = []
        lines = source.splitlines()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            # If unparseable, fall back to line-based chunking
            return self._line_chunk_fallback(source, file_path, max_chunk_tokens)

        # Extract module-level imports block
        import_lines = [
            (i + 1, l) for i, l in enumerate(lines)
            if l.strip().startswith(("import ", "from "))
        ]
        if import_lines:
            start = import_lines[0][0]
            end = import_lines[-1][0]
            content = "\n".join(l for _, l in import_lines)
            chunk = SemanticChunk(
                chunk_id=self._make_id(file_path, start, "imports"),
                file_path=file_path,
                content=content,
                start_line=start,
                end_line=end,
                chunk_type="imports"
            )
            chunks.append(chunk)

        # Chunk top-level classes and functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_content = "\n".join(lines[node.lineno - 1:(node.end_lineno or node.lineno)])
                if len(class_content) // 4 > max_chunk_tokens:
                    # Chunk each method separately
                    for child in ast.iter_child_nodes(node):
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            method_content = "\n".join(lines[child.lineno - 1:(child.end_lineno or child.lineno)])
                            chunk = SemanticChunk(
                                chunk_id=self._make_id(file_path, child.lineno, "method"),
                                file_path=file_path,
                                content=method_content,
                                start_line=child.lineno,
                                end_line=child.end_lineno or child.lineno,
                                chunk_type="function_body",
                                symbol_name=f"{node.name}.{child.name}"
                            )
                            chunks.append(chunk)
                else:
                    chunk = SemanticChunk(
                        chunk_id=self._make_id(file_path, node.lineno, "class"),
                        file_path=file_path,
                        content=class_content,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        chunk_type="class_body",
                        symbol_name=node.name
                    )
                    chunks.append(chunk)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_content = "\n".join(lines[node.lineno - 1:(node.end_lineno or node.lineno)])
                chunk = SemanticChunk(
                    chunk_id=self._make_id(file_path, node.lineno, "function"),
                    file_path=file_path,
                    content=fn_content,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    chunk_type="function_body",
                    symbol_name=node.name
                )
                chunks.append(chunk)

        return chunks if chunks else self._line_chunk_fallback(source, file_path, max_chunk_tokens)

    def _line_chunk_fallback(self, source: str, file_path: str, max_chunk_tokens: int) -> List[SemanticChunk]:
        """Fallback: splits non-parseable files by line count."""
        lines = source.splitlines()
        chunk_size = max(1, max_chunk_tokens * 4 // 80)  # Approx lines per chunk
        chunks = []
        for i in range(0, len(lines), chunk_size):
            segment = lines[i:i + chunk_size]
            start = i + 1
            end = start + len(segment) - 1
            content = "\n".join(segment)
            chunks.append(SemanticChunk(
                chunk_id=self._make_id(file_path, start, "segment"),
                file_path=file_path,
                content=content,
                start_line=start,
                end_line=end,
                chunk_type="module_header"
            ))
        return chunks

    @staticmethod
    def _make_id(file_path: str, line: int, kind: str) -> str:
        h = hashlib.md5(f"{file_path}:{line}:{kind}".encode()).hexdigest()[:8]
        return f"chunk-{h}"


# ---------------------------------------------------------------------------
# Context Entry & Context Window Manager
# ---------------------------------------------------------------------------

@dataclass
class ContextEntry:
    """A single prioritized context slot within the agent's context window."""
    entry_id: str
    source: str              # "skeleton", "chunk", "tool_output", "artifact", "directive"
    content: str
    token_cost: int
    priority: float          # 0.0 (least important) → 1.0 (highest priority)
    ttl_seconds: Optional[float] = None   # None = permanent
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds

    def score(self) -> float:
        """Scoring heuristic: priority weighted by recency decay."""
        age_seconds = time.time() - self.created_at
        recency_factor = 1.0 / (1.0 + age_seconds / 300.0)  # Decay over 5 minutes
        return self.priority * recency_factor


class ContextWindow:
    """
    Priority-ordered token-budget manager for assembling LLM context.
    Evicts expired and lowest-priority entries when the budget is exceeded.
    """

    def __init__(self, max_tokens: int = 32000):
        self.max_tokens = max_tokens
        self._entries: Dict[str, ContextEntry] = {}
        self._used_tokens: int = 0

    @property
    def used_tokens(self) -> int:
        return self._used_tokens

    @property
    def available_tokens(self) -> int:
        return max(0, self.max_tokens - self._used_tokens)

    def add_entry(self, entry: ContextEntry) -> bool:
        """
        Adds an entry to the context window.
        If budget is exceeded, evicts lowest-priority entries to make room.
        Returns True if successfully added.
        """
        # Evict expired entries first
        self._evict_expired()

        # If entry already exists, update it
        if entry.entry_id in self._entries:
            old = self._entries[entry.entry_id]
            self._used_tokens -= old.token_cost
            self._entries[entry.entry_id] = entry
            self._used_tokens += entry.token_cost
            return True

        # Check if we need to evict to make room
        if entry.token_cost > self.max_tokens:
            return False   # Single entry too large for window

        while self._used_tokens + entry.token_cost > self.max_tokens:
            if not self._evict_lowest_priority():
                return False   # Cannot free enough space

        self._entries[entry.entry_id] = entry
        self._used_tokens += entry.token_cost
        return True

    def remove_entry(self, entry_id: str) -> bool:
        """Removes an entry from the window."""
        entry = self._entries.pop(entry_id, None)
        if entry:
            self._used_tokens -= entry.token_cost
            return True
        return False

    def get_entry(self, entry_id: str) -> Optional[ContextEntry]:
        return self._entries.get(entry_id)

    def list_entries(self) -> List[ContextEntry]:
        return sorted(self._entries.values(), key=lambda e: -e.score())

    def _evict_expired(self):
        expired_ids = [eid for eid, e in self._entries.items() if e.is_expired]
        for eid in expired_ids:
            self.remove_entry(eid)

    def _evict_lowest_priority(self) -> bool:
        if not self._entries:
            return False
        lowest = min(self._entries.values(), key=lambda e: e.score())
        self.remove_entry(lowest.entry_id)
        return True

    def get_usage_stats(self) -> Dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "used_tokens": self._used_tokens,
            "available_tokens": self.available_tokens,
            "entry_count": len(self._entries),
            "utilization_pct": round(self._used_tokens / self.max_tokens * 100, 1)
        }


# ---------------------------------------------------------------------------
# Context Assembler — builds final context string from window
# ---------------------------------------------------------------------------

class ContextAssembler:
    """
    Assembles the final context string from a ContextWindow for injection into LLM prompts.
    Groups entries by source type for structured presentation.
    """

    def __init__(self, context_window: ContextWindow):
        self.window = context_window
        self.skeletonizer = ASTSkeletonizer()

    def build_context_string(self) -> str:
        """Builds ordered, grouped context string from all window entries."""
        entries = self.window.list_entries()
        if not entries:
            return ""

        groups: Dict[str, List[ContextEntry]] = {}
        for entry in entries:
            groups.setdefault(entry.source, []).append(entry)

        sections: List[str] = []

        # Ordering: directives first, then artifacts, skeletons, chunks, tool_output
        order = ["directive", "artifact", "skeleton", "chunk", "tool_output"]
        remaining_keys = [k for k in groups if k not in order]

        for key in order + remaining_keys:
            if key not in groups:
                continue
            group = groups[key]
            label = key.upper().replace("_", " ")
            sections.append(f"\n--- {label} CONTEXT ---")
            for entry in group:
                sections.append(entry.content)

        return "\n".join(sections)

    def add_file_skeleton(self, file_path: Path, priority: float = 0.7,
                          ttl_seconds: Optional[float] = None) -> int:
        """
        Skeletonizes a source file and adds it to the context window.
        Returns number of tokens consumed.
        """
        symbols = self.skeletonizer.skeletonize_file(file_path)
        if not symbols:
            return 0

        skeleton_text = self.skeletonizer.build_skeleton_text(symbols, str(file_path))
        token_cost = max(1, len(skeleton_text) // 4)

        entry = ContextEntry(
            entry_id=f"skel:{file_path.name}",
            source="skeleton",
            content=skeleton_text,
            token_cost=token_cost,
            priority=priority,
            ttl_seconds=ttl_seconds,
            metadata={"file_path": str(file_path), "symbol_count": len(symbols)}
        )
        self.window.add_entry(entry)
        return token_cost

    def add_tool_output(self, tool_name: str, output: str, priority: float = 0.9,
                        ttl_seconds: float = 300.0) -> bool:
        """Adds a tool observation to the context with short TTL (expires after 5 minutes)."""
        content = f"[TOOL: {tool_name}]\n{output}"
        entry = ContextEntry(
            entry_id=f"tool:{tool_name}:{int(time.time())}",
            source="tool_output",
            content=content,
            token_cost=max(1, len(content) // 4),
            priority=priority,
            ttl_seconds=ttl_seconds
        )
        return self.window.add_entry(entry)

    def add_steering_directive(self, directive: str, author: str = "human") -> bool:
        """Adds a high-priority mid-flight steering directive (never expires)."""
        content = f"[{author.upper()} DIRECTIVE] {directive}"
        entry = ContextEntry(
            entry_id=f"dir:{hashlib.md5(directive.encode()).hexdigest()[:8]}",
            source="directive",
            content=content,
            token_cost=max(1, len(content) // 4),
            priority=1.0,
            ttl_seconds=None
        )
        return self.window.add_entry(entry)
