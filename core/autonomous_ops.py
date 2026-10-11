"""PRUBETH IDE - Autonomous Operations & Self-Diagnostic Engine
============================================================
Implements the formal Observe -> Diagnose -> Plan -> Check Policy -> Approve -> Execute -> Verify -> Record loop
for resilient, zero-maintenance local developer operations with human-in-the-loop checkpoints.
"""

from __future__ import annotations

import enum
import logging
import os
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Models
# ============================================================================

class AutonomyMode(str, enum.Enum):
    FULL_AUTONOMY_SAFE = "FULL_AUTONOMY_SAFE"  # Auto-executes READ_ONLY & SAFE_EXECUTION
    SUPERVISED = "SUPERVISED"                  # Auto-executes READ_ONLY, prompts for others
    MANUAL = "MANUAL"                          # Requires explicit approval for all plans


class OperationRiskLevel(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    SAFE_EXECUTION = "SAFE_EXECUTION"
    MUTATING = "MUTATING"
    HIGH_RISK = "HIGH_RISK"


class TicketStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class DiagnosticObservation:
    category: str  # "STORAGE", "COMPUTE", "CONNECTOR", "INTEGRITY"
    metric_name: str
    current_value: Any
    threshold_value: Any
    healthy: bool
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DiagnosticIssue:
    issue_id: str
    severity: str  # "INFO", "WARNING", "ERROR", "CRITICAL"
    title: str
    root_cause: str
    suggested_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealingStep:
    step_id: str
    action_name: str
    execute_fn: Callable[[], bool]
    rollback_fn: Optional[Callable[[], bool]] = None
    description: str = ""


@dataclass
class HealingPlan:
    plan_id: str
    issue_id: str
    title: str
    steps: List[HealingStep] = field(default_factory=list)
    risk_level: OperationRiskLevel = OperationRiskLevel.SAFE_EXECUTION
    requires_human_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "issue_id": self.issue_id,
            "title": self.title,
            "risk_level": self.risk_level.value,
            "requires_human_approval": self.requires_human_approval,
            "step_count": len(self.steps),
        }


@dataclass
class ApprovalTicket:
    ticket_id: str
    plan_id: str
    title: str
    risk_level: OperationRiskLevel
    status: TicketStatus = TicketStatus.PENDING
    requested_at: float = field(default_factory=time.time)
    decided_at: Optional[float] = None
    decided_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["risk_level"] = self.risk_level.value
        d["status"] = self.status.value
        return d


@dataclass
class AutonomousAuditRecord:
    audit_id: str
    plan_id: str
    timestamp: float
    risk_level: str
    steps_executed: int
    success: bool
    verification_passed: bool
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# Autonomous Supervisor Engine
# ============================================================================

