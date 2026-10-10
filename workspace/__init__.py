"""
SUKHI IDE — Workspace Management Subsystem
Provides boundary enforcement, path canonicalization, atomic safe file operations,
and multi-file transactional session checkpoints with rollback.
"""
from core.workspace import WorkspaceGuard, WorkspaceSecurityError
from workspace.checkpoints import CheckpointManager, SessionCheckpoint, FileSnapshot

__all__ = [
    "WorkspaceGuard",
    "WorkspaceSecurityError",
    "CheckpointManager",
    "SessionCheckpoint",
    "FileSnapshot"
]
