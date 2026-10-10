"""
Unit and Integration Tests for Workspace Management & Multi-File Checkpoint Rollback
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest
from core.workspace import WorkspaceGuard, WorkspaceSecurityError
from workspace.checkpoints import CheckpointManager, compute_sha256


@pytest.fixture
def temp_workspace():
    tmp_dir = tempfile.mkdtemp(prefix="test_sukhi_ws_")
    ws_path = Path(tmp_dir)
    guard = WorkspaceGuard(ws_path)
    mgr = CheckpointManager(guard)
    yield ws_path, guard, mgr
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_checkpoint_creation_and_listing(temp_workspace):
    ws_path, guard, mgr = temp_workspace
    c1 = mgr.begin_checkpoint("Initial state")
    c2 = mgr.begin_checkpoint("Feature branch")

    chks = mgr.list_checkpoints()
    assert len(chks) == 2
    ids = [c["checkpoint_id"] for c in chks]
    assert c1 in ids
    assert c2 in ids


def test_single_file_modification_and_rollback(temp_workspace):
    ws_path, guard, mgr = temp_workspace
    test_file = ws_path / "hello.py"
    test_file.write_text("print('version 1')\n", encoding="utf-8")

    cid = mgr.begin_checkpoint("Edit hello.py")
    mgr.track_file_before_edit(cid, str(test_file))

    # Perform edit
    test_file.write_text("print('version 2 modified')\n", encoding="utf-8")
    mgr.track_file_after_edit(cid, str(test_file))

    # Verify modified
    assert "version 2 modified" in test_file.read_text(encoding="utf-8")

    # Rollback
    res = mgr.rollback(cid)
    assert res["success"] is True
    assert "hello.py" in res["restored_files"]
    assert test_file.read_text(encoding="utf-8") == "print('version 1')\n"


def test_multi_file_atomic_rollback(temp_workspace):
    ws_path, guard, mgr = temp_workspace
    f1 = ws_path / "main.py"
    f2 = ws_path / "config.json"
    f3_new = ws_path / "new_helper.py"

    f1.write_text("def run(): return 1\n", encoding="utf-8")
    f2.write_text('{"debug": false}', encoding="utf-8")

    cid = mgr.begin_checkpoint("Multi-file agent task")

    # Track pre-edits
    mgr.track_file_before_edit(cid, str(f1))
    mgr.track_file_before_edit(cid, str(f2))
    mgr.track_file_before_edit(cid, str(f3_new))  # does not exist yet

    # Agent performs edits
    f1.write_text("def run(): return 999\n", encoding="utf-8")
    f2.write_text('{"debug": true, "extra": 42}', encoding="utf-8")
    f3_new.write_text("def helper(): pass\n", encoding="utf-8")

    mgr.track_file_after_edit(cid, str(f1))
    mgr.track_file_after_edit(cid, str(f2))
    mgr.track_file_after_edit(cid, str(f3_new))

    assert f3_new.exists()

    # Rollback entire checkpoint
    res = mgr.rollback(cid)
    assert res["success"] is True
    assert "main.py" in res["restored_files"]
    assert "config.json" in res["restored_files"]
    assert "new_helper.py" in res["deleted_files"]

    # Verify original states
    assert f1.read_text(encoding="utf-8") == "def run(): return 1\n"
    assert f2.read_text(encoding="utf-8") == '{"debug": false}'
    assert not f3_new.exists()


def test_checkpoint_rejection_of_traversal(temp_workspace):
    ws_path, guard, mgr = temp_workspace
    cid = mgr.begin_checkpoint("Traversal test")

    with pytest.raises(WorkspaceSecurityError):
        mgr.track_file_before_edit(cid, "../outside_file.txt")
