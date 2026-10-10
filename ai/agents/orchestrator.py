"""
SUKHI IDE — Multi-Agent Orchestration Subsystem
Coordinates specialized subagents (Architect, Coder, Critic, Tester)
via structured messaging, dependency-driven DAG planning, and transactional verification.
"""
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from ai.agents.planner import ExecutionPlan, TaskStep, TaskStatus, CycleDetectedError
from ai.agents.critic import AgentCritic, ReviewReport, ReviewStatus


class AgentRole(str, Enum):
    ARCHITECT = "architect"
    CODER = "coder"
    CRITIC = "critic"
    TESTER = "tester"
    ORCHESTRATOR = "orchestrator"


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    role: AgentRole
    content: str
    msg_id: str = field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:8]}")
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "role": self.role.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class Subagent:
    """Base specialized subagent for task execution."""

    def __init__(self, name: str, role: AgentRole, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.execution_handler: Optional[Callable[[TaskStep, Dict[str, Any]], Dict[str, Any]]] = None

    def set_handler(self, handler: Callable[[TaskStep, Dict[str, Any]], Dict[str, Any]]):
        self.execution_handler = handler

    def execute(self, task: TaskStep, context: Dict[str, Any]) -> Dict[str, Any]:
        if self.execution_handler:
            return self.execution_handler(task, context)
        # Default fallback execution simulation
        return {
            "status": "success",
            "output": f"Completed {task.title} by {self.name} ({self.role.value}).",
            "artifacts": []
        }


class MultiAgentOrchestrator:
    """Coordinates specialized agent teams across the development lifecycle."""

    def __init__(
        self,
        workspace_root: str,
        checkpoint_manager: Optional[Any] = None,
        tool_gateway: Optional[Any] = None
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.checkpoint_manager = checkpoint_manager
        self.tool_gateway = tool_gateway
        self.critic = AgentCritic()

        self.messages: List[AgentMessage] = []
        self.subagents: Dict[AgentRole, Subagent] = {}
        self._init_default_agents()

    def _init_default_agents(self):
        self.register_subagent(
            Subagent(
                name="System Architect",
                role=AgentRole.ARCHITECT,
                system_prompt="Analyze requirements, produce modular software designs, and decompose tasks into DAGs."
            )
        )
        self.register_subagent(
            Subagent(
                name="Senior Coder",
                role=AgentRole.CODER,
                system_prompt="Implement clean, robust, production-grade source code matching specifications."
            )
        )
        self.register_subagent(
            Subagent(
                name="Security & Quality Critic",
                role=AgentRole.CRITIC,
                system_prompt="Verify syntax, security guardrails, credential safety, and architectural integrity."
            )
        )
        self.register_subagent(
            Subagent(
                name="QA & Verification Tester",
                role=AgentRole.TESTER,
                system_prompt="Create reproducible unit/integration tests and verify deliverable acceptance criteria."
            )
        )

    def register_subagent(self, agent: Subagent):
        self.subagents[agent.role] = agent

    def get_subagent(self, role: AgentRole) -> Optional[Subagent]:
        return self.subagents.get(role)

    def post_message(
        self,
        sender: str,
        recipient: str,
        role: AgentRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        msg = AgentMessage(
            sender=sender,
            recipient=recipient,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(msg)
        return msg

    def build_plan(self, goal: str, steps_spec: Optional[List[Dict[str, Any]]] = None) -> ExecutionPlan:
        """Decomposes a goal into an ExecutionPlan."""
        plan = ExecutionPlan(goal=goal)

        if steps_spec:
            for s in steps_spec:
                plan.add_step(
                    title=s.get("title", "Untitled Task"),
                    description=s.get("description", ""),
                    assigned_role=s.get("role", "coder"),
                    dependencies=s.get("dependencies", []),
                    step_id=s.get("step_id")
                )
        else:
            # Default standard 4-phase engineering plan
            s1 = plan.add_step(
                title=f"Architectural Design: {goal}",
                description="Analyze system requirements and establish module interfaces.",
                assigned_role=AgentRole.ARCHITECT.value,
                step_id="step-01"
            )
            s2 = plan.add_step(
                title=f"Core Implementation: {goal}",
                description="Write production-grade source code and logic.",
                assigned_role=AgentRole.CODER.value,
                dependencies=["step-01"],
                step_id="step-02"
            )
            s3 = plan.add_step(
                title=f"Security & AST Review: {goal}",
                description="Inspect code against security rules, secrets, and syntax.",
                assigned_role=AgentRole.CRITIC.value,
                dependencies=["step-02"],
                step_id="step-03"
            )
            plan.add_step(
                title=f"Automated Testing & Verification: {goal}",
                description="Execute automated test suite and confirm 100% pass rate.",
                assigned_role=AgentRole.TESTER.value,
                dependencies=["step-03"],
                step_id="step-04"
            )

        self.post_message(
            sender="Architect",
            recipient="Orchestrator",
            role=AgentRole.ARCHITECT,
            content=f"Generated execution plan with {len(plan.steps)} steps for goal: '{goal}'.",
            metadata={"plan_id": plan.plan_id}
        )
        return plan

    def run_plan(self, plan: ExecutionPlan, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes an ExecutionPlan step-by-step in topological dependency order.
        """
        ctx = context or {}
        ordered_steps = plan.topological_order()
        checkpoint_id = None

        if self.checkpoint_manager:
            checkpoint_id = self.checkpoint_manager.begin_checkpoint(f"Orchestration: {plan.goal[:40]}")

        execution_log = []

        for step in ordered_steps:
            # Verify dependencies are completed
            for dep_id in step.dependencies:
                dep_step = plan.get_step(dep_id)
                if not dep_step or dep_step.status != TaskStatus.COMPLETED:
                    plan.mark_step_status(step.step_id, TaskStatus.BLOCKED)
                    break

            if step.status == TaskStatus.BLOCKED:
                continue

            plan.mark_step_status(step.step_id, TaskStatus.IN_PROGRESS)
            role_enum = AgentRole(step.assigned_role) if step.assigned_role in [r.value for r in AgentRole] else AgentRole.CODER
            agent = self.get_subagent(role_enum)

            self.post_message(
                sender="Orchestrator",
                recipient=agent.name if agent else step.assigned_role,
                role=role_enum,
                content=f"Starting task '{step.title}'."
            )

            res = agent.execute(step, ctx) if agent else {"status": "success", "output": "Default execution"}
            out_text = res.get("output", "")
            artifacts = res.get("artifacts", [])

            # Run Critic gating on Coder outputs
            if role_enum == AgentRole.CODER and out_text:
                review = self.critic.analyze_code(out_text)
                if review.status == ReviewStatus.REJECTED:
                    plan.mark_step_status(step.step_id, TaskStatus.FAILED, result_output=f"Rejected by Critic: {review.summary}")
                    self.post_message(
                        sender="Critic",
                        recipient="Orchestrator",
                        role=AgentRole.CRITIC,
                        content=f"Step '{step.title}' rejected: {review.summary}"
                    )
                    continue

            plan.mark_step_status(step.step_id, TaskStatus.COMPLETED, result_output=out_text, artifacts=artifacts)
            execution_log.append({
                "step_id": step.step_id,
                "role": step.assigned_role,
                "title": step.title,
                "output": out_text
            })

            self.post_message(
                sender=agent.name if agent else step.assigned_role,
                recipient="Orchestrator",
                role=role_enum,
                content=f"Completed task '{step.title}'."
            )

        success = plan.is_complete()
        return {
            "success": success,
            "plan_id": plan.plan_id,
            "goal": plan.goal,
            "checkpoint_id": checkpoint_id,
            "progress": plan.get_progress_percentage(),
            "completed_steps": len(execution_log),
            "execution_log": execution_log
        }
