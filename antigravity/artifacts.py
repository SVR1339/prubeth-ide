"""
PRUBETH IDE — Antigravity Artifact Engine & Mid-Flight Review System
Solves the HCI "Trust Gap" via Verifiable, Inspectable Output:
1. Implementation Plans & Task Checklists: Structured roadmaps generated before code execution.
2. Interactive Diffs: Unified visual hunks highlighting modifications before physical disk writes.
3. Google Docs-style Inline Commenting Loops: Developers highlight line ranges within an artifact
   to add mid-flight feedback, steering execution without stopping or resetting the agent process.
"""
import os
import json
import time
import uuid
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any


class ArtifactType(str, Enum):
    IMPLEMENTATION_PLAN = "IMPLEMENTATION_PLAN"
    TASK_CHECKLIST = "TASK_CHECKLIST"
    INTERACTIVE_DIFF = "INTERACTIVE_DIFF"
    BROWSER_VERIFICATION = "BROWSER_VERIFICATION"
    VISUAL_SCREENSHOT = "VISUAL_SCREENSHOT"
    TEST_EVIDENCE = "TEST_EVIDENCE"
    ARCHITECTURE_SPEC = "ARCHITECTURE_SPEC"


@dataclass
class ArtifactComment:
    """A Google-Docs-style inline comment attached to an artifact line range."""
    comment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    artifact_id: str = ""
    line_start: int = 1
    line_end: int = 1
    author: str = "developer"
    content: str = ""
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolution_note: Optional[str] = None
    steer_directive: bool = True  # If True, automatically fed into agent's ReAct context

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChecklistItem:
    """Individual item in a structured task checklist."""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4())[:6])
    description: str = ""
    completed: bool = False
    file_target: Optional[str] = None
    order: int = 0


