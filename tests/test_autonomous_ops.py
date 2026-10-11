"""Tests for PRUBETH IDE Autonomous Operations & Self-Diagnostics (core/autonomous_ops.py)
"""

import tempfile
from pathlib import Path
import pytest
from core.autonomous_ops import (
    AutonomyMode,
    OperationRiskLevel,
    TicketStatus,
    DiagnosticObservation,
    DiagnosticIssue,
    HealingStep,
    HealingPlan,
    ApprovalTicket,
    AutonomousSupervisor,
)


def test_autonomous_supervisor_observe_and_diagnose():
    with tempfile.TemporaryDirectory() as temp_scratch:
        supervisor = AutonomousSupervisor(
            autonomy_mode=AutonomyMode.FULL_AUTONOMY_SAFE,
            scratch_dir=temp_scratch,
        )

        # 1. Healthy observation
        observations = supervisor.observe()
        assert len(observations) >= 1
        scratch_obs = next(o for o in observations if o.metric_name == "scratch_space_mb")
        assert scratch_obs.healthy is True

        issues = supervisor.diagnose(observations)
        assert len(issues) == 0

        # 2. Simulate scratch overflow
        large_file = Path(temp_scratch) / "heavy_scratch_cache.bin"
        large_file.write_bytes(b"\x00" * (1024 * 1024))  # 1MB
        # Force artificial threshold violation
        simulated_obs = [
            DiagnosticObservation(
                category="STORAGE",
                metric_name="scratch_space_mb",
                current_value=250.0,
                threshold_value=200.0,
                healthy=False,
                details="Scratch overflow",
            )
        ]
        sim_issues = supervisor.diagnose(simulated_obs)
        assert len(sim_issues) == 1
        assert "Scratch Storage" in sim_issues[0].title


def test_autonomous_healing_plan_and_policy_check():
    supervisor = AutonomousSupervisor(autonomy_mode=AutonomyMode.FULL_AUTONOMY_SAFE)

    issue = DiagnosticIssue(
        issue_id="ISSUE-01",
        severity="WARNING",
        title="Scratch Storage Accumulation",
        root_cause="Over threshold",
        suggested_action="Purge",
    )

    plan = supervisor.plan(issue)
    assert plan.risk_level == OperationRiskLevel.SAFE_EXECUTION

    # Under FULL_AUTONOMY_SAFE, SAFE_EXECUTION is approved automatically
    can_exec, ticket = supervisor.check_policy_and_approve(plan)
    assert can_exec is True
    assert ticket is None

    # For MUTATING plan, ticket is required
    mutating_plan = HealingPlan(
        plan_id="PLAN-MUT-01",
        issue_id="ISSUE-02",
        title="Rebuild Large Database Index",
        steps=[],
        risk_level=OperationRiskLevel.MUTATING,
    )
    can_exec, ticket = supervisor.check_policy_and_approve(mutating_plan)
    assert can_exec is False
    assert ticket is not None
    assert ticket.status == TicketStatus.PENDING

    # Decide ticket
    assert supervisor.decide_ticket(ticket.ticket_id, approved=True)
    assert ticket.status == TicketStatus.APPROVED


def test_autonomous_execution_and_verification():
    with tempfile.TemporaryDirectory() as temp_scratch:
        scratch_file = Path(temp_scratch) / "stale_temp.dat"
        scratch_file.write_text("temporary data")

        supervisor = AutonomousSupervisor(
            autonomy_mode=AutonomyMode.FULL_AUTONOMY_SAFE,
            scratch_dir=temp_scratch,
        )

        assert scratch_file.exists()

        def purge_fn():
            if scratch_file.exists():
                scratch_file.unlink()
            return True

        step = HealingStep(
            step_id="step-clean",
            action_name="Purge Stale File",
            execute_fn=purge_fn,
        )

        plan = HealingPlan(
            plan_id="PLAN-EXEC-01",
            issue_id="ISSUE-03",
            title="Clean Stale File",
            steps=[step],
            risk_level=OperationRiskLevel.SAFE_EXECUTION,
        )

        def verify_probe():
            return not scratch_file.exists()

        record = supervisor.execute_and_verify(plan, verification_probe=verify_probe)

        assert record.success is True
        assert record.verification_passed is True
        assert record.steps_executed == 1
        assert not scratch_file.exists()

        history = supervisor.get_audit_history()
        assert len(history) == 1
        assert history[0].plan_id == "PLAN-EXEC-01"
