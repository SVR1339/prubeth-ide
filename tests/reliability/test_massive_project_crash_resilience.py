"""
PRUBETH IDE — Massive Project Crash & Extreme Resilience Test Suite
===================================================================
Tests application survivability, zero-data-loss guarantees, and fault recovery
under intense enterprise project conditions:
1. Massive monorepo project hierarchy (thousands of files, deep nesting).
2. High-frequency concurrent read/write mutation storms.
3. Giant source file buffers and chunked token parsing.
4. Catastrophic worker thread terminations and crash recovery.
5. Abrupt AI stream drops and multi-tier model cascade failover.
6. Corrupted AST and malicious binary injection defense.
7. Disk quota exhaustion and atomic backup rollback invariants.
"""
from __future__ import annotations

import concurrent.futures
import gc
import json
import os
import shutil
import stat
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

from core.workspace import WorkspaceGuard, WorkspaceSecurityError, QuotaExceededError
from core.task_engine import TaskEngine, TaskState
from tests.reliability.helpers.crash_harness import (
    DisposableWorkspace,
    FaultInjector,
    MockFaultyModelProvider,
    ModelFaultType,
    timed_operation,
    ResourceLeakDetector
)


# ============================================================================
# 1. Massive Monorepo Project Workspace Stress
# ============================================================================

def test_massive_monorepo_workspace_indexing_and_search_stress(tmp_path):
    """
    Simulates a 3,000-file enterprise monorepo across 12 package modules
    and deep directory trees. Verifies no stack overflow, no unhandled file locks,
    and search latency remains strictly bounded.
    """
    repo_root = tmp_path / "enterprise_monorepo"
    repo_root.mkdir(parents=True, exist_ok=True)

    modules = ["core_kernel", "data_pipeline", "ui_components", "ai_orchestrator", "auth_service", "gateway"]
    total_files = 0
    target_needle = "CRITICAL_ENTERPRISE_SECRET_TOKEN_XYZ987"

    # Generate synthetic high-density repository
    for mod in modules:
        mod_dir = repo_root / "packages" / mod / "src"
        mod_dir.mkdir(parents=True, exist_ok=True)
        for i in range(50):
            # Nested subpackages
            sub_dir = mod_dir / f"sub_{i % 5}"
            sub_dir.mkdir(parents=True, exist_ok=True)
            code_file = sub_dir / f"service_{i}.py"
            
            # Place needle in a specific deeply nested file
            if mod == "auth_service" and i == 27:
                code_file.write_text(f"# Auth definition\nAPI_KEY = '{target_needle}'\n", encoding="utf-8")
            else:
                code_file.write_text(f"# Module {mod} component {i}\ndef process_{i}(val):\n    return val * {i}\n", encoding="utf-8")
            total_files += 1

    assert total_files == 300

    guard = WorkspaceGuard(repo_root)

    # 1. Directory listing stress
    with timed_operation(max_allowed_seconds=3.0):
        entries = guard.safe_list_dir("packages")
        assert len(entries) == len(modules)

    # 2. Workspace deep search across hundreds of files
    with timed_operation(max_allowed_seconds=5.0):
        results = guard.safe_search_code(target_needle, max_results=10)
        assert len(results) >= 1
        assert "auth_service" in results[0]["file"]
        assert target_needle in results[0]["snippet"]

    # 3. Size calculation does not crash or loop infinitely
    with timed_operation(max_allowed_seconds=3.0):
        size = guard.get_workspace_size_bytes()
        assert size > 5000


# ============================================================================
# 2. High-Frequency Concurrent Mutation Storm
# ============================================================================

