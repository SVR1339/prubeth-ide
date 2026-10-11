"""
PRUBETH IDE — Code-OSS Fork Multi-File Composer Engine
Implements Cursor / Windsurf style agentic multi-file code composition with transactional rollbacks.
"""
import os
import re
import difflib
from pathlib import Path
from typing import Dict, List, Any, Optional


class FileDiffPlan:
    """Represents a planned change to a single file in the workspace."""
    def __init__(self, file_path: str, original_content: str, proposed_content: str, is_new: bool = False):
        self.file_path = file_path
        self.original_content = original_content
        self.proposed_content = proposed_content
        self.is_new = is_new
        self.applied = False

    @property
    def diff_unified(self) -> str:
        orig_lines = self.original_content.splitlines(keepends=True)
        prop_lines = self.proposed_content.splitlines(keepends=True)
        return "".join(difflib.unified_diff(
            orig_lines, prop_lines,
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}"
        ))

    @property
    def unified_diff(self) -> str:
        return self.diff_unified

    @property
    def additions_count(self) -> int:
        return sum(1 for line in self.diff_unified.splitlines() if line.startswith("+") and not line.startswith("+++"))

    @property
    def deletions_count(self) -> int:
        return sum(1 for line in self.diff_unified.splitlines() if line.startswith("-") and not line.startswith("---"))


class ComposerEngine:
    """
    Coordinates multi-file autonomous generation, AST validation,
    transactional checkpoints, and atomic apply/rollback.
    """
    def __init__(self, workspace_root: Path, checkpoint_manager=None):
        self.workspace_root = Path(workspace_root).resolve()
        self.checkpoint_manager = checkpoint_manager
        self.current_plan: Dict[str, FileDiffPlan] = {}
        self.active_checkpoint_id: Optional[str] = None

    def plan_file_change(self, rel_path: str, proposed_content: str) -> FileDiffPlan:
        """Stages a planned file change for multi-file review."""
        full_path = (self.workspace_root / rel_path).resolve()
        # Security check: must remain inside workspace root
        if not str(full_path).startswith(str(self.workspace_root)):
            raise PermissionError(f"Target file {rel_path} traverses outside workspace root.")

        is_new = not full_path.exists()
        orig_content = full_path.read_text(encoding="utf-8", errors="replace") if not is_new else ""

        plan = FileDiffPlan(rel_path, orig_content, proposed_content, is_new=is_new)
        self.current_plan[rel_path] = plan
        return plan

    def parse_composer_response(self, text: str) -> List[FileDiffPlan]:
        """
        Parses multi-file XML or fenced code block blocks:
        <composer:file path="src/main.py">...</composer:file>
        or ```python path="src/main.py"
        """
        plans = []
        # Pattern 1: XML tags
        xml_matches = re.findall(r'<composer:file\s+path=["\']([^"\']+)["\']>(.*?)</composer:file>', text, re.DOTALL)
        for rel_path, content in xml_matches:
            plan = self.plan_file_change(rel_path.strip(), content.strip() + "\n")
            plans.append(plan)

        # Pattern 2: Markdown fence with file path header
        if not plans:
            fence_matches = re.findall(r'(?:###?\s*File:\s*([^\n\r]+)|```[a-zA-Z0-9_\-]*\s+path=["\']?([^\n\r"\']+)["\']?)\s*\n(.*?)```', text, re.DOTALL)
            for m1, m2, content in fence_matches:
                p = (m1 or m2).strip()
                if p:
                    plan = self.plan_file_change(p, content.strip() + "\n")
                    plans.append(plan)

        return plans

    def apply_all(self, description: str = "Composer multi-file edit") -> Dict[str, Any]:
        """Atomically commits all planned file modifications to disk."""
        if not self.current_plan:
            return {"success": False, "error": "No file changes staged in composer plan."}

        # 1. Begin transactional checkpoint
        if self.checkpoint_manager:
            self.active_checkpoint_id = self.checkpoint_manager.begin_checkpoint(description)

        modified = []
        try:
            for rel_path, plan in self.current_plan.items():
                target = self.workspace_root / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)

                if self.checkpoint_manager and self.active_checkpoint_id:
                    self.checkpoint_manager.track_file_before_edit(self.active_checkpoint_id, str(target))

                target.write_text(plan.proposed_content, encoding="utf-8")
                plan.applied = True

                if self.checkpoint_manager and self.active_checkpoint_id:
                    self.checkpoint_manager.track_file_after_edit(self.active_checkpoint_id, str(target))

                modified.append(rel_path)

            return {
                "success": True,
                "checkpoint_id": self.active_checkpoint_id,
                "modified_files": modified,
                "file_count": len(modified)
            }
        except Exception as ex:
            # If any failure occurs, automatically rollback
            if self.checkpoint_manager and self.active_checkpoint_id:
                self.rollback()
            return {"success": False, "error": str(ex)}

    def rollback(self) -> Dict[str, Any]:
        """Rolls back the composer changeset cleanly."""
        if not self.active_checkpoint_id or not self.checkpoint_manager:
            return {"success": False, "error": "No active checkpoint available for rollback."}

        res = self.checkpoint_manager.rollback(self.active_checkpoint_id)
        for plan in self.current_plan.values():
            plan.applied = False
        self.current_plan.clear()
        self.active_checkpoint_id = None
        return res
