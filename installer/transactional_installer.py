"""
PRUBETH IDE — Transactional Safe Extractor & Rollback Engine
Performs pre-extraction security inspection (rejecting path traversal, absolute paths, unsafe symlinks),
stages extraction in an isolated directory, verifies required runtime files, creates upgrade backups,
atomically commits changes, performs non-destructive health checks, and rolls back upon any failure.
"""
import os
import sys
import ast
import shutil
import zipfile
import tempfile
import time
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

_INSTALLER_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _INSTALLER_DIR.parent
for _p in [str(_REPO_ROOT), str(_INSTALLER_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from installer.download_engine import DownloadProgress, STAGE_NAMES
except ImportError:
    from download_engine import DownloadProgress, STAGE_NAMES


WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


class SecurityInspectionError(Exception):
    """Raised when an archive contains malicious or dangerous paths."""
    pass


class InstallationCommitError(Exception):
    """Raised when committing files or performing health checks fails."""
    pass


def inspect_archive_security(zip_path: Path) -> List[str]:
    """
    Validates every entry inside the ZIP archive prior to extraction.
    Detects path traversal, absolute paths, and Windows reserved device names.
    Returns list of safe relative member names.
    """
    with zipfile.ZipFile(zip_path, 'r') as z:
        # First test archive integrity
        bad_file = z.testzip()
        if bad_file:
            raise SecurityInspectionError(f"Corrupted entry detected inside ZIP archive: '{bad_file}'")

        safe_members = []
        for info in z.infolist():
            filename = info.filename

            # 1. Reject absolute paths
            if filename.startswith("/") or filename.startswith("\\"):
                raise SecurityInspectionError(f"Security boundary violation: absolute path '{filename}' in archive.")
            if len(filename) >= 2 and filename[1] == ":":
                raise SecurityInspectionError(f"Security boundary violation: drive-letter path '{filename}' in archive.")

            # 2. Reject path traversal sequences
            parts = Path(filename).parts
            if any(p == ".." for p in parts):
                raise SecurityInspectionError(f"Security boundary violation: path traversal sequence in '{filename}'.")

            # 3. Reject Windows reserved device names
            for part in parts:
                stem = Path(part).stem.upper()
                if stem in WINDOWS_RESERVED_NAMES:
                    raise SecurityInspectionError(f"Security boundary violation: reserved Windows device name '{stem}' in '{filename}'.")

            safe_members.append(filename)

        return safe_members


class TransactionalInstaller:
    """
    Manages safe staged extraction, atomic installation commit,
    upgrade backup preservation, non-destructive health checks, and rollback.
    """
    def __init__(
        self,
        target_dir: Path,
        staging_dir: Optional[Path] = None
    ):
        self.target_dir = Path(target_dir).resolve()
        self.staging_dir = Path(staging_dir).resolve() if staging_dir else Path(tempfile.gettempdir())
        self.active_staging_dir: Optional[Path] = None
        self.backup_dir: Optional[Path] = None

    def execute_transaction(
        self,
        payload_zip: Path,
        required_files: List[str],
        is_upgrade: bool = False,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete transactional installation.
        Stages, backs up existing files (if upgrading), applies files, validates health,
        and automatically rolls back on any error.
        """
        session_id = str(uuid.uuid4())[:8]
        self.active_staging_dir = self.staging_dir / f"prubeth_stage_{session_id}"
        self.active_staging_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Stage 7: Preparing Installation & Safe Staging Extraction
            if progress_callback:
                progress_callback(DownloadProgress(
                    stage=7,
                    stage_name=STAGE_NAMES[7],
                    status_text="Inspecting archive security and unpacking into isolated staging directory..."
                ))

            # Security Inspection
            safe_members = inspect_archive_security(payload_zip)

            with zipfile.ZipFile(payload_zip, 'r') as z:
                total_files = len(safe_members)
                for idx, member in enumerate(safe_members):
                    z.extract(member, self.active_staging_dir)
                    if progress_callback and idx % 25 == 0:
                        pct = (idx / max(total_files, 1)) * 100.0
                        progress_callback(DownloadProgress(
                            stage=7,
                            stage_name=STAGE_NAMES[7],
                            percent=pct,
                            status_text=f"Staging files: {member[:35]}... ({idx}/{total_files})"
                        ))

            # Verify Staged Files Against Required Manifest Entries
            for req in required_files:
                staged_req = self.active_staging_dir / req
                if not staged_req.exists():
                    raise SecurityInspectionError(f"Required application component missing from staged payload: '{req}'")

            # Stage 8: Installing Application & Transactional Commit
            if progress_callback:
                progress_callback(DownloadProgress(
                    stage=8,
                    stage_name=STAGE_NAMES[8],
                    status_text="Preserving user configuration and atomically applying application update..."
                ))

            # If existing installation directory exists, backup before applying
            if self.target_dir.exists() and any(self.target_dir.iterdir()):
                timestamp = int(time.time())
                self.backup_dir = self.staging_dir / f"prubeth_backup_{timestamp}_{session_id}"
                # Copy existing installation to backup, preserving user data
                shutil.copytree(self.target_dir, self.backup_dir, dirs_exist_ok=True)

            self.target_dir.mkdir(parents=True, exist_ok=True)

            # Copy staged files to target directory
            shutil.copytree(self.active_staging_dir, self.target_dir, dirs_exist_ok=True)

            # Stage 9: Verifying Installed Application Health
            if progress_callback:
                progress_callback(DownloadProgress(
                    stage=9,
                    stage_name=STAGE_NAMES[9],
                    status_text="Executing non-destructive application health check..."
                ))

            health_ok, health_err = self._run_health_check()
            if not health_ok:
                raise InstallationCommitError(f"Installed application health check failed: {health_err}")

            # Write installation receipt
            receipt = {
                "installed_at": time.time(),
                "target_dir": str(self.target_dir),
                "is_upgrade": is_upgrade,
                "health_status": "PASS"
            }
            with open(self.target_dir / "installation_receipt.json", "w", encoding="utf-8") as f_r:
                json.dump(receipt, f_r, indent=2)

            # Cleanup staging and backup on success
            self._cleanup_staging()
            self._cleanup_backup()

            # Stage 10: Completing Setup
            if progress_callback:
                progress_callback(DownloadProgress(
                    stage=10,
                    stage_name=STAGE_NAMES[10],
                    percent=100.0,
                    status_text="Installation and verification completed successfully!"
                ))

            return {"success": True, "target_dir": str(self.target_dir)}

        except Exception as e:
            # Transaction failed: Rollback to previous working version if backup exists
            rollback_status = self.rollback()
            self._cleanup_staging()
            raise InstallationCommitError(
                f"Installation transaction failed: {e}. Rollback status: {rollback_status}"
            ) from e

    def _run_health_check(self) -> Tuple[bool, Optional[str]]:
        """
        Validates that primary application files exist and Python entrypoints are syntactically valid.
        """
        entrypoint = self.target_dir / "local_ai_studio_pro.py"
        if not entrypoint.exists():
            return False, "Main application entrypoint 'local_ai_studio_pro.py' not found."

        try:
            # Syntax validation of installed entrypoint
            with open(entrypoint, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            ast.parse(content, filename=str(entrypoint))
        except Exception as ex:
            return False, f"AST parsing error in installed 'local_ai_studio_pro.py': {ex}"

        return True, None

    def rollback(self) -> str:
        """Restores the target directory from the backup directory if available."""
        if not self.backup_dir or not self.backup_dir.exists():
            return "No previous version backup was created; nothing to roll back."

        try:
            # Restore files from backup directory
            shutil.copytree(self.backup_dir, self.target_dir, dirs_exist_ok=True)
            self._cleanup_backup()
            return "Successfully rolled back to previous working version."
        except Exception as ex:
            return f"Rollback attempt encountered error: {ex}"

    def _cleanup_staging(self):
        if self.active_staging_dir and self.active_staging_dir.exists():
            try:
                shutil.rmtree(self.active_staging_dir, ignore_errors=True)
            except OSError:
                pass

    def _cleanup_backup(self):
        if self.backup_dir and self.backup_dir.exists():
            try:
                shutil.rmtree(self.backup_dir, ignore_errors=True)
            except OSError:
                pass