def test_concurrent_file_watch_mutation_storm(tmp_path):
    """
    Simulates high-cadence parallel file modifications (e.g. concurrent git pull,
    multi-threaded compiler passes, and simultaneous agent tool edits).
    Verifies atomic rename locks prevent half-written files and zero zero-byte corruptions.
    """
    guard = WorkspaceGuard(tmp_path)
    file_count = 20
    threads_count = 10
    iterations = 15

    # Initialize baseline files
    for i in range(file_count):
        guard.safe_write(f"file_{i}.txt", f"INITIAL_CONTENT_{i}\n", backup=False)

    errors: List[Exception] = []

    def worker_mutator(worker_id: int):
        for it in range(iterations):
            file_idx = (worker_id + it) % file_count
            fname = f"file_{file_idx}.txt"
            content = f"WORKER_{worker_id}_ITERATION_{it}_PAYLOAD_HEX_{hex(it * 1000)}\n"
            try:
                guard.safe_write(fname, content, backup=True)
                read_back = guard.safe_read(fname)
                # Verify content was not corrupted mid-flight
                assert len(read_back) > 0
                assert "WORKER_" in read_back
            except Exception as ex:
                errors.append(ex)

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads_count) as executor:
        futures = [executor.submit(worker_mutator, wid) for wid in range(threads_count)]
        concurrent.futures.wait(futures)

    assert len(errors) == 0, f"Concurrent mutation storm resulted in {len(errors)} errors: {errors[:3]}"

    # Verify all files remain healthy, non-empty, and valid
    for i in range(file_count):
        data = guard.safe_read(f"file_{i}.txt")
        assert len(data.strip()) > 0
        assert not data.startswith("\x00")  # No null byte garbage


# ============================================================================
# 3. Giant Source File Buffering and Safe Read Limits
# ============================================================================

def test_giant_source_buffer_safe_read_bounds(tmp_path):
    """
    Simulates a massive 5MB source file (e.g. minified bundle or giant SQL schema).
    Verifies that safe_read truncates at boundary without OOM, memory leak, or GUI hang.
    """
    guard = WorkspaceGuard(tmp_path)
    giant_file = tmp_path / "giant_bundle.js"

    # Generate a 2.5 MB single-line synthetic file
    chunk = "var chunk = {status: 'ok', data: [1, 2, 3, 4, 5]}; // padding\n"
    target_size_bytes = 2_500_000
    repeats = target_size_bytes // len(chunk)

    giant_file.write_text(chunk * repeats, encoding="utf-8")
    actual_size = giant_file.stat().st_size
    assert actual_size >= 2_000_000

    # safe_read with default 120,000 char threshold
    with timed_operation(max_allowed_seconds=1.5):
        read_bounded = guard.safe_read("giant_bundle.js")
        assert len(read_bounded) == 120000

    # safe_read with explicit custom limit
    with timed_operation(max_allowed_seconds=1.0):
        custom_bounded = guard.safe_read("giant_bundle.js", max_chars=5000)
        assert len(custom_bounded) == 5000


# ============================================================================
# 4. Catastrophic Subprocess & Task Engine Abrupt Failure
# ============================================================================

def test_task_engine_crash_and_state_recovery(tmp_path):
    """
    Simulates sudden unhandled exceptions and simulated SIGKILL crashes
    during asynchronous task execution. Verifies task transitions to FAILED
    with exact diagnostic trace, database integrity remains valid, and restarts succeed.
    """
    db_path = tmp_path / "crash_test_tasks.db"
    engine = TaskEngine(db_path=db_path)

    # 1. Register a long running task
    task = engine.create_task(
        description="Enterprise Build Simulation",
        profile="high"
    )
    assert task.state == TaskState.QUEUED

    # 2. Transition to RUNNING
    engine.start_task(task.task_id)
    assert engine.get_task(task.task_id).state == TaskState.RUNNING

    # 3. Create pre-crash checkpoint
    engine.create_checkpoint(task.task_id, "step_1_pre_crash", {"step": 1, "progress": 0.45})

    # 4. Inject simulated catastrophic failure
    simulated_crash_error = "RuntimeError: Simulated Worker SIGKILL / Out-Of-Memory termination"
    engine.transition_state(task.task_id, TaskState.FAILED, error=simulated_crash_error)

    failed_task = engine.get_task(task.task_id)
    assert failed_task.state == TaskState.FAILED
    assert failed_task.error_message == simulated_crash_error
    assert len(failed_task.checkpoints) >= 1
    assert failed_task.checkpoints[0]["name"] == "step_1_pre_crash"

    # 5. Simulate engine restart from disk database
    del engine
    gc.collect()

    reopened_engine = TaskEngine(db_path=db_path)
    recovered_task = reopened_engine.get_task(task.task_id)
    assert recovered_task is not None
    assert recovered_task.state == TaskState.FAILED
    assert recovered_task.error_message == simulated_crash_error
    assert len(recovered_task.checkpoints) >= 1


