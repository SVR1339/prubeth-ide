"""
SUKHI IDE — Gate 9 Automated Test Suite
Verifies Transactional Checkpoints:
- Pre-edit content hashing and change capture
- Two-phase atomic rollback (reverting modified files, deleting created files)
- Cross-session disk persistence and reload
- Atomic shadow recovery under simulated disk failure injection
- Double rollback safety
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch

from core.workspace import WorkspaceGuard
from workspace.checkpoints import CheckpointManager


def test_checkpoint_lifecycle_and_atomic_rollback():
    """Verify modification tracking, new file deletion, and exact byte restoration."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_chk_test_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        mgr = CheckpointManager(workspace_guard=guard)

        # 1. Setup existing file
        existing_file = temp_dir / "app.py"
        existing_file.write_text("print('version 1.0')\n", encoding="utf-8")

        # 2. Begin checkpoint
        c_id = mgr.begin_checkpoint("Feature update v2")

        # 3. Track existing file before edit
        mgr.track_file_before_edit(c_id, "app.py")

        # 4. Modify existing file
        guard.safe_write("app.py", "print('version 2.0 with bugs')\n")
        mgr.track_file_after_edit(c_id, "app.py")

        # 5. Create new file under this checkpoint
        mgr.track_file_before_edit(c_id, "new_module.py")
        guard.safe_write("new_module.py", "# brand new file\n")
        mgr.track_file_after_edit(c_id, "new_module.py")

        assert existing_file.read_text(encoding="utf-8") == "print('version 2.0 with bugs')\n"
        assert (temp_dir / "new_module.py").exists()

        # 6. Execute atomic rollback
        res = mgr.rollback(c_id)
        assert res["success"] is True
        assert "app.py" in res["restored_files"]
        assert "new_module.py" in res["deleted_files"]

        # Verify filesystem state matches pre-checkpoint exact state
        assert existing_file.read_text(encoding="utf-8") == "print('version 1.0')\n"
        assert not (temp_dir / "new_module.py").exists()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_checkpoint_persistence_across_sessions():
    """Checkpoints must persist to disk and reload in a new CheckpointManager instance."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_chk_persist_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        mgr1 = CheckpointManager(workspace_guard=guard)

        file1 = temp_dir / "config.json"
        file1.write_text('{"env": "test"}', encoding="utf-8")

        c_id = mgr1.begin_checkpoint("Persistence verification")
        mgr1.track_file_before_edit(c_id, "config.json")
        guard.safe_write("config.json", '{"env": "production"}')
        mgr1.track_file_after_edit(c_id, "config.json")

        # Initialize fresh CheckpointManager (simulating IDE restart)
        mgr2 = CheckpointManager(workspace_guard=guard)
        chk = mgr2.get_checkpoint(c_id)

        assert chk is not None
        assert chk.description == "Persistence verification"
        assert "config.json" in chk.snapshots
        assert chk.snapshots["config.json"].existed_before is True

        # Perform rollback from the reloaded instance
        res = mgr2.rollback(c_id)
        assert res["success"] is True
        assert file1.read_text(encoding="utf-8") == '{"env": "test"}'

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_failure_injection_atomic_recovery():
    """When disk restoration encounters an error, rollback must abort and preserve live shadow state."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_chk_inject_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        mgr = CheckpointManager(workspace_guard=guard)

        file_a = temp_dir / "a.py"
        file_a.write_text("a_v1", encoding="utf-8")
        file_b = temp_dir / "b.py"
        file_b.write_text("b_v1", encoding="utf-8")

        c_id = mgr.begin_checkpoint("Multi-file batch")
        mgr.track_file_before_edit(c_id, "a.py")
        mgr.track_file_before_edit(c_id, "b.py")

        guard.safe_write("a.py", "a_v2")
        guard.safe_write("b.py", "b_v2")

        # Inject simulated failure during safe_write during rollback
        original_safe_write = guard.safe_write
        def buggy_safe_write(path, content, backup=True):
            if "b.py" in str(path):
                raise OSError("Simulated hardware write fault / file locked by external process")
            return original_safe_write(path, content, backup)

        with patch.object(guard, "safe_write", side_effect=buggy_safe_write):
            res = mgr.rollback(c_id)
            assert res["success"] is False
            assert "Transactional rollback failed" in res["error"]

        # Ensure shadow recovery protected state: a.py and b.py retained their v2 state rather than partial half-revert
        assert file_a.read_text(encoding="utf-8") == "a_v2"
        assert file_b.read_text(encoding="utf-8") == "b_v2"

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_double_rollback_safety():
    """Rolling back an already rolled-back checkpoint must return clean refusal without side effects."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_chk_double_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        mgr = CheckpointManager(workspace_guard=guard)

        f = temp_dir / "data.txt"
        f.write_text("initial", encoding="utf-8")

        c_id = mgr.begin_checkpoint("Double rollback test")
        mgr.track_file_before_edit(c_id, "data.txt")
        guard.safe_write("data.txt", "modified")

        # First rollback succeeds
        r1 = mgr.rollback(c_id)
        assert r1["success"] is True

        # Second rollback safely rejected
        r2 = mgr.rollback(c_id)
        assert r2["success"] is False
        assert "already rolled back" in r2["error"]

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
