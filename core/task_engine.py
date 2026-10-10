"""
SO NAIVE IDE — Persistent Task Engine & Recovery Lifecycle
Provides explicit task state machines, cancellation tokens, step checkpoints,
and bounded recovery loops.
"""
import time
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class TaskState(str, Enum):
    QUEUED = "queued"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    step_id: int
    tool: str
    args: Dict[str, Any]
    status: str = "pending"
    result: str = ""
    evidence: str = ""


@dataclass
class Task:
    task_id: str
    description: str
    profile: str = "medium"
    state: TaskState = TaskState.QUEUED
    parent_id: Optional[str] = None
    steps: List[TaskStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    is_cancelled: bool = False
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)


class TaskEngine:
    """Manages active tasks, enforces state transitions, and supports cancellation."""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    def create_task(self, description: str, profile: str = "medium", parent_id: Optional[str] = None) -> Task:
        t_id = f"task-{uuid.uuid4().hex[:8]}"
        task = Task(task_id=t_id, description=description, profile=profile, parent_id=parent_id)
        self._tasks[t_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def transition_state(self, task_id: str, new_state: TaskState, error: Optional[str] = None) -> Task:
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task '{task_id}' not found")

        if task.is_cancelled and new_state not in (TaskState.CANCELLED, TaskState.FAILED):
            return task

        task.state = new_state
        if error:
            task.error_message = error
        if new_state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED):
            task.completed_at = time.time()
        return task

    def cancel_task(self, task_id: str):
        task = self._tasks.get(task_id)
        if task:
            task.is_cancelled = True
            task.state = TaskState.CANCELLED
            task.completed_at = time.time()

    def add_step(self, task_id: str, tool: str, args: Dict[str, Any]) -> TaskStep:
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task '{task_id}' not found")
        step_id = len(task.steps) + 1
        step = TaskStep(step_id=step_id, tool=tool, args=args)
        task.steps.append(step)
        return step

    def complete_step(self, task_id: str, step_id: int, result: str, evidence: str = ""):
        task = self._tasks.get(task_id)
        if not task or step_id > len(task.steps):
            return
        step = task.steps[step_id - 1]
        step.status = "completed"
        step.result = result
        step.evidence = evidence

    def create_checkpoint(self, task_id: str, name: str, state_data: Dict[str, Any]):
        task = self._tasks.get(task_id)
        if task:
            task.checkpoints.append({
                "name": name,
                "timestamp": time.time(),
                "data": state_data
            })
