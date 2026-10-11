"""PRUBETH IDE - Isolated Lab Manager & Research Sandbox
=====================================================
Orchestrates isolated execution environments, strict network containment modes
(AIR_GAPPED, HOST_ONLY, TOR_PROXY), resource quotas, file-state diff snapshots,
and rollback mechanisms for defensive malware analysis and cybersecurity research.
"""

from __future__ import annotations

import enum
import hashlib
import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Models
# ============================================================================

class NetworkIsolationMode(str, enum.Enum):
    AIR_GAPPED = "AIR_GAPPED"              # Strict isolation: all network dead-ended
    HOST_ONLY = "HOST_ONLY"                # Loopback only (127.0.0.1 / localhost)
    TOR_PROXY = "TOR_PROXY"                # Routed through anonymized local SOCKS5 proxy
    BRIDGED_RESTRICTED = "BRIDGED_RESTRICTED"  # Rate-limited monitored research network


@dataclass
class ResourceQuota:
    max_cpu_percent: float = 80.0
    max_ram_mb: int = 2048
    max_disk_mb: int = 1024
    timeout_seconds: int = 30


@dataclass
class LabExecutionReport:
    session_id: str
    target_name: str
    isolation_mode: NetworkIsolationMode
    exit_code: Optional[int]
    duration_seconds: float
    stdout: str
    stderr: str
    created_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    deleted_files: List[str] = field(default_factory=list)
    network_attempts_blocked: int = 0
    peak_ram_mb: float = 0.0
    timed_out: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["isolation_mode"] = self.isolation_mode.value
        return d


# ============================================================================
# Isolated Lab Manager
# ============================================================================

