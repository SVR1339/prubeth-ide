"""
SUKHI IDE — Multi-Agent Task Decomposition & DAG Execution Planner
Provides dependency-ordered task graph management, topological sorting,
cycle detection, and lifecycle step execution state tracking.
"""
import uuid
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class TaskStep:
    step_id: str
    title: str
    description: str
    assigned_role: str = "coder"  # 'architect', 'coder', 'critic', 'tester'
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result_output: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "description": self.description,
            "assigned_role": self.assigned_role,
            "dependencies": list(self.dependencies),
            "status": self.status.value,
            "result_output": self.result_output,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "artifacts": list(self.artifacts)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskStep":
        return cls(
            step_id=data["step_id"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            assigned_role=data.get("assigned_role", "coder"),
            dependencies=data.get("dependencies", []),
            status=TaskStatus(data.get("status", TaskStatus.PENDING.value)),
            result_output=data.get("result_output"),
            created_at=data.get("created_at", time.time()),
            completed_at=data.get("completed_at"),
            artifacts=data.get("artifacts", [])
        )


class CycleDetectedError(ValueError):
    """Raised when an execution plan contains cyclical step dependencies."""
    pass


class ExecutionPlan:
    """Manages a directed acyclic graph (DAG) of collaborative subagent task steps."""

    def __init__(self, goal: str, plan_id: Optional[str] = None):
        self.plan_id = plan_id or f"plan-{uuid.uuid4().hex[:8]}"
        self.goal = goal
        self.created_at = time.time()
        self.steps: Dict[str, TaskStep] = {}

    def add_step(
        self,
        title: str,
        description: str,
        assigned_role: str = "coder",
        dependencies: Optional[List[str]] = None,
        step_id: Optional[str] = None
    ) -> TaskStep:
        s_id = step_id or f"step-{len(self.steps) + 1:02d}"
        deps = dependencies or []

        # Validate dependency references exist or will be valid
        for d in deps:
            if d == s_id:
                raise CycleDetectedError(f"Step '{s_id}' cannot depend on itself.")

        step = TaskStep(
            step_id=s_id,
            title=title,
            description=description,
            assigned_role=assigned_role,
            dependencies=deps
        )
        self.steps[s_id] = step
        # Validate that adding this step didn't introduce a cycle
        self.topological_order()
        return step

    def get_step(self, step_id: str) -> Optional[TaskStep]:
        return self.steps.get(step_id)

    def mark_step_status(
        self,
        step_id: str,
        status: TaskStatus,
        result_output: Optional[str] = None,
        artifacts: Optional[List[str]] = None
    ) -> bool:
        step = self.steps.get(step_id)
        if not step:
            return False

        step.status = status
        if result_output is not None:
            step.result_output = result_output
        if artifacts:
            step.artifacts.extend(artifacts)

        if status == TaskStatus.COMPLETED:
            step.completed_at = time.time()
        return True

    def get_ready_steps(self) -> List[TaskStep]:
        """Returns steps that are PENDING and whose dependencies are all COMPLETED."""
        ready: List[TaskStep] = []
        for step in self.steps.values():
            if step.status != TaskStatus.PENDING:
                continue

            all_deps_done = True
            for dep_id in step.dependencies:
                dep_step = self.steps.get(dep_id)
                if not dep_step or dep_step.status != TaskStatus.COMPLETED:
                    all_deps_done = False
                    break

            if all_deps_done:
                ready.append(step)
        return ready

    def topological_order(self) -> List[TaskStep]:
        """
        Calculates topological sort of steps.
        Raises CycleDetectedError if a dependency cycle is detected.
        """
        in_degree: Dict[str, int] = {s_id: 0 for s_id in self.steps}
        adj: Dict[str, List[str]] = {s_id: [] for s_id in self.steps}

        for s_id, step in self.steps.items():
            for dep in step.dependencies:
                if dep in self.steps:
                    adj[dep].append(s_id)
                    in_degree[s_id] += 1

        queue = [s_id for s_id, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            curr = queue.pop(0)
            order.append(self.steps[curr])

            for nxt in adj[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        if len(order) < len(self.steps):
            raise CycleDetectedError("Dependency cycle detected in execution plan.")

        return order

    def is_complete(self) -> bool:
        if not self.steps:
            return False
        return all(s.status == TaskStatus.COMPLETED for s in self.steps.values())

    def has_failures(self) -> bool:
        return any(s.status == TaskStatus.FAILED for s in self.steps.values())

    def get_progress_percentage(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps.values() if s.status == TaskStatus.COMPLETED)
        return (completed / len(self.steps)) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "created_at": self.created_at,
            "progress": self.get_progress_percentage(),
            "is_complete": self.is_complete(),
            "steps": [s.to_dict() for s in self.steps.values()]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionPlan":
        plan = cls(goal=data.get("goal", ""), plan_id=data.get("plan_id"))
        plan.created_at = data.get("created_at", time.time())
        for s_data in data.get("steps", []):
            step = TaskStep.from_dict(s_data)
            plan.steps[step.step_id] = step
        return plan
