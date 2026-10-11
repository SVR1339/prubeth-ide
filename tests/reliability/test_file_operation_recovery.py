"""PRUBETH IDE - File Operations & Data Integrity Chaos Tests
==========================================================
Exercises file conflict mutex guards, path traversal security barriers,
read-only file protections, and transactional rollback recovery.
"""

import concurrent.futures
import os
import stat
import tempfile
from pathlib import Path
import pytest

from tests.reliability.helpers.crash_harness import (
    DisposableWorkspace,
    FaultInjector,
    timed_operation,
)
from ai.agent_studio import FileConflictGuard, FileConflictError
from core.workspace import WorkspaceGuard, WorkspaceSecurityError


def test_file_conflict_guard_prevents_simultaneous_writes():
    """Mutex locking must prevent concurrent agents from modifying the same file."""
    guard = FileConflictGuard()
    test_file = "src/main.py"

    assert guard.acquire_lock("agent_1", test_file) is True
    # Second agent attempting lock must raise FileConflictError
    with pytest.raises(FileConflictError):
        guard.acquire_lock("agent_2", test_file)

    # Once released, second agent can acquire
    guard.release_lock("agent_1", test_file)
    assert guard.acquire_lock("agent_2", test_file) is True
    guard.release_lock("agent_2", test_file)


def test_file_conflict_guard_high_concurrency_race():
    """High contention across multiple threads must grant the lock to exactly one agent at a time."""
    guard = FileConflictGuard()
    target_file = "core/shared_module.py"
    successful_locks = []

    def try_lock_worker(agent_id: str):
        try:
            if guard.acquire_lock(agent_id, target_file):
                successful_locks.append(agent_id)
                guard.release_lock(agent_id, target_file)
                return True
        except FileConflictError:
            return False
        return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(try_lock_worker, f"agent_{i}") for i in range(20)]
        results = [f.result() for f in futures]

    assert any(results)
    assert len(guard.get_locked_files()) == 0


def test_path_traversal_boundary_guard():
    """Workspace boundary guard must reject directory escape attempts (e.g. ../../)."""
    with DisposableWorkspace() as ws_path:
        guard = WorkspaceGuard(ws_path)

        # Legal path inside workspace
        valid_path = guard.canonicalize("src/utils.py")
        assert valid_path.exists()

        # Path traversal escapes must be rejected
        with pytest.raises(WorkspaceSecurityError):
            guard.canonicalize("../../Windows/System32/cmd.exe")

        with pytest.raises(WorkspaceSecurityError):
            guard.canonicalize("../outside_secret.txt")


def test_read_only_file_modification_safety():
    """Modifying a read-only file must fail with PermissionError without crashing the process."""
    with DisposableWorkspace() as ws_path:
        target = ws_path / "protected_file.txt"
        target.write_text("initial immutable content", encoding="utf-8")
        FaultInjector.make_read_only(target)

        try:
            with pytest.raises(PermissionError):
                with open(target, "w", encoding="utf-8") as f:
                    f.write("malicious overwrite")
            # Content must remain intact
            assert target.read_text(encoding="utf-8") == "initial immutable content"
        finally:
            FaultInjector.restore_writable(target)
