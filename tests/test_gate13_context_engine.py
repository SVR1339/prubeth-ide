"""
Gate 13: AST-Aware Context Window Manager — Integration Tests
Tests: ASTSkeletonizer, SemanticChunker, ContextWindow, and ContextAssembler.
"""
import time
import pytest
from horizon_engine.context_engine import (
    ASTSkeletonizer, SemanticChunker, ContextWindow, ContextEntry, ContextAssembler
)


# ─── Test 1: ASTSkeletonizer ─── #
def test_ast_skeletonizer_extracts_signatures():
    """Skeletonizer extracts class and function symbols with correct metadata."""
    source = '''
class DataProcessor:
    """Processes incoming data streams."""

    def __init__(self, max_batch: int = 32):
        self.max_batch = max_batch

    def process(self, data: list) -> list:
        """Transforms raw data entries."""
        return [x * 2 for x in data]

    async def flush(self) -> None:
        """Asynchronously flushes the buffer."""
        pass


def standalone_helper(x: int, y: int) -> int:
    """Adds two integers."""
    return x + y
'''
    sk = ASTSkeletonizer()
    symbols = sk.skeletonize_source(source, "processor.py")

    names = [s.name for s in symbols]
    assert "DataProcessor" in names
    assert "process" in names
    assert "flush" in names
    assert "standalone_helper" in names

    # Verify class symbol
    cls_sym = next(s for s in symbols if s.name == "DataProcessor")
    assert cls_sym.symbol_type == "class"
    assert "DataProcessor" in cls_sym.signature
    assert "Processes incoming data streams" in (cls_sym.docstring or "")

    # Verify async function
    flush_sym = next(s for s in symbols if s.name == "flush")
    assert flush_sym.parent_class == "DataProcessor"
    assert flush_sym.symbol_type == "method"

    # Verify token estimate is non-zero
    for sym in symbols:
        assert sym.token_estimate > 0

    # Verify skeleton text renders correctly
    skeleton_text = sk.build_skeleton_text(symbols, "processor.py")
    assert "# processor.py" in skeleton_text
    assert "DataProcessor" in skeleton_text
    assert "standalone_helper" in skeleton_text


# ─── Test 2: ASTSkeletonizer handles syntax errors gracefully ─── #
def test_ast_skeletonizer_handles_syntax_error():
    """Skeletonizer returns empty list for unparseable source — never raises."""
    broken = "def broken_function(:\n    pass"
    sk = ASTSkeletonizer()
    symbols = sk.skeletonize_source(broken, "broken.py")
    assert symbols == []   # Graceful degradation, no exception


# ─── Test 3: SemanticChunker splits at class/function boundaries ─── #
def test_semantic_chunker_logical_boundaries():
    """SemanticChunker respects Python AST boundaries, not raw line counts."""
    source = '''
import os
import sys


class AnalyticsEngine:
    """Computes analytics over datasets."""

    def compute(self) -> float:
        """Returns a float result."""
        return 3.14

    def reset(self) -> None:
        """Resets internal state."""
        pass


def utility_function():
    """A standalone utility."""
    return 42
'''
    chunker = SemanticChunker()
    chunks = chunker.chunk_source(source, "analytics.py", max_chunk_tokens=100)

    # Should have at least: imports, class_body or methods, standalone function
    assert len(chunks) >= 2
    chunk_types = {c.chunk_type for c in chunks}
    # Must produce some recognized chunk type
    assert chunk_types & {"imports", "class_body", "function_body", "module_header"}

    # Every chunk must have a valid chunk_id and positive token estimate
    for chunk in chunks:
        assert chunk.chunk_id.startswith("chunk-")
        assert chunk.token_estimate > 0
        assert chunk.file_path == "analytics.py"


# ─── Test 4: ContextWindow manages token budget and eviction ─── #
def test_context_window_token_budget_and_eviction():
    """ContextWindow enforces max_tokens budget and evicts LRU entries."""
    window = ContextWindow(max_tokens=100)

    # Add entry within budget
    e1 = ContextEntry(entry_id="e1", source="skeleton", content="A" * 80,
                      token_cost=20, priority=0.5)
    assert window.add_entry(e1) is True
    assert window.used_tokens == 20

    # Add second entry filling 80 of 100 tokens
    e2 = ContextEntry(entry_id="e2", source="chunk", content="B" * 240,
                      token_cost=60, priority=0.3)
    assert window.add_entry(e2) is True
    assert window.used_tokens == 80

    # Third entry (30 tokens) forces eviction of e2 (lowest priority)
    e3 = ContextEntry(entry_id="e3", source="directive", content="C" * 120,
                      token_cost=30, priority=0.9)
    assert window.add_entry(e3) is True
    # e2 (priority=0.3) should be evicted, e1 (priority=0.5) retained
    assert window.get_entry("e2") is None
    assert window.get_entry("e1") is not None
    assert window.get_entry("e3") is not None

    # Verify usage stats
    stats = window.get_usage_stats()
    assert stats["used_tokens"] <= stats["max_tokens"]
    assert 0 <= stats["utilization_pct"] <= 100


# ─── Test 5: ContextWindow TTL expiry ─── #
def test_context_window_ttl_expiry():
    """Expired entries are evicted from the window automatically."""
    window = ContextWindow(max_tokens=1000)

    # Entry with 0.01s TTL (expires almost immediately)
    short_entry = ContextEntry(
        entry_id="short", source="tool_output", content="ephemeral data",
        token_cost=5, priority=0.8, ttl_seconds=0.01
    )
    window.add_entry(short_entry)
    assert window.get_entry("short") is not None

    time.sleep(0.05)  # Wait for TTL to expire

    # Trigger eviction via add_entry
    trigger = ContextEntry(entry_id="trigger", source="directive", content="new data",
                           token_cost=1, priority=0.5)
    window.add_entry(trigger)

    # The expired entry should now be gone
    assert window.get_entry("short") is None


# ─── Test 6: ContextAssembler builds structured context string ─── #
def test_context_assembler_builds_ordered_context():
    """ContextAssembler groups entries by source type and orders them correctly."""
    window = ContextWindow(max_tokens=5000)
    assembler = ContextAssembler(window)

    # Add a steering directive (highest priority)
    assembler.add_steering_directive("Focus only on the authentication module.", author="human")

    # Add a tool output with short TTL
    assembler.add_tool_output("read_file", "def login(user: str) -> bool: ...", priority=0.8)

    # Verify context string is built
    context = assembler.build_context_string()
    assert "DIRECTIVE" in context
    assert "Focus only on the authentication module" in context
    assert "TOOL OUTPUT" in context or "tool_output" in context.lower() or "read_file" in context

    # Verify stats
    stats = window.get_usage_stats()
    assert stats["entry_count"] == 2
    assert stats["used_tokens"] > 0
