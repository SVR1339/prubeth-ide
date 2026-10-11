"""
PRUBETH IDE — Antigravity Agent Manager & Mission Control Orchestrator (DAG Engine)
Implements:
1. Dual-Track Agile / Commander-Crew Operating Model:
   - Decoupled interface: Editor View (Synchronous) vs Mission Control (Asynchronous)
   - Developers act as project board / system architects supervising parallel subagents.
2. Parent-Child Subagent Scheduler (DAG Engine):
   - Decomposes high-level objectives into Planner -> Coder -> Tester/Reviewer subagents.
3. Multi-Task Coordination:
   - Spawns parallel 30-60 minute background tasks with isolated worktree sandboxes,
     verifiable artifact creation, ReAct traces, and mid-flight steering feedback.
"""
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable

from antigravity.stage_gate import StageGateEngine, StageStatus, ReActTraceStep
from antigravity.artifacts import ArtifactEngine, Artifact, ArtifactType
from antigravity.worktree_sandbox import WorktreeSandboxManager, SandboxSession
from antigravity.skills import SkillsEngine
from antigravity.browser_verifier import BrowserVerificationRunner, BrowserVerificationReport


@dataclass
class SubagentMission:
    """Represents an independent asynchronous subagent mission in Mission Control."""
    task_id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:6]}")
    title: str = "Autonomous Task"
    objective: str = ""
    model: str = "redsage-8b:latest"
    workspace_root: str = ""
    use_isolated_worktree: bool = True
    stage_gate: Optional[StageGateEngine] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    progress_pct: int = 0
    assigned_role: str = "Generalist Engineer"
    active_skills: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)  # Artifact IDs
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "objective": self.objective,
            "model": self.model,
            "workspace_root": self.workspace_root,
            "use_isolated_worktree": self.use_isolated_worktree,
            "stage": self.stage_gate.current_stage.value if self.stage_gate else StageStatus.INITIATION.value,
            "progress_pct": self.progress_pct,
            "assigned_role": self.assigned_role,
            "active_skills": self.active_skills,
            "artifacts_count": len(self.artifacts),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message
        }