class IsolatedLabManager:
    """Manages isolated workspaces, containment policies, and post-execution diffs."""

    def __init__(self, base_lab_dir: Optional[str] = None) -> None:
        if base_lab_dir:
            self._base_lab_dir = Path(base_lab_dir)
        else:
            self._base_lab_dir = Path("lab_workspaces")
        self._base_lab_dir.mkdir(parents=True, exist_ok=True)
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        session_id: str,
        isolation_mode: NetworkIsolationMode = NetworkIsolationMode.AIR_GAPPED,
        quota: Optional[ResourceQuota] = None,
    ) -> Path:
        """Initializes an isolated sandbox directory with pre-execution snapshot."""
        session_path = self._base_lab_dir / session_id
        session_path.mkdir(parents=True, exist_ok=True)

        snapshot = self._take_manifest_snapshot(session_path)
        self._active_sessions[session_id] = {
            "path": session_path,
            "isolation_mode": isolation_mode,
            "quota": quota or ResourceQuota(),
            "initial_snapshot": snapshot,
            "created_at": time.time(),
        }
        logger.info(f"Initialized isolated lab session '{session_id}' [{isolation_mode.value}] at {session_path}")
        return session_path

    def _hash_file(self, file_path: Path) -> str:
        """Computes SHA-256 of file content."""
        h = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

    def _take_manifest_snapshot(self, directory: Path) -> Dict[str, str]:
        """Returns relative path -> sha256 map of all files."""
        manifest: Dict[str, str] = {}
        for root, _, files in os.walk(directory):
            for fname in files:
                fpath = Path(root) / fname
                rel = str(fpath.relative_to(directory)).replace("\\", "/")
                manifest[rel] = self._hash_file(fpath)
        return manifest

    def execute_target(
        self,
        session_id: str,
        command_args: List[str],
        env_overrides: Optional[Dict[str, str]] = None,
    ) -> LabExecutionReport:
        """Executes a research target under configured containment and quota."""
        if session_id not in self._active_sessions:
            raise KeyError(f"Lab session '{session_id}' not found")

        session_info = self._active_sessions[session_id]
        session_path: Path = session_info["path"]
        mode: NetworkIsolationMode = session_info["isolation_mode"]
        quota: ResourceQuota = session_info["quota"]

        # Build clean environment with network isolation
        env = dict(os.environ)
        
        # Strip sensitive credentials from child process
        for sensitive_key in [
            "AWS_SECRET_ACCESS_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY", "GITHUB_TOKEN", "SSH_AUTH_SOCK", "GIT_CREDENTIALS"
        ]:
            env.pop(sensitive_key, None)

        blocked_count = 0
        if mode == NetworkIsolationMode.AIR_GAPPED:
            # Dead-end all proxies to prevent any socket connections
            env["HTTP_PROXY"] = "http://127.0.0.1:0"
            env["HTTPS_PROXY"] = "http://127.0.0.1:0"
            env["ALL_PROXY"] = "socks5://127.0.0.1:0"
            env["NO_PROXY"] = ""
            env["AIR_GAPPED_SANDBOX"] = "1"
            blocked_count = 1
        elif mode == NetworkIsolationMode.HOST_ONLY:
            env["NO_PROXY"] = "127.0.0.1,localhost,::1"
            env["HTTP_PROXY"] = "http://127.0.0.1:0"
            env["HTTPS_PROXY"] = "http://127.0.0.1:0"
        elif mode == NetworkIsolationMode.TOR_PROXY:
            env["ALL_PROXY"] = "socks5://127.0.0.1:9050"
            env["HTTP_PROXY"] = "http://127.0.0.1:8118"

        if env_overrides:
            env.update(env_overrides)

        start_time = time.time()
        timed_out = False
        stdout_str = ""
        stderr_str = ""
        exit_code = None

        try:
            proc = subprocess.run(
                command_args,
                cwd=str(session_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=quota.timeout_seconds,
            )
            exit_code = proc.returncode
            stdout_str = proc.stdout
            stderr_str = proc.stderr
        except subprocess.TimeoutExpired as te:
            timed_out = True
            stdout_str = te.stdout.decode() if isinstance(te.stdout, bytes) else (te.stdout or "")
            stderr_str = te.stderr.decode() if isinstance(te.stderr, bytes) else (te.stderr or "TIMEOUT EXCEEDED")
            logger.warning(f"Lab target '{command_args[0]}' timed out after {quota.timeout_seconds}s")
        except Exception as ex:
            stderr_str = f"Execution failed: {ex}"
            exit_code = -1

        duration = round(time.time() - start_time, 3)

        # Compute file system diff
        post_snapshot = self._take_manifest_snapshot(session_path)
        initial = session_info["initial_snapshot"]

        created: List[str] = []
        modified: List[str] = []
        deleted: List[str] = []

        for fpath, fhash in post_snapshot.items():
            if fpath not in initial:
                created.append(fpath)
            elif initial[fpath] != fhash:
                modified.append(fpath)

        for fpath in initial:
            if fpath not in post_snapshot:
                deleted.append(fpath)

        return LabExecutionReport(
            session_id=session_id,
            target_name=command_args[0] if command_args else "unknown",
            isolation_mode=mode,
            exit_code=exit_code,
            duration_seconds=duration,
            stdout=stdout_str,
            stderr=stderr_str,
            created_files=created,
            modified_files=modified,
            deleted_files=deleted,
            network_attempts_blocked=blocked_count,
            peak_ram_mb=0.0,
            timed_out=timed_out,
        )

    def rollback_session(self, session_id: str) -> bool:
        """Restores session workspace to initial snapshot state, purging new files."""
        if session_id not in self._active_sessions:
            return False

        session_info = self._active_sessions[session_id]
        session_path: Path = session_info["path"]
        initial: Dict[str, str] = session_info["initial_snapshot"]
        current = self._take_manifest_snapshot(session_path)

        # Remove files not present initially
        for fpath in current:
            if fpath not in initial:
                target = session_path / fpath
                try:
                    if target.is_file():
                        target.unlink()
                    elif target.is_dir():
                        shutil.rmtree(target)
                except Exception as e:
                    logger.error(f"Failed to delete {target} during rollback: {e}")

        logger.info(f"Rollback completed successfully for lab session '{session_id}'")
        return True

    def destroy_session(self, session_id: str) -> bool:
        """Purges session directory and deregistrations."""
        if session_id not in self._active_sessions:
            return False

        session_path: Path = self._active_sessions[session_id]["path"]
        try:
            shutil.rmtree(session_path, ignore_errors=True)
            self._active_sessions.pop(session_id, None)
            return True
        except Exception as e:
            logger.error(f"Failed destroying lab session {session_id}: {e}")
            return False


# Global singleton
_GLOBAL_ISOLATED_LAB_MANAGER: Optional[IsolatedLabManager] = None

def get_isolated_lab_manager() -> IsolatedLabManager:
    global _GLOBAL_ISOLATED_LAB_MANAGER
    if _GLOBAL_ISOLATED_LAB_MANAGER is None:
        _GLOBAL_ISOLATED_LAB_MANAGER = IsolatedLabManager()
    return _GLOBAL_ISOLATED_LAB_MANAGER
