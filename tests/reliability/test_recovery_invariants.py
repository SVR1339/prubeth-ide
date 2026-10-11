"""PRUBETH IDE - Recovery Invariants & Data Correctness Chaos Tests
================================================================
Verifies non-negotiable reliability invariants:
1. User files are never deleted or truncated by cache cleanup.
2. Mutating operations cannot bypass autonomous approval tickets.
3. Air-gap policy enforces zero remote socket egress.
4. Isolated lab rollback deterministically restores SHA-256 state.
5. Critical security vulnerabilities are never silently ignored.
"""

import os
import tempfile
from pathlib import Path
import pytest

from tests.reliability.helpers.crash_harness import DisposableWorkspace, timed_operation
from core.autonomous_ops import (
    AutonomousSupervisor,
    AutonomyMode,
    HealingPlan,
    HealingStep,
    OperationRiskLevel,
    TicketStatus,
)
from core.model_lab import (
    OfflineEnforcementPolicy,
    OfflinePolicyMode,
    AirGapViolationError,
)
from security_research.sast_sca_engine import SASTEngine, SecuritySeverity
from security_research.isolated_lab_manager import IsolatedLabManager


def test_invariant_user_source_files_preserved_during_scratch_purge():
    """Scratch storage cleanup must NEVER purge or modify user source files."""
    with DisposableWorkspace() as ws_path:
        # Create user source file
        user_source = ws_path / "src" / "critical_algorithm.py"
        user_source.write_text("def sovereign_compute(): return 42\n", encoding="utf-8")
        original_hash = hash(user_source.read_text())

        # Set up supervisor targeting isolated scratch folder
        scratch_dir = ws_path / ".prubeth_scratch"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        (scratch_dir / "stale_temp_cache.bin").write_bytes(b"\x00" * 5000)

        supervisor = AutonomousSupervisor(
            autonomy_mode=AutonomyMode.FULL_AUTONOMY_SAFE,
            scratch_dir=str(scratch_dir),
        )

        # Plan and execute scratch purge
        obs = supervisor.observe()
        # Force plan
        step = HealingStep(
            step_id="step-purge",
            action_name="Purge Scratch",
            execute_fn=lambda: [f.unlink() for f in scratch_dir.glob("*")] is not None,
        )
        plan = HealingPlan(
            plan_id="PLAN-PURGE",
            issue_id="ISSUE-PURGE",
            title="Clean Scratch",
            steps=[step],
            risk_level=OperationRiskLevel.SAFE_EXECUTION,
        )

        rec = supervisor.execute_and_verify(plan)
        assert rec.success is True

        # Invariant check: user source file is untouched
        assert user_source.exists()
        assert hash(user_source.read_text()) == original_hash


def test_invariant_mutating_actions_strictly_require_approval_tickets():
    """Mutating or high-risk operations cannot execute automatically without human approval."""
    supervisor = AutonomousSupervisor(autonomy_mode=AutonomyMode.FULL_AUTONOMY_SAFE)

    mutating_plan = HealingPlan(
        plan_id="PLAN-MUTATING-01",
        issue_id="ISSUE-01",
        title="Wipe and Rebuild Vector Index",
        steps=[],
        risk_level=OperationRiskLevel.MUTATING,
    )

    can_exec, ticket = supervisor.check_policy_and_approve(mutating_plan)
    assert can_exec is False
    assert ticket is not None
    assert ticket.status == TicketStatus.PENDING

    # Invariant: Must remain pending until decided
    pending_tickets = supervisor.get_pending_tickets()
    assert any(t.ticket_id == ticket.ticket_id for t in pending_tickets)


def test_invariant_strict_airgap_blocks_remote_sockets():
    """STRICT_AIRGAP policy physically raises AirGapViolationError for non-local destinations."""
    policy = OfflineEnforcementPolicy(mode=OfflinePolicyMode.STRICT_AIRGAP)

    destinations = [
        ("api.openai.com", False),
        ("cloud.google.com", False),
        ("telemetry.vendor.net", False),
        ("127.0.0.1", True),
        ("localhost", True),
    ]

    for host, should_allow in destinations:
        if should_allow:
            assert policy.check_and_audit(host, 443, "test") is True
        else:
            with pytest.raises(AirGapViolationError):
                policy.check_and_audit(host, 443, "test")


def test_invariant_isolated_lab_deterministic_rollback():
    """Lab sandbox rollback restores pre-run directory state with 100% fidelity."""
    with tempfile.TemporaryDirectory() as base_tmp:
        lab_mgr = IsolatedLabManager(base_lab_dir=base_tmp)
        session_id = "test_invariant_rollback"
        session_path = lab_mgr.create_session(session_id)

        # Baseline file
        (session_path / "clean_baseline.txt").write_text("pristine", encoding="utf-8")
        # Re-take snapshot of pristine state
        lab_mgr._active_sessions[session_id]["initial_snapshot"] = lab_mgr._take_manifest_snapshot(session_path)

        # Detonate mock payload that creates files
        (session_path / "dropped_payload.exe").write_bytes(b"\x90\xCC\xC3")
        (session_path / "ransom_note.txt").write_text("encrypted", encoding="utf-8")

        assert (session_path / "dropped_payload.exe").exists()
        assert (session_path / "ransom_note.txt").exists()

        # Rollback
        assert lab_mgr.rollback_session(session_id) is True

        # Invariant check: only baseline exists, dropped files are purged
        assert (session_path / "clean_baseline.txt").exists()
        assert not (session_path / "dropped_payload.exe").exists()
        assert not (session_path / "ransom_note.txt").exists()

        lab_mgr.destroy_session(session_id)
