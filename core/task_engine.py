"""
PRUBETH IDE — Persistent Task Engine & Recovery Lifecycle
Provides explicit task state machines, cancellation tokens, step checkpoints,
and bounded recovery loops.
"""
import time
import uuid
import contextlib
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path


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

    @property
    def tool_name(self) -> str:
        return self.tool

    @property
    def state(self) -> TaskState:
        if self.status == "completed":
            return TaskState.COMPLETED
        elif self.status == "failed":
            return TaskState.FAILED
        return TaskState.PENDING


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

    @property
    def goal(self) -> str:
        return self.description


class TaskEngine:
    """Manages active tasks, enforces state transitions, and supports SQLite persistence."""

    def __init__(self, db_path: Optional[str] = None):
        self._tasks: Dict[str, Task] = {}
        if db_path is None:
            config_dir = Path.home() / ".local_ai_studio_pro"
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
                self.db_path = str(config_dir / "tasks.db")
            except Exception:
                self.db_path = ":memory:"
        else:
            self.db_path = db_path

        self._init_db()
        self._load_from_db()

    @contextlib.contextmanager
    def _connection(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _get_conn(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        try:
            with self._connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        description TEXT,
                        profile TEXT,
                        state TEXT,
                        parent_id TEXT,
                        created_at REAL,
                        completed_at REAL,
                        error_message TEXT,
                        is_cancelled INTEGER
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS task_steps (
                        task_id TEXT,
                        step_id INTEGER,
                        tool TEXT,
                        args TEXT,
                        status TEXT,
                        result TEXT,
                        evidence TEXT,
                        PRIMARY KEY (task_id, step_id)
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS task_checkpoints (
                        task_id TEXT,
                        name TEXT,
                        timestamp REAL,
                        data TEXT
                    )
                """)
                conn.commit()
        except Exception:
            pass

    def _load_from_db(self):
        try:
            import json
            with self._connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM tasks")
                for r in cur.fetchall():
                    t = Task(
                        task_id=r["task_id"],
                        description=r["description"],
                        profile=r["profile"] or "medium",
                        state=TaskState(r["state"]) if r["state"] in [s.value for s in TaskState] else TaskState.QUEUED,
                        parent_id=r["parent_id"],
                        created_at=r["created_at"],
                        completed_at=r["completed_at"],
                        error_message=r["error_message"],
                        is_cancelled=bool(r["is_cancelled"])
                    )
                    self._tasks[t.task_id] = t

                cur.execute("SELECT * FROM task_steps ORDER BY task_id, step_id")
                for r in cur.fetchall():
                    if r["task_id"] in self._tasks:
                        try:
                            args_dict = json.loads(r["args"]) if r["args"] else {}
                        except Exception:
                            args_dict = {}
                        step = TaskStep(
                            step_id=r["step_id"],
                            tool=r["tool"],
                            args=args_dict,
                            status=r["status"] or "pending",
                            result=r["result"] or "",
                            evidence=r["evidence"] or ""
                        )
                        self._tasks[r["task_id"]].steps.append(step)

                cur.execute("SELECT * FROM task_checkpoints ORDER BY task_id, timestamp")
                for r in cur.fetchall():
                    if r["task_id"] in self._tasks:
                        try:
                            c_data = json.loads(r["data"]) if r["data"] else {}
                        except Exception:
                            c_data = {}
                        self._tasks[r["task_id"]].checkpoints.append({
                            "name": r["name"],
                            "timestamp": r["timestamp"],
                            "data": c_data
                        })
        except Exception:
            pass

    def _persist_task(self, task: Task):
        try:
            with self._connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR REPLACE INTO tasks (
                        task_id, description, profile, state, parent_id,
                        created_at, completed_at, error_message, is_cancelled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.task_id, task.description, task.profile, task.state.value,
                    task.parent_id, task.created_at, task.completed_at,
                    task.error_message, 1 if task.is_cancelled else 0
                ))
                conn.commit()
        except Exception:
            pass

    def _persist_step(self, task_id: str, step: TaskStep):
        try:
            import json
            with self._connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR REPLACE INTO task_steps (
                        task_id, step_id, tool, args, status, result, evidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id, step.step_id, step.tool, json.dumps(step.args),
                    step.status, step.result, step.evidence
                ))
                conn.commit()
        except Exception:
            pass

    def create_task(self, description: str = "", profile: str = "medium", parent_id: Optional[str] = None, goal: Optional[str] = None) -> Task:
        desc = description or goal or "Unnamed Task"
        t_id = f"task-{uuid.uuid4().hex[:8]}"
        task = Task(task_id=t_id, description=desc, profile=profile, parent_id=parent_id)
        self._tasks[t_id] = task
        self._persist_task(task)
        return task

    def start_task(self, task_id: str) -> Task:
        return self.transition_state(task_id, TaskState.RUNNING)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[Task]:
        return list(self._tasks.values())

    def get_resumable_tasks(self) -> List[Task]:
        """Returns tasks that can be resumed after IDE restart."""
        resumable_states = {
            TaskState.QUEUED, TaskState.PLANNING, TaskState.RUNNING,
            TaskState.WAITING_APPROVAL, TaskState.VERIFYING
        }
        return [t for t in self._tasks.values() if t.state in resumable_states and not t.is_cancelled]

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
        self._persist_task(task)
        return task

    def cancel_task(self, task_id: str):
        task = self._tasks.get(task_id)
        if task:
            task.is_cancelled = True
            task.state = TaskState.CANCELLED
            task.completed_at = time.time()
            self._persist_task(task)

    def add_step(self, task_id: str, tool: str = "", args: Optional[Dict[str, Any]] = None, description: str = "", tool_name: str = "", parameters: Optional[Dict[str, Any]] = None) -> TaskStep:
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task '{task_id}' not found")
        t_name = tool or tool_name or "unknown"
        p_args = args if args is not None else (parameters or {})
        step_id = len(task.steps) + 1
        step = TaskStep(step_id=step_id, tool=t_name, args=p_args)
        task.steps.append(step)
        self._persist_step(task_id, step)
        return step

    def complete_step(self, task_id: str, step_id: int, result: str, evidence: str = ""):
        task = self._tasks.get(task_id)
        if not task or step_id > len(task.steps):
            return
        step = task.steps[step_id - 1]
        step.status = "completed"
        step.result = result
        step.evidence = evidence
        self._persist_step(task_id, step)

    def fail_step(self, task_id: str, step_id: int, error: str):
        task = self._tasks.get(task_id)
        if not task or step_id > len(task.steps):
            return
        step = task.steps[step_id - 1]
        step.status = "failed"
        step.result = error
        self._persist_step(task_id, step)

    def create_checkpoint(self, task_id: str, name: str, state_data: Dict[str, Any]):
        task = self._tasks.get(task_id)
        if task:
            import json
            ts = time.time()
            task.checkpoints.append({
                "name": name,
                "timestamp": ts,
                "data": state_data
            })
            try:
                with self._connection() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO task_checkpoints (task_id, name, timestamp, data)
                        VALUES (?, ?, ?, ?)
                    """, (task_id, name, ts, json.dumps(state_data)))
                    conn.commit()
            except Exception:
                pass
