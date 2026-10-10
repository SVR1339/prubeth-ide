"""
SUKHI IDE — Multi-File Transactional Checkpoint & Rollback Engine
Captures pre-edit file state hashes, tracks agent changes across files,
and provides atomic transactional rollback of agent sessions.
"""
import os
import time
import uuid
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from core.workspace import WorkspaceGuard, WorkspaceSecurityError


def compute_sha256(content_or_bytes) -> str:
    if isinstance(content_or_bytes, str):
        data = content_or_bytes.encode("utf-8")
    else:
        data = content_or_bytes
    return hashlib.sha256(data).hexdigest()


@dataclass
class FileSnapshot:
    rel_path: str
    existed_before: bool
    pre_hash: Optional[str] = None
    pre_content: Optional[str] = None
    post_hash: Optional[str] = None


@dataclass
class SessionCheckpoint:
    checkpoint_id: str
    description: str
    created_at: float = field(default_factory=time.time)
    snapshots: Dict[str, FileSnapshot] = field(default_factory=dict)
    is_rolled_back: bool = False


class CheckpointManager:
    """Manages multi-file transactional checkpoints for autonomous agent edits."""

    def __init__(self, workspace_guard: WorkspaceGuard):
        self.guard = workspace_guard
        self.root = self.guard.root
        self._checkpoints: Dict[str, SessionCheckpoint] = {}

    def begin_checkpoint(self, description: str = "") -> str:
        """Starts a new transactional checkpoint session."""
        c_id = f"chk-{uuid.uuid4().hex[:8]}"
        chk = SessionCheckpoint(
            checkpoint_id=c_id,
            description=description or f"Agent Task Checkpoint {c_id}"
        )
        self._checkpoints[c_id] = chk
        return c_id

    def track_file_before_edit(self, checkpoint_id: str, file_path: str) -> bool:
        """Records file existence, content, and hash before an edit takes place."""
        chk = self._checkpoints.get(checkpoint_id)
        if not chk:
            raise KeyError(f"Checkpoint '{checkpoint_id}' not found")

        canon = self.guard.canonicalize(file_path)
        rel = str(canon.relative_to(self.root)).replace("\\", "/")

        if rel in chk.snapshots:
            # Already captured pre-edit state
            return True

        if canon.is_file():
            try:
                content = canon.read_text(encoding="utf-8", errors="replace")
                h = compute_sha256(content)
                chk.snapshots[rel] = FileSnapshot(
                    rel_path=rel,
                    existed_before=True,
                    pre_hash=h,
                    pre_content=content
                )
            except Exception as e:
                return False
        else:
            chk.snapshots[rel] = FileSnapshot(
                rel_path=rel,
                existed_before=False,
                pre_hash=None,
                pre_content=None
            )
        return True

    def track_file_after_edit(self, checkpoint_id: str, file_path: str) -> bool:
        """Records post-edit hash to measure modification."""
        chk = self._checkpoints.get(checkpoint_id)
        if not chk:
            return False

        canon = self.guard.canonicalize(file_path)
        rel = str(canon.relative_to(self.root)).replace("\\", "/")

        snap = chk.snapshots.get(rel)
        if not snap:
            return False

        if canon.is_file():
            try:
                content = canon.read_text(encoding="utf-8", errors="replace")
                snap.post_hash = compute_sha256(content)
            except Exception:
                pass
        return True

    def rollback(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Atomically rolls back all file changes in this checkpoint.
        - Deletes files that did not exist before the task.
        - Replaces modified files with their exact pre-edit content.
        """
        chk = self._checkpoints.get(checkpoint_id)
        if not chk:
            raise KeyError(f"Checkpoint '{checkpoint_id}' not found")

        if chk.is_rolled_back:
            return {
                "success": False,
                "error": f"Checkpoint '{checkpoint_id}' was already rolled back.",
                "restored_files": [],
                "deleted_files": []
            }

        restored = []
        deleted = []
        errors = []

        for rel, snap in chk.snapshots.items():
            canon = self.guard.canonicalize(rel)

            if snap.existed_before:
                # Restore original content
                try:
                    if snap.pre_content is not None:
                        self.guard.safe_write(str(canon), snap.pre_content, backup=False)
                        restored.append(rel)
                except Exception as e:
                    errors.append({"file": rel, "error": str(e)})
            else:
                # File was newly created by agent -> delete it
                try:
                    if canon.exists() and canon.is_file():
                        canon.unlink()
                        deleted.append(rel)
                except Exception as e:
                    errors.append({"file": rel, "error": str(e)})

        chk.is_rolled_back = True

        return {
            "success": len(errors) == 0,
            "checkpoint_id": checkpoint_id,
            "restored_files": restored,
            "deleted_files": deleted,
            "errors": errors
        }

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        return [
            {
                "checkpoint_id": chk.checkpoint_id,
                "description": chk.description,
                "created_at": chk.created_at,
                "file_count": len(chk.snapshots),
                "is_rolled_back": chk.is_rolled_back
            }
            for chk in sorted(self._checkpoints.values(), key=lambda c: c.created_at, reverse=True)
        ]

    def get_checkpoint(self, checkpoint_id: str) -> Optional[SessionCheckpoint]:
        return self._checkpoints.get(checkpoint_id)