class MissionControlOrchestrator:
    """
    Central Asynchronous Mission Control Orchestrator.
    Manages parallel subagents, stage-gate approvals, worktree sandboxes, and artifact generation.
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()
        self.artifact_engine = ArtifactEngine(self.workspace_root)
        self.sandbox_manager = WorktreeSandboxManager(self.workspace_root)
        self.skills_engine = SkillsEngine(self.workspace_root)
        self.browser_verifier = BrowserVerificationRunner(self.artifact_engine.artifacts_dir)
        self.missions: Dict[str, SubagentMission] = {}

    def spawn_mission(self, title: str, objective: str, model: str = "redsage-8b:latest",
                      use_isolated_worktree: bool = True) -> SubagentMission:
        """
        Spawns a new independent asynchronous subagent mission.
        Initializes StageGateEngine, detects applicable skills, and creates the plan phase.
        """
        task_id = f"mission-{uuid.uuid4().hex[:6]}"
        stage_gate = StageGateEngine(task_id=task_id)

        # Detect matching skills via progressive disclosure
        matched_skills = self.skills_engine.match_skills(objective)

        mission = SubagentMission(
            task_id=task_id,
            title=title,
            objective=objective,
            model=model,
            workspace_root=str(self.workspace_root),
            use_isolated_worktree=use_isolated_worktree,
            stage_gate=stage_gate,
            progress_pct=10,
            assigned_role="Lead Systems Architect",
            active_skills=matched_skills
        )

        # Create isolated worktree sandbox if requested
        if use_isolated_worktree:
            self.sandbox_manager.create_sandbox(task_id)

        # Initial ReAct planning step
        stage_gate.add_react_step(
            thought=f"Decomposing objective '{title}'. Matched skills: {', '.join(matched_skills) or 'None'}.",
            action="generate_implementation_plan",
            action_input={"objective": objective}
        )

        # Generate initial implementation plan artifact
        plan_content = (
            f"# Implementation Plan: {title}\n\n"
            f"**Objective**: {objective}\n\n"
            f"**Target Model**: {model}\n\n"
            f"## Proposed Architecture & Execution Steps\n"
            f"1. [ ] Analyze dependencies and codebase symbol map\n"
            f"2. [ ] Stage isolated modifications in shadow worktree\n"
            f"3. [ ] Run automated regression test suite\n"
            f"4. [ ] Run browser-based visual verification\n"
            f"5. [ ] Submit unified diff for Stage-Gate review\n"
        )
        plan_art = self.artifact_engine.create_plan_artifact(
            task_id=task_id,
            title=f"Plan: {title}",
            markdown_plan=plan_content
        )
        mission.artifacts.append(plan_art.artifact_id)

        # Transition to Stage-Gate Review per PRINCE2 process
        stage_gate.transition_to(
            StageStatus.STAGE_GATE_REVIEW,
            actor="agent",
            reason="Implementation plan drafted; awaiting developer approval"
        )
        mission.progress_pct = 25
        mission.updated_at = time.time()

        self.missions[task_id] = mission
        return mission

    def approve_mission_stage(self, task_id: str, reviewer: str = "developer", notes: str = "") -> bool:
        """Approves the Stage-Gate review to unlock autonomous execution in the sandbox."""
        mission = self.missions.get(task_id)
        if not mission or not mission.stage_gate:
            return False

        success = mission.stage_gate.approve_stage_gate(reviewer=reviewer, notes=notes)
        if success:
            mission.progress_pct = 50
            mission.updated_at = time.time()
            # Append execution ReAct trace
            mission.stage_gate.add_react_step(
                thought=f"Stage approved by {reviewer}. Commencing multi-file modifications in sandbox.",
                action="sandbox_execute",
                action_input={"worktree": mission.use_isolated_worktree}
            )
        return success

    def inject_mission_feedback(self, task_id: str, feedback: str, author: str = "developer") -> bool:
        """Injects mid-flight human feedback to steer the subagent without restarting."""
        mission = self.missions.get(task_id)
        if not mission or not mission.stage_gate:
            return False

        mission.stage_gate.inject_steering_directive(feedback, author=author)
        mission.updated_at = time.time()
        return True

    def run_mission_verification(self, task_id: str, local_url: Optional[str] = None,
                                 test_command: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Runs the Acceptance stage: executes unit tests and browser verification,
        generating verifiable evidence artifacts.
        """
        mission = self.missions.get(task_id)
        if not mission or not mission.stage_gate:
            return {"success": False, "error": f"Mission '{task_id}' not found"}

        if mission.stage_gate.current_stage == StageStatus.EXECUTION:
            mission.stage_gate.transition_to(StageStatus.ACCEPTANCE, actor="agent", reason="Modifications complete; running verification")

        test_passed = True
        test_output = ""

        # 1. Run unit test suite in sandbox if specified
        if test_command and mission.use_isolated_worktree:
            test_res = self.sandbox_manager.run_command(task_id, test_command)
            test_passed = test_res.get("success", False)
            test_output = test_res.get("stdout", "") + "\n" + test_res.get("stderr", "")

        # 2. Run browser verification if local URL is provided
        browser_report = None
        if local_url:
            browser_report = self.browser_verifier.verify_local_url(local_url, task_id=task_id)
            if not browser_report.passed:
                test_passed = False
            # Save browser evidence artifact
            web_art = self.artifact_engine.create_browser_evidence_artifact(
                task_id=task_id,
                title=f"Browser Verification: {local_url}",
                report_data=browser_report.to_dict(),
                screenshot_path=browser_report.screenshot_path
            )
            mission.artifacts.append(web_art.artifact_id)

        # 3. Generate unified diff artifact
        diff_text = self.sandbox_manager.generate_diff(task_id)
        if diff_text:
            diff_art = self.artifact_engine.create_diff_artifact(
                task_id=task_id,
                title=f"Unified Changes: {mission.title}",
                unified_diff=diff_text
            )
            mission.artifacts.append(diff_art.artifact_id)

        evidence = {
            "passed": test_passed,
            "test_output": test_output,
            "browser_passed": browser_report.passed if browser_report else True
        }

        # Transition stage gate
        completed = mission.stage_gate.complete_acceptance(evidence)
        if completed:
            mission.progress_pct = 100
        else:
            mission.progress_pct = 60

        mission.updated_at = time.time()
        return {
            "success": completed,
            "evidence": evidence,
            "stage": mission.stage_gate.current_stage.value
        }

    def abort_mission(self, task_id: str, reason: str = "User aborted") -> bool:
        """Aborts a subagent mission and cleans up its isolated sandbox."""
        mission = self.missions.get(task_id)
        if not mission:
            return False

        if mission.stage_gate:
            try:
                mission.stage_gate.transition_to(StageStatus.REJECTED, actor="human", reason=reason)
            except Exception:
                pass

        if mission.use_isolated_worktree:
            self.sandbox_manager.cleanup_sandbox(task_id)

        mission.error_message = reason
        mission.updated_at = time.time()
        return True

    def get_all_missions(self) -> List[SubagentMission]:
        """Returns all registered subagent missions."""
        return list(self.missions.values())
