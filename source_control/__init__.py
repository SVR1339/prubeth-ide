"""
SUKHI IDE — Source Control Subsystem
Provides Git repository detection, porcelain status parsing, diff generation,
staging, unstaging, commit composition, and branch management.
"""
from source_control.git_service import GitService, GitStatus, GitFileChange

__all__ = [
    "GitService",
    "GitStatus",
    "GitFileChange"
]
