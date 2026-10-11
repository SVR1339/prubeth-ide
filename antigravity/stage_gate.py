"""
PRUBETH IDE — Antigravity Stage-Gate Engine (PRINCE2 & ReAct Framework)
Synthesizes:
1. ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2022)
   - Thought: Structured reasoning step
   - Action: Tool/API/Shell invocation
   - Observation: Real-world environment feedback
2. PRINCE2 / Stage-Gate Process:
   - Initiation: implementation_plan.md & task checklist
   - Stage-Gate Review: Human-in-the-loop approval or mid-flight inline commenting
   - Execution: Autonomous multi-file modifications in sandboxed Git worktree
   - Acceptance: Evidence verification with test suite and browser validation
"""
import time
import uuid
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable


class StageStatus(str, Enum):
    INITIATION = "INITIATION"                     # Generating plan & checklist
    STAGE_GATE_REVIEW = "STAGE_GATE_REVIEW"       # Awaiting human review / inline feedback
    EXECUTION = "EXECUTION"                       # Subagent modifying code in sandbox
    ACCEPTANCE = "ACCEPTANCE"                     # Automated verification & test evidence
    COMPLETED = "COMPLETED"                       # Approved & merged
    REJECTED = "REJECTED"                         # Failed or user-rejected
    PAUSED = "PAUSED"                             # Temporarily halted by human


@dataclass
class ReActTraceStep:
    """A single ReAct reasoning and acting step."""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    step_number: int = 1
    thought: str = ""
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StageGateEvent:
    """Audit log entry for stage-gate transitions."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_stage: StageStatus = StageStatus.INITIATION
    to_stage: StageStatus = StageStatus.INITIATION
    actor: str = "agent"  # "agent", "human", "system"
    reason: str = ""
    timestamp: float = field(default_factory=time.time)


class StageGateEngine:
    """
    State machine enforcing the PRINCE2 Plan -> Review -> Execute -> Verify lifecycle
    interleaved with ReAct reasoning traces.
    """

    VALID_TRANSITIONS = {
        StageStatus.INITIATION: {StageStatus.STAGE_GATE_REVIEW, StageStatus.REJECTED},
        StageStatus.STAGE_GATE_REVIEW: {StageStatus.EXECUTION, StageStatus.INITIATION, StageStatus.REJECTED, StageStatus.PAUSED},
        StageStatus.EXECUTION: {StageStatus.ACCEPTANCE, StageStatus.STAGE_GATE_REVIEW, StageStatus.REJECTED, StageStatus.PAUSED},
        StageStatus.ACCEPTANCE: {StageStatus.COMPLETED, StageStatus.EXECUTION, StageStatus.STAGE_GATE_REVIEW, StageStatus.REJECTED},
        StageStatus.PAUSED: {StageStatus.STAGE_GATE_REVIEW, StageStatus.EXECUTION, StageStatus.REJECTED},
        StageStatus.COMPLETED: set(),
        StageStatus.REJECTED: {StageStatus.INITIATION},  # Can be re-initiated
    }

    def __init__(self, task_id: str, auto_approve_minor: bool = False):
        self.task_id = task_id
        self.current_stage: StageStatus = StageStatus.INITIATION
        self.auto_approve_minor = auto_approve_minor
        self.react_traces: List[ReActTraceStep] = []
        self.history: List[StageGateEvent] = []
        self.mid_flight_directives: List[str] = []
        self.approval_metadata: Dict[str, Any] = {}

    def transition_to(self, target_stage: StageStatus, actor: str = "agent", reason: str = "") -> bool:
        """Enforces formal stage boundaries per PRINCE2."""
        if target_stage not in self.VALID_TRANSITIONS.get(self.current_stage, set()):
            raise ValueError(
                f"Invalid stage transition: cannot move from {self.current_stage.value} to {target_stage.value}"
            )

        event = StageGateEvent(
            from_stage=self.current_stage,
            to_stage=target_stage,
            actor=actor,
            reason=reason
        )
        self.current_stage = target_stage
        self.history.append(event)
        return True

    def add_react_step(self, thought: str, action: Optional[str] = None,
                       action_input: Optional[Dict[str, Any]] = None,
                       observation: Optional[str] = None,
                       duration_ms: float = 0.0) -> ReActTraceStep:
        """Appends a structured ReAct thought-action-observation trace."""
        step = ReActTraceStep(
            step_number=len(self.react_traces) + 1,
            thought=thought,
            action=action,
            action_input=action_input or {},
            observation=observation,
            duration_ms=duration_ms
        )
        self.react_traces.append(step)
        return step

    def record_observation(self, observation: str) -> Optional[ReActTraceStep]:
        """Attaches an observation to the latest ReAct step."""
        if not self.react_traces:
            return None
        latest = self.react_traces[-1]
        latest.observation = observation
        return latest

    def inject_steering_directive(self, directive: str, author: str = "human"):
        """
        Injects a mid-flight human comment to steer execution without restarting
        the subagent process.
        """
        formatted = f"[{author.upper()} STEERING DIRECTIVE] {directive}"
        self.mid_flight_directives.append(formatted)

    def consume_steering_directives(self) -> List[str]:
        """Pulls and clears pending steering directives for the next ReAct prompt."""
        pending = list(self.mid_flight_directives)
        self.mid_flight_directives.clear()
        return pending

    def approve_stage_gate(self, reviewer: str = "developer", notes: str = "") -> bool:
        """Approves the current Stage-Gate review to unlock autonomous execution."""
        if self.current_stage != StageStatus.STAGE_GATE_REVIEW:
            raise RuntimeError(f"Cannot approve stage gate when in {self.current_stage.value} stage")

        self.approval_metadata = {
            "approved_by": reviewer,
            "approved_at": time.time(),
            "notes": notes
        }
        return self.transition_to(StageStatus.EXECUTION, actor="human", reason=f"Approved by {reviewer}: {notes}")

    def request_revision(self, reviewer: str = "developer", feedback: str = "") -> bool:
        """Rejects or requests changes, sending the subagent back to plan refinement."""
        self.inject_steering_directive(feedback, author=reviewer)
        return self.transition_to(StageStatus.INITIATION, actor="human", reason=f"Revision requested: {feedback}")

    def complete_acceptance(self, test_evidence: Dict[str, Any]) -> bool:
        """Validates verification evidence and transitions to COMPLETED."""
        if self.current_stage != StageStatus.ACCEPTANCE:
            raise RuntimeError(f"Cannot complete acceptance from {self.current_stage.value} stage")

        passed = test_evidence.get("passed", False)
        if not passed:
            self.transition_to(StageStatus.EXECUTION, actor="system", reason="Verification failed; retreating to execution")
            return False

        return self.transition_to(StageStatus.COMPLETED, actor="system", reason="Verification passed with clean evidence")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "current_stage": self.current_stage.value,
            "trace_count": len(self.react_traces),
            "traces": [t.to_dict() for t in self.react_traces],
            "history": [asdict(h) for h in self.history],
            "pending_directives": self.mid_flight_directives,
            "approval_metadata": self.approval_metadata,
        }