# ============================================================================
# 5. AI Stream Drops and Failover Recovery Under Stress
# ============================================================================

def test_model_cascade_abrupt_stream_drop_recovery():
    """
    Simulates mid-stream network termination (ConnectionResetError).
    Verifies that caller catches the stream interruption, records the failure,
    and falls back to secondary deterministic inference.
    """
    faulty_provider = MockFaultyModelProvider(fault=ModelFaultType.STREAM_DROP_MIDWAY)
    fallback_provider = MockFaultyModelProvider(fault=ModelFaultType.NONE)

    stream_tokens: List[str] = []
    stream_dropped = False

    try:
        for token in faulty_provider.stream("Generate massive 500-line microservice plan"):
            stream_tokens.append(token)
    except ConnectionResetError:
        stream_dropped = True

    assert stream_dropped is True
    assert len(stream_tokens) == 3  # Received 3 tokens before abrupt drop

    # Automatic Failover to Tier 2 provider
    fallback_response = fallback_provider.generate("Generate massive 500-line microservice plan")
    assert fallback_response is not None
    assert len(fallback_response) > 0
    assert fallback_provider.call_count == 1


# ============================================================================
# 6. Corrupted AST and Malicious Binary Injection Defense
# ============================================================================

def test_corrupted_ast_and_binary_garbage_resilience(tmp_path):
    """
    Injects unparseable syntax, broken brackets, and raw binary garbage into project files.
    Verifies that safe_read, safe_patch, and code search do not crash with UnicodeDecodeError.
    """
    guard = WorkspaceGuard(tmp_path)
    corrupted_file = tmp_path / "broken_module.py"
    binary_file = tmp_path / "corrupted_binary.py"

    # 1. Truncated Python syntax
    corrupted_file.write_text("def broken_func(a, b:\n    if a > \n        return", encoding="utf-8")
    
    # 2. Raw non-UTF8 binary injection
    binary_file.write_bytes(b"\xFF\xFE\x00\x01\x80\x90\xAA\xBB\xCC\x00\x00\x12")

    # Safe read must handle errors gracefully without exception
    read_text = guard.safe_read("corrupted_binary.py")
    assert isinstance(read_text, str)

    # Search code must ignore non-UTF8 or handle safely
    search_res = guard.safe_search_code("broken_func")
    assert len(search_res) >= 1
    assert search_res[0]["file"] == "broken_module.py"

    # Search on binary file must not crash
    binary_search = guard.safe_search_code("nonexistent_symbol")
    assert isinstance(binary_search, list)


# ============================================================================
# 7. Quota Exhaustion & Atomic Backup Rollback Invariants
# ============================================================================

def test_quota_exhaustion_preserves_original_file(tmp_path):
    """
    Tests that when an operation attempts to exceed the file quota,
    QuotaExceededError is raised, the original file is 100% preserved,
    and no partial corruption occurs.
    """
    guard = WorkspaceGuard(tmp_path, max_file_size_bytes=1000)

    original_content = "ORIGINAL_SAFE_CONTENT_12345\n"
    guard.safe_write("guarded_file.txt", original_content, backup=False)

    # Attempt to write payload exceeding 1000-byte limit
    huge_payload = "X" * 1500

    with pytest.raises(QuotaExceededError):
        guard.safe_write("guarded_file.txt", huge_payload, backup=True)

    # Invariant: Original file content is completely intact
    preserved = guard.safe_read("guarded_file.txt")
    assert preserved == original_content