@dataclass
class Artifact:
    """A verifiable, human-inspectable deliverable produced by an autonomous subagent."""
    artifact_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_id: str = ""
    title: str = ""
    artifact_type: ArtifactType = ArtifactType.IMPLEMENTATION_PLAN
    file_name: str = ""
    content: str = ""
    binary_path: Optional[str] = None
    version: int = 1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    comments: List[ArtifactComment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["artifact_type"] = self.artifact_type.value
        return d


class ArtifactEngine:
    """Manages the creation, persistence, inspection, and review comments for subagent artifacts."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()
        self.artifacts_dir = self.workspace_root / ".antigravity" / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts: Dict[str, Artifact] = {}
        self._load_cached_artifacts()

    def _get_task_dir(self, task_id: str) -> Path:
        d = self.artifacts_dir / task_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def create_plan_artifact(self, task_id: str, title: str, markdown_plan: str,
                             checklists: Optional[List[Dict[str, Any]]] = None) -> Artifact:
        """Creates an implementation plan artifact."""
        art_id = f"plan-{uuid.uuid4().hex[:6]}"
        file_name = "implementation_plan.md"
        meta = {"items": checklists or []}

        artifact = Artifact(
            artifact_id=art_id,
            task_id=task_id,
            title=title,
            artifact_type=ArtifactType.IMPLEMENTATION_PLAN,
            file_name=file_name,
            content=markdown_plan,
            metadata=meta
        )
        self.save_artifact(artifact)
        return artifact

    def create_checklist_artifact(self, task_id: str, title: str, items: List[Dict[str, Any]]) -> Artifact:
        """Creates a structured task checklist artifact."""
        art_id = f"chk-{uuid.uuid4().hex[:6]}"
        content = json.dumps(items, indent=2)

        artifact = Artifact(
            artifact_id=art_id,
            task_id=task_id,
            title=title,
            artifact_type=ArtifactType.TASK_CHECKLIST,
            file_name="task_checklist.json",
            content=content,
            metadata={"items": items}
        )
        self.save_artifact(artifact)
        return artifact

    def create_diff_artifact(self, task_id: str, title: str, unified_diff: str,
                             files_touched: Optional[List[str]] = None) -> Artifact:
        """Creates an interactive unified diff artifact."""
        art_id = f"diff-{uuid.uuid4().hex[:6]}"
        artifact = Artifact(
            artifact_id=art_id,
            task_id=task_id,
            title=title,
            artifact_type=ArtifactType.INTERACTIVE_DIFF,
            file_name="changes.patch",
            content=unified_diff,
            metadata={"files_touched": files_touched or []}
        )
        self.save_artifact(artifact)
        return artifact

    def create_browser_evidence_artifact(self, task_id: str, title: str, report_data: Dict[str, Any],
                                         screenshot_path: Optional[str] = None) -> Artifact:
        """Creates a browser verification evidence artifact."""
        art_id = f"web-{uuid.uuid4().hex[:6]}"
        artifact = Artifact(
            artifact_id=art_id,
            task_id=task_id,
            title=title,
            artifact_type=ArtifactType.BROWSER_VERIFICATION,
            file_name="browser_verification.json",
            content=json.dumps(report_data, indent=2),
            binary_path=screenshot_path,
            metadata=report_data
        )
        self.save_artifact(artifact)
        return artifact

    def save_artifact(self, artifact: Artifact):
        """Persists the artifact to the disk storage."""
        task_dir = self._get_task_dir(artifact.task_id)
        file_path = task_dir / artifact.file_name

        if artifact.content:
            file_path.write_text(artifact.content, encoding="utf-8")

        meta_path = task_dir / f"{artifact.artifact_id}.meta.json"
        meta_path.write_text(json.dumps(artifact.to_dict(), indent=2), encoding="utf-8")

        self.artifacts[artifact.artifact_id] = artifact

    def add_inline_comment(self, artifact_id: str, line_start: int, line_end: int,
                           content: str, author: str = "developer") -> ArtifactComment:
        """
        Adds a Google-Docs-style mid-flight comment to an artifact.
        If steer_directive is True, this can immediately guide the agent.
        """
        art = self.artifacts.get(artifact_id)
        if not art:
            raise KeyError(f"Artifact '{artifact_id}' not found")

        comment = ArtifactComment(
            artifact_id=artifact_id,
            line_start=line_start,
            line_end=line_end,
            author=author,
            content=content,
            timestamp=time.time(),
            resolved=False,
            steer_directive=True
        )
        art.comments.append(comment)
        art.updated_at = time.time()
        self.save_artifact(art)
        return comment

    def resolve_comment(self, artifact_id: str, comment_id: str, note: str = "") -> bool:
        """Marks an inline comment as resolved."""
        art = self.artifacts.get(artifact_id)
        if not art:
            return False

        for c in art.comments:
            if c.comment_id == comment_id:
                c.resolved = True
                c.resolution_note = note
                self.save_artifact(art)
                return True
        return False

    def get_unresolved_comments(self, artifact_id: str) -> List[ArtifactComment]:
        """Returns all unresolved comments on an artifact."""
        art = self.artifacts.get(artifact_id)
        if not art:
            return []
        return [c for c in art.comments if not c.resolved]

    def get_task_artifacts(self, task_id: str) -> List[Artifact]:
        """Returns all artifacts belonging to a specific task."""
        return [a for a in self.artifacts.values() if a.task_id == task_id]

    def _load_cached_artifacts(self):
        """Discovers existing artifact metadata files on disk."""
        if not self.artifacts_dir.exists():
            return
        for root, _, files in os.walk(self.artifacts_dir):
            for f in files:
                if f.endswith(".meta.json"):
                    try:
                        p = Path(root) / f
                        data = json.loads(p.read_text(encoding="utf-8"))
                        art_id = data["artifact_id"]
                        comments = [ArtifactComment(**c) for c in data.get("comments", [])]
                        art = Artifact(
                            artifact_id=art_id,
                            task_id=data["task_id"],
                            title=data["title"],
                            artifact_type=ArtifactType(data["artifact_type"]),
                            file_name=data["file_name"],
                            content=data.get("content", ""),
                            binary_path=data.get("binary_path"),
                            version=data.get("version", 1),
                            created_at=data.get("created_at", time.time()),
                            updated_at=data.get("updated_at", time.time()),
                            comments=comments,
                            metadata=data.get("metadata", {})
                        )
                        self.artifacts[art_id] = art
                    except Exception:
                        pass
