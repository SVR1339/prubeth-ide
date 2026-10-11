"""
Comprehensive Unit & Integration Test Suite for PRUBETH Horizon Core Subsystems.
Validates:
1. PRINCE2 Stage-Gate governance & ReAct reasoning/action trace loops
2. Artifact Engine & Google-Docs-style inline commenting loops
3. Multi-Tenant Sandbox & Git worktree isolation
4. Reusable Skill Protocol (SKILL.md) & low-token progressive disclosure
5. Browser-aware autonomous verification runner
6. Mission Control orchestrator & parent-child subagent scheduling
"""
import os
import json
import pytest
from pathlib import Path

from horizon_engine.stage_gate import StageGateEngine, StageStatus
from horizon_engine.artifacts import ArtifactEngine, ArtifactType
from horizon_engine.worktree_sandbox import WorktreeSandboxManager
from horizon_engine.skills import SkillsEngine, SkillManifest
from horizon_engine.browser_verifier import BrowserVerificationRunner
from horizon_engine.mission_control import MissionControlOrchestrator, SubagentMission


def test_stage_gate_engine_transitions_and_governance():
    """Tests PRINCE2 stage boundaries and ReAct trace execution."""
    gate = StageGateEngine(task_id="task-test-01")
    assert gate.current_stage == StageStatus.INITIATION

    # ReAct trace logging
    step = gate.add_react_step(
        thought="Need to analyze repository imports and locate auth provider.",
        action="search_files",
        action_input={"query": "AuthProvider"}
    )
    assert step.step_number == 1
    assert step.action == "search_files"

    gate.record_observation("Found AuthProvider in src/auth/provider.py")
    assert gate.react_traces[0].observation == "Found AuthProvider in src/auth/provider.py"

    # Transition to review
    assert gate.transition_to(StageStatus.STAGE_GATE_REVIEW, actor="agent", reason="Plan generated")
    assert gate.current_stage == StageStatus.STAGE_GATE_REVIEW

    # Mid-flight steering
    gate.inject_steering_directive("Use JWT tokens instead of cookies", author="reviewer")
    directives = gate.consume_steering_directives()
    assert len(directives) == 1
    assert "JWT tokens" in directives[0]

    # Human-in-the-loop approval
    assert gate.approve_stage_gate(reviewer="lead_dev", notes="Approved with JWT requirement")
    assert gate.current_stage == StageStatus.EXECUTION

    # Transition to acceptance
    gate.transition_to(StageStatus.ACCEPTANCE, actor="agent", reason="Code edits complete")
    assert gate.current_stage == StageStatus.ACCEPTANCE

    # Complete acceptance with clean test evidence
    passed = gate.complete_acceptance({"passed": True, "test_count": 12})
    assert passed is True
    assert gate.current_stage == StageStatus.COMPLETED

    # Verify invalid transitions are blocked
    with pytest.raises(ValueError):
        gate.transition_to(StageStatus.INITIATION)  # COMPLETED is terminal


def test_artifact_engine_and_inline_commenting_loop(tmp_path):
    """Tests artifact creation, Google-Docs-style inline comments, and persistence."""
    engine = ArtifactEngine(workspace_root=tmp_path)

    # 1. Create Implementation Plan artifact
    plan = engine.create_plan_artifact(
        task_id="task-auth",
        title="OAuth2 Migration Plan",
        markdown_plan="# Architecture\nMigrating session auth to OAuth2.\n1. Add TokenService\n2. Update tests."
    )
    assert plan.artifact_id.startswith("plan-")
    assert plan.artifact_type == ArtifactType.IMPLEMENTATION_PLAN
    assert (tmp_path / ".horizon" / "artifacts" / "task-auth" / "implementation_plan.md").exists()

    # 2. Add inline comment (Google Docs style mid-flight feedback)
    comment = engine.add_inline_comment(
        artifact_id=plan.artifact_id,
        line_start=2,
        line_end=4,
        content="Ensure RS256 algorithm is used for signing",
        author="security_lead"
    )
    assert comment.line_start == 2
    assert comment.line_end == 4
    assert comment.resolved is False

    # Check unresolved comments query
    unresolved = engine.get_unresolved_comments(plan.artifact_id)
    assert len(unresolved) == 1

    # Resolve comment
    assert engine.resolve_comment(plan.artifact_id, comment.comment_id, note="Applied RS256")
    assert len(engine.get_unresolved_comments(plan.artifact_id)) == 0

    # 3. Create Diff Artifact
    diff = engine.create_diff_artifact(
        task_id="task-auth",
        title="OAuth2 Diff",
        unified_diff="--- a/auth.py\n+++ b/auth.py\n@@ -1 +1 @@\n-cookie\n+jwt\n"
    )
    assert diff.artifact_type == ArtifactType.INTERACTIVE_DIFF
    assert len(engine.get_task_artifacts("task-auth")) == 2


