"""
SUKHI IDE — Multi-File Transactional Checkpoint & Rollback Engine
Captures pre-edit file state hashes, tracks agent changes across files,
persists checkpoints across IDE sessions, and provides two-phase atomic transactional rollback.
"""
import os
import json
import time
import uuid
import shutil
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
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
    """Manages multi-file transactional checkpoints for autonomous agent edits with disk persistence."""

    def __init__(self, workspace_guard: WorkspaceGuard, storage_dir: Optional[Path] = None):
        self.guard = workspace_guard
        self.root = self.guard.root
        self.storage_dir = Path(storage_dir) if storage_dir else (self.root / ".local_ai_studio_pro")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "checkpoints.json"

        self._checkpoints: Dict[str, SessionCheckpoint] = {}
        self._load_from_disk()

    def _save_to_disk(self):
        try:
            data = {}
            for c_id, chk in self._checkpoints.items():
                data[c_id] = {
                    "checkpoint_id": chk.checkpoint_id,
                    "description": chk.description,
                    "created_at": chk.created_at,
                    "is_rolled_back": chk.is_rolled_back,
                    "snapshots": {
                        rel: asdict(snap) for rel, snap in chk.snapshots.items()
                    }
                }
            tmp_file = self.storage_file.with_suffix(".tmp")
            tmp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp_file.replace(self.storage_file)
        except Exception:
            pass

    def _load_from_disk(self):
        if not self.storage_file.exists():
            return
        try:
            data = json.loads(self.storage_file.read_text(encoding="utf-8"))
            for c_id, chk_dict in data.items():
                snaps = {}
                for rel, s_dict in chk_dict.get("snapshots", {}).items():
                    snaps[rel] = FileSnapshot(**s_dict)
                self._checkpoints[c_id] = SessionCheckpoint(
                    checkpoint_id=chk_dict["checkpoint_id"],
                    description=chk_dict["description"],
                    created_at=chk_dict.get("created_at", time.time()),
                    snapshots=snaps,
                    is_rolled_back=chk_dict.get("is_rolled_back", False)
                )
        except Exception:
            pass

    def begin_checkpoint(self, description: str = "") -> str:
        """Starts a new transactional checkpoint session."""
        c_id = f"chk-{uuid.uuid4().hex[:8]}"
        chk = SessionCheckpoint(
            checkpoint_id=c_id,
            description=description or f"Agent Task Checkpoint {c_id}"
        )
        self._checkpoints[c_id] = chk
        self._save_to_disk()
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
            except Exception:
                return False
        else:
            chk.snapshots[rel] = FileSnapshot(
                rel_path=rel,
                existed_before=False,
                pre_hash=None,
                pre_content=None
            )
        self._save_to_disk()
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
                self._save_to_disk()
            except Exception:
                pass
        return True

    def rollback(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Two-phase atomic rollback of all file changes in this checkpoint.
        Phase 1: Captures shadow backup of all target files before rollback.
        Phase 2: Restores original contents and deletes newly created files.
        If any failure occurs, automatically reverts to shadow stage to prevent data loss.
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

        # Phase 1: Shadow capture of live files before rollback application
        shadow_backup: Dict[str, Optional[str]] = {}
        for rel in chk.snapshots.keys():
            canon = self.guard.canonicalize(rel)
            if canon.is_file():
                try:
                    shadow_backup[rel] = canon.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    shadow_backup[rel] = None
            else:
                shadow_backup[rel] = None

        restored = []
        deleted = []
        errors = []

        # Phase 2: Atomic execution
        try:
            for rel, snap in chk.snapshots.items():
                canon = self.guard.canonicalize(rel)

                if snap.existed_before:
                    if snap.pre_content is not None:
                        self.guard.safe_write(str(canon), snap.pre_content, backup=False)
                        restored.append(rel)
                else:
                    if canon.exists() and canon.is_file():
                        canon.unlink()
                        deleted.append(rel)

            chk.is_rolled_back = True
            self._save_to_disk()

            return {
                "success": True,
                "checkpoint_id": checkpoint_id,
                "restored_files": restored,
                "deleted_files": deleted,
                "errors": []
            }

        except Exception as ex:
            # Atomic rollback recovery: revert to pre-rollback shadow state
            recovery_errors = []
            for rel, content in shadow_backup.items():
                canon = self.guard.canonicalize(rel)
                try:
                    if content is not None:
                        self.guard.safe_write(str(canon), content, backup=False)
                    else:
                        if canon.exists() and canon.is_file():
                            canon.unlink()
                except Exception as r_ex:
                    recovery_errors.append(str(r_ex))

            return {
                "success": False,
                "checkpoint_id": checkpoint_id,
                "error": f"Transactional rollback failed and was safely aborted: {str(ex)}",
                "restored_files": [],
                "deleted_files": [],
                "recovery_errors": recovery_errors
            }

    def rollback_checkpoint(self, checkpoint_id: str) -> bool:
        """Convenience method returning bool for UI compatibility."""
        res = self.rollback(checkpoint_id)
        return res.get("success", False)

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
