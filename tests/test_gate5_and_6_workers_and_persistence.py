"""
Tests for Gate 5 & Gate 6:
Gate 5 — Background Tool Worker (QThread signals, async execution)
Gate 6 — TaskEngine SQLite Backend (persistence, restart recovery, transactions)
"""
import pytest
from core.task_engine import TaskEngine, TaskState
from local_ai_studio_pro import AgentToolEngine, ToolExecutionWorker
from PyQt5.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_task_engine_sqlite_persistence_and_recovery(tmp_path):
    db_file = tmp_path / "test_tasks.db"

    # Session 1: Create task, add steps, create checkpoints
    engine1 = TaskEngine(db_path=str(db_file))
    task1 = engine1.create_task("Multi-file refactor", profile="large")
    t_id = task1.task_id

    s1 = engine1.add_step(t_id, tool="read_file", args={"path": "main.py"})
    s2 = engine1.add_step(t_id, tool="patch_file", args={"path": "main.py", "search": "a", "replace": "b"})
    engine1.complete_step(t_id, s1.step_id, result="read 100 bytes")
    engine1.fail_step(t_id, s2.step_id, error="search string not found")

    engine1.create_checkpoint(t_id, "checkpoint-before-patch", {"modified": ["main.py"]})
    engine1.transition_state(t_id, TaskState.WAITING_APPROVAL)

    # Session 2: Fresh TaskEngine instance opening same database (simulating IDE restart)
    engine2 = TaskEngine(db_path=str(db_file))
    recovered = engine2.get_task(t_id)

    assert recovered is not None
    assert recovered.description == "Multi-file refactor"
    assert recovered.state == TaskState.WAITING_APPROVAL
    assert len(recovered.steps) == 2
    assert recovered.steps[0].tool == "read_file"
    assert recovered.steps[0].status == "completed"
    assert recovered.steps[1].tool == "patch_file"
    assert recovered.steps[1].status == "failed"
    assert len(recovered.checkpoints) == 1
    assert recovered.checkpoints[0]["name"] == "checkpoint-before-patch"

    # Verify resumable tasks
    resumables = engine2.get_resumable_tasks()
    assert any(t.task_id == t_id for t in resumables)


def test_agent_tool_engine_async_worker(tmp_path, qapp):
    tool_engine = AgentToolEngine(str(tmp_path), settings={"unrestricted_mode": True})

    # Create dummy file to test async read
    test_file = tmp_path / "async_test.txt"
    test_file.write_text("async content test", encoding="utf-8")

    completed = []
    failed = []

    worker = tool_engine.execute_tool_async(
        "read_file",
        {"path": "async_test.txt"},
        on_finished=lambda tool, res: completed.append((tool, res)),
        on_error=lambda tool, err: failed.append((tool, err))
    )

    worker.wait(5000)
    qapp.processEvents()

    assert len(completed) == 1
    assert completed[0][0] == "read_file"
    assert "async content test" in completed[0][1]
    assert len(failed) == 0