def test_worktree_sandbox_isolation(tmp_path):
    """Tests isolated subagent sandbox creation and zero-interference execution."""
    src_file = tmp_path / "main.py"
    src_file.write_text("def run():\n    return 'original'\n", encoding="utf-8")

    mgr = WorktreeSandboxManager(workspace_root=tmp_path)
    session = mgr.create_sandbox(task_id="task-isolated")

    assert session.sandbox_path.exists()
    assert (session.sandbox_path / "main.py").exists()

    # Edit file inside sandbox
    sbx_file = session.sandbox_path / "main.py"
    sbx_file.write_text("def run():\n    return 'modified-by-agent'\n", encoding="utf-8")

    # Verify developer's working directory remains untouched! (Zero interference)
    assert src_file.read_text(encoding="utf-8") == "def run():\n    return 'original'\n"

    # Generate unified diff
    diff = mgr.generate_diff("task-isolated")
    assert "modified-by-agent" in diff
    assert "original" in diff

    # Cleanup
    mgr.cleanup_sandbox("task-isolated")
    assert not session.sandbox_path.exists()


def test_skills_engine_progressive_disclosure(tmp_path):
    """Tests SKILL.md parsing, low-token signatures, and on-demand disclosure."""
    skills_dir = tmp_path / "skills" / "custom_skill"
    skills_dir.mkdir(parents=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text("""---
name: custom-db-analyzer
description: Performs deep SQL query optimization and index analysis.
triggers: sql, query, postgres, database, index
tools: sql_runner, explain_analyzer
---
# Instructions
Analyze all slow query logs and suggest composite B-tree indices.
""", encoding="utf-8")

    engine = SkillsEngine(workspace_root=tmp_path)
    assert "custom-db-analyzer" in engine.signatures

    # Low-token progressive disclosure prompt
    summary = engine.get_progressive_disclosure_prompt()
    assert "custom-db-analyzer" in summary
    assert "Performs deep SQL query optimization" in summary

    # Keyword matching
    matches = engine.match_skills("Please optimize our Postgres query performance")
    assert "custom-db-analyzer" in matches

    # On-demand full instructions disclosure
    instructions = engine.disclose_skill("custom-db-analyzer")
    assert "=== ACTIVATED SKILL: custom-db-analyzer ===" in instructions
    assert "Analyze all slow query logs" in instructions


def test_browser_verification_runner(tmp_path):
    """Tests browser verification runner and visual artifact generation."""
    runner = BrowserVerificationRunner(artifacts_dir=tmp_path / "artifacts")
    report = runner.verify_local_url(
        url="http://invalid.local.test.domain:9999",
        task_id="task-web-01"
    )
    assert report.passed is False
    assert report.screenshot_path is not None
    assert Path(report.screenshot_path).exists()


def test_mission_control_orchestrator_lifecycle(tmp_path):
    """Tests end-to-end mission lifecycle in Mission Control."""
    orch = MissionControlOrchestrator(workspace_root=tmp_path)

    # 1. Spawn subagent mission
    mission = orch.spawn_mission(
        title="Refactor Token Auth",
        objective="Replace cookies with JWT tokens and verify test pass",
        model="redsage-8b:latest",
        use_isolated_worktree=True
    )
    assert mission.task_id.startswith("mission-")
    assert mission.stage_gate.current_stage == StageStatus.STAGE_GATE_REVIEW
    assert mission.progress_pct == 25
    assert len(mission.artifacts) >= 1  # Plan artifact

    # 2. Inject mid-flight steering feedback
    assert orch.inject_mission_feedback(mission.task_id, "Use 256-bit secret key")
    assert len(mission.stage_gate.mid_flight_directives) == 1

    # 3. Approve stage gate
    assert orch.approve_mission_stage(mission.task_id, reviewer="lead", notes="LGTM")
    assert mission.stage_gate.current_stage == StageStatus.EXECUTION
    assert mission.progress_pct == 50

    # 4. Run verification
    res = orch.run_mission_verification(mission.task_id)
    assert "evidence" in res
    assert mission.stage_gate.current_stage == StageStatus.COMPLETED
    assert mission.progress_pct == 100

    # 5. Clean abort test
    m2 = orch.spawn_mission("Aborted Mission", "To be cancelled")
    assert orch.abort_mission(m2.task_id)
    assert m2.stage_gate.current_stage == StageStatus.REJECTED