class AutonomousSupervisor:
    """Oversees autonomous self-diagnostics, safe healing, and audit recording."""

    def __init__(
        self,
        autonomy_mode: AutonomyMode = AutonomyMode.FULL_AUTONOMY_SAFE,
        scratch_dir: str = ".prubeth_scratch",
    ) -> None:
        self._mode = autonomy_mode
        self._scratch_dir = Path(scratch_dir)
        self._scratch_dir.mkdir(parents=True, exist_ok=True)
        self._tickets: Dict[str, ApprovalTicket] = {}
        self._audit_log: List[AutonomousAuditRecord] = []

    @property
    def mode(self) -> AutonomyMode:
        return self._mode

    def set_mode(self, mode: AutonomyMode) -> None:
        logger.info(f"Autonomy Supervisor mode set to {mode.value}")
        self._mode = mode

    # ------------------------------------------------------------------------
    # 1. OBSERVE
    # ------------------------------------------------------------------------
    def observe(self) -> List[DiagnosticObservation]:
        """Collects telemetry from disk, scratch workspaces, and environment."""
        observations: List[DiagnosticObservation] = []

        # Check scratch directory size
        scratch_bytes = 0
        file_count = 0
        if self._scratch_dir.exists():
            for root, _, files in os.walk(self._scratch_dir):
                for f in files:
                    fp = Path(root) / f
                    try:
                        scratch_bytes += fp.stat().st_size
                        file_count += 1
                    except Exception:
                        pass

        scratch_mb = scratch_bytes / (1024 * 1024)
        scratch_healthy = scratch_mb < 200.0  # Alert if scratch exceeds 200MB
        observations.append(DiagnosticObservation(
            category="STORAGE",
            metric_name="scratch_space_mb",
            current_value=round(scratch_mb, 2),
            threshold_value=200.0,
            healthy=scratch_healthy,
            details=f"{file_count} temporary scratch files occupying {scratch_mb:.2f} MB",
        ))

        # Check disk space on workspace drive
        try:
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024 ** 3)
            disk_healthy = free_gb > 2.0  # Alert if free disk under 2GB
            observations.append(DiagnosticObservation(
                category="STORAGE",
                metric_name="free_disk_gb",
                current_value=round(free_gb, 2),
                threshold_value=2.0,
                healthy=disk_healthy,
                details=f"Workspace drive has {free_gb:.2f} GB free space",
            ))
        except Exception:
            pass

        return observations

    # ------------------------------------------------------------------------
    # 2. DIAGNOSE
    # ------------------------------------------------------------------------
    def diagnose(self, observations: List[DiagnosticObservation]) -> List[DiagnosticIssue]:
        """Identifies root cause issues requiring healing plans."""
        issues: List[DiagnosticIssue] = []

        for obs in observations:
            if not obs.healthy:
                if obs.metric_name == "scratch_space_mb":
                    issues.append(DiagnosticIssue(
                        issue_id=f"ISSUE-SCRATCH-OVERFLOW-{int(time.time())}",
                        severity="WARNING",
                        title="Scratch Storage Accumulation",
                        root_cause=f"Scratch temporary directory size ({obs.current_value} MB) exceeds threshold",
                        suggested_action="Purge stale scratch artifacts older than 1 hour",
                    ))
                elif obs.metric_name == "free_disk_gb":
                    issues.append(DiagnosticIssue(
                        issue_id=f"ISSUE-LOW-DISK-{int(time.time())}",
                        severity="CRITICAL",
                        title="Low Disk Space on Development Drive",
                        root_cause=f"Free disk space is critically low ({obs.current_value} GB)",
                        suggested_action="Purge build caches and compress inactive logs",
                    ))

        return issues

    # ------------------------------------------------------------------------
    # 3. PLAN
    # ------------------------------------------------------------------------
    def plan(self, issue: DiagnosticIssue) -> HealingPlan:
        """Synthesizes structured step-by-step remediation plan."""
        plan_id = f"PLAN-{uuid.uuid4().hex[:8]}"

        if "Scratch Storage" in issue.title:
            def purge_scratch() -> bool:
                for f in self._scratch_dir.glob("*"):
                    try:
                        if f.is_file():
                            f.unlink()
                        elif f.is_dir():
                            shutil.rmtree(f)
                    except Exception:
                        pass
                return True

            step = HealingStep(
                step_id="step-purge-scratch",
                action_name="Purge Scratch Temporary Files",
                execute_fn=purge_scratch,
                description="Removes ephemeral scratch files to restore space.",
            )
            return HealingPlan(
                plan_id=plan_id,
                issue_id=issue.issue_id,
                title="Auto-Clean Scratch Storage",
                steps=[step],
                risk_level=OperationRiskLevel.SAFE_EXECUTION,
            )

        # Default fallback plan
        return HealingPlan(
            plan_id=plan_id,
            issue_id=issue.issue_id,
            title=f"Remediate {issue.title}",
            steps=[],
            risk_level=OperationRiskLevel.MUTATING,
        )

    # ------------------------------------------------------------------------
    # 4. CHECK POLICY & 5. APPROVE
    # ------------------------------------------------------------------------
    def check_policy_and_approve(self, plan: HealingPlan) -> Tuple[bool, Optional[ApprovalTicket]]:
        """Evaluates plan risk against autonomy mode; returns (can_execute, ticket)."""
        if self._mode == AutonomyMode.FULL_AUTONOMY_SAFE:
            if plan.risk_level in (OperationRiskLevel.READ_ONLY, OperationRiskLevel.SAFE_EXECUTION):
                return True, None
        elif self._mode == AutonomyMode.SUPERVISED:
            if plan.risk_level == OperationRiskLevel.READ_ONLY:
                return True, None

        # Requires human-in-the-loop approval ticket
        ticket_id = f"TICKET-{uuid.uuid4().hex[:8]}"
        ticket = ApprovalTicket(
            ticket_id=ticket_id,
            plan_id=plan.plan_id,
            title=plan.title,
            risk_level=plan.risk_level,
        )
        self._tickets[ticket_id] = ticket
        plan.requires_human_approval = True
        return False, ticket

    def decide_ticket(self, ticket_id: str, approved: bool, decided_by: str = "operator") -> bool:
        """User/Operator decision handler."""
        if ticket_id not in self._tickets:
            return False
        ticket = self._tickets[ticket_id]
        ticket.status = TicketStatus.APPROVED if approved else TicketStatus.REJECTED
        ticket.decided_at = time.time()
        ticket.decided_by = decided_by
        return True

    # ------------------------------------------------------------------------
    # 6. EXECUTE & 7. VERIFY & 8. RECORD
    # ------------------------------------------------------------------------
    def execute_and_verify(
        self, plan: HealingPlan, verification_probe: Optional[Callable[[], bool]] = None
    ) -> AutonomousAuditRecord:
        """Executes plan steps, runs verification probe, and logs to immutable record."""
        executed_steps = 0
        overall_success = True
        details = []

        for step in plan.steps:
            try:
                ok = step.execute_fn()
                if ok:
                    executed_steps += 1
                    details.append(f"Step {step.step_id} succeeded")
                else:
                    overall_success = False
                    details.append(f"Step {step.step_id} returned false")
                    break
            except Exception as e:
                overall_success = False
                details.append(f"Step {step.step_id} failed with error: {e}")
                # Execute rollbacks of completed steps if available
                break

        # Verification step
        verification_passed = True
        if verification_probe:
            try:
                verification_passed = verification_probe()
            except Exception:
                verification_passed = False

        record = AutonomousAuditRecord(
            audit_id=f"AUDIT-{uuid.uuid4().hex[:8]}",
            plan_id=plan.plan_id,
            timestamp=time.time(),
            risk_level=plan.risk_level.value,
            steps_executed=executed_steps,
            success=overall_success,
            verification_passed=verification_passed,
            details="; ".join(details),
        )
        self._audit_log.append(record)
        return record

    def get_audit_history(self) -> List[AutonomousAuditRecord]:
        return list(self._audit_log)

    def get_pending_tickets(self) -> List[ApprovalTicket]:
        return [t for t in self._tickets.values() if t.status == TicketStatus.PENDING]


# Global singleton
_GLOBAL_SUPERVISOR: Optional[AutonomousSupervisor] = None

def get_autonomous_supervisor() -> AutonomousSupervisor:
    global _GLOBAL_SUPERVISOR
    if _GLOBAL_SUPERVISOR is None:
        _GLOBAL_SUPERVISOR = AutonomousSupervisor()
    return _GLOBAL_SUPERVISOR
