"""PRUBETH IDE - Shutdown & Clean Exit Chaos Tests
================================================
Exercises application shutdown behavior under active background operations,
worker cancellation propagation, and state persistence on close.
"""

import threading
import time
import pytest
from tests.reliability.helpers.crash_harness import (
    DisposableWorkspace,
    ResourceLeakDetector,
    timed_operation,
)
from core.future_compat import ISchedulerEngineV2, SemanticContractVersion


class MockScheduler(ISchedulerEngineV2):
    def __init__(self):
        self._tasks = {}
        self._canceled = set()

    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V2_0

    def submit(self, task_name, fn, *args, **kwargs):
        tid = f"task_{len(self._tasks)}"
        self._tasks[tid] = {"name": task_name, "status": "running"}
        return tid

    def submit_priority(self, task_name, priority, fn, *args, **kwargs):
        return self.submit(task_name, fn, *args, **kwargs)

    def cancel_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = "canceled"
            self._canceled.add(task_id)
            return True
        return False

    def get_status(self, task_id: str):
        return self._tasks.get(task_id, {"status": "unknown"})

    def get_worker_utilization(self):
        return {"active": len([t for t in self._tasks.values() if t["status"] == "running"])}

    def shutdown_all(self):
        for tid in list(self._tasks):
            self.cancel_task(tid)


def test_shutdown_with_active_background_tasks():
    """Shutdown must cancel all active tasks and release workers within deadline."""
    scheduler = MockScheduler()

    t1 = scheduler.submit("heavy_indexing", lambda: time.sleep(10))
    t2 = scheduler.submit("model_streaming", lambda: time.sleep(10))

    assert scheduler.get_status(t1)["status"] == "running"
    assert scheduler.get_status(t2)["status"] == "running"

    with timed_operation(2.0):
        scheduler.shutdown_all()

    assert scheduler.get_status(t1)["status"] == "canceled"
    assert scheduler.get_status(t2)["status"] == "canceled"
    assert scheduler.get_worker_utilization()["active"] == 0


def test_disposable_workspace_cleanup_on_abrupt_exit():
    """DisposableWorkspace must clean up all temporary directories even when an exception occurs."""
    workspace_ref = None
    try:
        with DisposableWorkspace() as ws:
            workspace_ref = ws
            assert workspace_ref.exists()
            raise RuntimeError("Simulated crash during task execution")
    except RuntimeError:
        pass

    assert workspace_ref is not None
    # Directory must be purged on exit
    assert not workspace_ref.exists()
