"""
Unit & Integration Tests for PRINCE2 7 Reliability Assurance Engine
===================================================================
Verifies the 9 test profiles, quality stage-gate calculations,
emergency stop controls, and requirements traceability.
"""
import pytest

from core.reliability_engine import (
    ReliabilityEngine, ReliabilityProfile, StageGateDecision,
    ScenarioStatus, Prince2Report
)


def test_engine_smoke_profile_execution():
    """Verify Smoke profile executes and yields approved stage-gate decision."""
    engine = ReliabilityEngine()
    report = engine.run_profile(ReliabilityProfile.SMOKE)

    assert report.profile == ReliabilityProfile.SMOKE
    assert report.total_scenarios >= 3
    assert report.passed_count == report.total_scenarios
    assert report.failed_count == 0
    assert report.stage_gate_decision == StageGateDecision.APPROVED
    assert len(report.requirements_traceability) == 10


def test_engine_security_profile_execution():
    """Verify Security profile runs directory traversal, reserved devices, and quota checks."""
    engine = ReliabilityEngine()
    report = engine.run_profile(ReliabilityProfile.SECURITY)

    assert report.profile == ReliabilityProfile.SECURITY
    assert report.passed_count == 3
    assert report.failed_count == 0
    assert report.stage_gate_decision == StageGateDecision.APPROVED


def test_engine_recovery_profile_execution():
    """Verify Recovery profile tests atomic .bak, WAL checkpoints, and settings reset."""
    engine = ReliabilityEngine()
    report = engine.run_profile(ReliabilityProfile.RECOVERY)

    assert report.profile == ReliabilityProfile.RECOVERY
    assert report.passed_count == 3
    assert report.failed_count == 0
    assert report.stage_gate_decision == StageGateDecision.APPROVED


def test_engine_large_project_profile_execution():
    """Verify Large Project profile tests monorepos, giant buffers, and 15-tier trees."""
    engine = ReliabilityEngine()
    report = engine.run_profile(ReliabilityProfile.LARGE_PROJECT)

    assert report.profile == ReliabilityProfile.LARGE_PROJECT
    assert report.passed_count == 3
    assert report.failed_count == 0
    assert report.stage_gate_decision == StageGateDecision.APPROVED


def test_engine_release_candidate_profile_execution():
    """Verify Release Candidate profile runs all quality gates."""
    engine = ReliabilityEngine()
    report = engine.run_profile(ReliabilityProfile.RELEASE_CANDIDATE)

    assert report.profile == ReliabilityProfile.RELEASE_CANDIDATE
    assert report.total_scenarios >= 10
    assert report.failed_count == 0
    assert report.stage_gate_decision == StageGateDecision.APPROVED


def test_engine_emergency_stop_control():
    """Verify emergency stop cleanly halts execution of remaining scenarios."""
    engine = ReliabilityEngine()
    engine.request_stop()
    report = engine.run_profile(ReliabilityProfile.RELEASE_CANDIDATE)

    # When immediately stopped, total executed scenarios should be 0 or 1
    assert report.total_scenarios <= 1
