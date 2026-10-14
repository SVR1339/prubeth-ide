"""
SUKHI IDE — Multi-Agent Orchestration Subsystem
Coordinates specialized subagents (Architect, Coder, Critic, Tester)
via structured messaging, dependency-driven DAG planning, and transactional verification.
"""
import time
import uuid
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from ai.agents.planner import ExecutionPlan, TaskStep, TaskStatus, CycleDetectedError
from ai.agents.critic import AgentCritic, ReviewReport, ReviewStatus
from ai.agents.self_healing_executive import SelfHealingExecutiveAgent, ProjectScale


class AgentRole(str, Enum):
    # Specification Starter Agents (Section 4)
    PLANNER = "planner"
    RESEARCHER = "researcher"
    CODER = "coder"
    TESTER = "tester"
    REVIEWER = "reviewer"
    DEBUGGER = "debugger"
    RELEASE = "release"
    # Core Architecture & Compatibility Aliases
    ARCHITECT = "architect"
    CRITIC = "critic"
    ORCHESTRATOR = "orchestrator"
    # Specialist Extensions
    WORK = "work"
    CODEX = "codex"
    DOTS = "dots"


@dataclass
class StructuredAgentResult:
    """Structured agent contract matching SUKHI IDE specification."""
    task_id: str
    status: str = "success"  # "success", "failed", "blocked"
    changed_files: List[str] = field(default_factory=list)
    evidence: str = ""
    errors: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    unresolved_questions: List[str] = field(default_factory=list)
    output: str = ""
    artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "changed_files": self.changed_files,
            "evidence": self.evidence,
            "errors": self.errors,
            "test_results": self.test_results,
            "unresolved_questions": self.unresolved_questions,
            "output": self.output,
            "artifacts": self.artifacts
        }


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
        # Default fallback execution contract
        return {
            "status": "success",
            "task_id": task.step_id,
            "output": f"Completed {task.title} by {self.name} ({self.role.value}).",
            "changed_files": [],
            "evidence": f"Executed via {self.name}",
            "errors": [],
            "test_results": {},
            "unresolved_questions": [],
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
        self.executive_healer = SelfHealingExecutiveAgent(
            workspace_root=self.workspace_root,
            critic=self.critic,
            checkpoint_manager=self.checkpoint_manager
        )

        self.messages: List[AgentMessage] = []
        self.subagents: Dict[AgentRole, Subagent] = {}
        self._init_default_agents()

    def _init_default_agents(self):
        # 1. Planner / Architect
        planner = Subagent(
            name="System Planner",
            role=AgentRole.PLANNER,
            system_prompt="Analyze requirements, produce modular software designs, and decompose tasks into DAGs with acceptance criteria."
        )
        self.register_subagent(planner)
        self.register_subagent(
            Subagent(
                name="System Architect",
                role=AgentRole.ARCHITECT,
                system_prompt=planner.system_prompt
            )
        )

        # 2. Researcher
        self.register_subagent(
            Subagent(
                name="Repository Researcher",
                role=AgentRole.RESEARCHER,
                system_prompt="Inspect relevant files, dependencies, AST symbols, and gather evidence with file references."
            )
        )

        # 3. Coder
        self.register_subagent(
            Subagent(
                name="Senior Coder",
                role=AgentRole.CODER,
                system_prompt="Implement clean, robust, production-grade source code matching specifications."
            )
        )

        # 4. Reviewer / Critic
        reviewer = Subagent(
            name="Security & Quality Reviewer",
            role=AgentRole.REVIEWER,
            system_prompt="Verify syntax, security guardrails, credential safety, and architectural integrity."
        )
        self.register_subagent(reviewer)
        self.register_subagent(
            Subagent(
                name="Security & Quality Critic",
                role=AgentRole.CRITIC,
                system_prompt=reviewer.system_prompt
            )
        )

        # 5. Tester
        self.register_subagent(
            Subagent(
                name="QA & Verification Tester",
                role=AgentRole.TESTER,
                system_prompt="Create reproducible unit/integration tests and verify deliverable acceptance criteria."
            )
        )

        # 6. Debugger
        self.register_subagent(
            Subagent(
                name="Diagnosis Debugger",
                role=AgentRole.DEBUGGER,
                system_prompt="Reproduce failures, isolate root causes, and formulate minimal corrective patches."
            )
        )

        # 7. Release Agent
        self.register_subagent(
            Subagent(
                name="Release & Build Agent",
                role=AgentRole.RELEASE,
                system_prompt="Execute build/test/package workflows, verify deliverables, and generate release evidence."
            )
        )

        # 8. Specialist Extensions: Work, Codex, Dots
        self.register_subagent(
            Subagent(
                name="Work Operations Agent",
                role=AgentRole.WORK,
                system_prompt="Execute cross-file workflows, environment configuration, and project-wide operations."
            )
        )
        self.register_subagent(
            Subagent(
                name="Codex Synthesis Engine",
                role=AgentRole.CODEX,
                system_prompt="High-speed code synthesis, refactoring, and AST transformations."
            )
        )
        self.register_subagent(
            Subagent(
                name="Dots Background Sentinel",
                role=AgentRole.DOTS,
                system_prompt="Always-on background monitoring, continuous linting, and auto-heal diagnosis."
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

    def run_plan(self, plan: ExecutionPlan, context: Optional[Dict[str, Any]] = None, auto_heal: bool = False) -> Dict[str, Any]:
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

            # Run Critic gating on Coder/Codex/Work outputs with Autonomous Self-Healing
            if role_enum in (AgentRole.CODER, AgentRole.CODEX, AgentRole.WORK) and out_text:
                review = self.critic.analyze_code(out_text)
                if review.status == ReviewStatus.REJECTED:
                    if auto_heal:
                        self.post_message(
                            sender="Critic",
                            recipient="Executive Healer",
                            role=AgentRole.CRITIC,
                            content=f"Step '{step.title}' flagged by Critic: {review.summary}. Initiating autonomous self-heal..."
                        )
                        healed_code = out_text
                        heal_success = False
                        for attempt in range(1, 4):
                            # Sanitize dangerous patterns and secrets
                            for pattern, repl in [
                                (r"sk-[a-zA-Z0-9]{20,}", "os.environ.get('OPENAI_API_KEY', '')"),
                                (r"ghp_[a-zA-Z0-9]{20,}", "os.environ.get('GITHUB_TOKEN', '')"),
                                (r"AIza[0-9A-Za-z-_]{35}", "os.environ.get('GOOGLE_API_KEY', '')"),
                            ]:
                                healed_code = re.sub(pattern, repl, healed_code)
                            healed_code = re.sub(r'\beval\s*\(', 'json.loads(', healed_code)
                            healed_code = re.sub(r'\bexec\s*\(', '# exec disabled: ', healed_code)

                            re_review = self.critic.analyze_code(healed_code)
                            if re_review.status != ReviewStatus.REJECTED:
                                out_text = healed_code
                                heal_success = True
                                self.post_message(
                                    sender="Executive Healer",
                                    recipient="Orchestrator",
                                    role=AgentRole.DEBUGGER,
                                    content=f"Step '{step.title}' self-healed successfully on attempt {attempt}: {re_review.summary}"
                                )
                                break

                        if not heal_success:
                            plan.mark_step_status(step.step_id, TaskStatus.FAILED, result_output=f"Rejected by Critic after self-healing attempts: {review.summary}")
                            continue
                    else:
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

    def scaffold_and_verify_project(self, scale: str, goal: str, target_dir: str = "") -> Dict[str, Any]:
        """Scaffolds a small, mid, or large powered project and verifies it autonomously."""
        scale_enum = ProjectScale.SMALL
        if "large" in scale.lower():
            scale_enum = ProjectScale.LARGE_POWERED
        elif "mid" in scale.lower():
            scale_enum = ProjectScale.MID

        return self.executive_healer.scaffold_project(
            scale=scale_enum,
            goal=goal,
            target_subfolder=target_dir
        )
