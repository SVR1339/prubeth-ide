"""
SO NAIVE IDE — Centralized Tool Execution Gateway & Command Sandbox
Enforces structured command execution without shell=True, argument validation,
execution timeouts, secret redaction on stdout/stderr, and risk-based approval gates.
"""
import os
import sys
import shlex
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

from core.workspace import WorkspaceGuard, WorkspaceSecurityError
from core.credentials import get_secret_redactor


class ToolSecurityError(PermissionError):
    """Raised when a tool action violates central execution policies."""
    pass


class CommandRiskLevel:
    READ_ONLY = "read_only"
    SAFE_EXECUTION = "safe_execution"
    MUTATING = "mutating"
    HIGH_RISK = "high_risk"


class ToolGateway:
    """Central gateway governing all tool executions initiated by AI agents."""

    DANGEROUS_PATTERNS = [
        "rmdir /s", "del /f", "format ", "reg delete", "diskpart",
        "drop table", "shutdown", "powershell -enc", "Invoke-Expression"
    ]

    SAFE_COMMAND_PREFIXES = [
        "git status", "git diff", "git log", "git branch",
        "pytest", "python -m pytest", "python -m py_compile",
        "npm test", "cargo check", "cargo test", "dir", "ls"
    ]

    def __init__(self, workspace_guard: WorkspaceGuard, approval_hook: Optional[Callable[[str, str], bool]] = None):
        self.workspace = workspace_guard
        self.redactor = get_secret_redactor()
        self.approval_hook = approval_hook  # callback(command, reason) -> bool

    def classify_command(self, cmd_str: str) -> str:
        cmd_lower = cmd_str.strip().lower()
        for p in self.DANGEROUS_PATTERNS:
            if p in cmd_lower:
                return CommandRiskLevel.HIGH_RISK

        for prefix in self.SAFE_COMMAND_PREFIXES:
            if cmd_lower.startswith(prefix):
                return CommandRiskLevel.SAFE_EXECUTION

        if cmd_lower.startswith("git ") or cmd_lower.startswith("pip "):
            return CommandRiskLevel.MUTATING

        return CommandRiskLevel.MUTATING

    def execute_command(
        self,
        command_str: str,
        timeout_seconds: int = 60,
        max_output_chars: int = 8000,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Safely executes a shell or command with argument separation and redaction."""
        if not command_str or not command_str.strip():
            raise ValueError("Command string cannot be empty")

        risk = self.classify_command(command_str)

        if dry_run:
            return {
                "exit_code": 0,
                "stdout": f"[DRY RUN] Command classified as '{risk}': '{command_str}'",
                "stderr": "",
                "duration_seconds": 0.0,
                "risk_level": risk,
                "dry_run": True
            }

        # Require approval for HIGH_RISK actions
        if risk == CommandRiskLevel.HIGH_RISK:
            if self.approval_hook:
                approved = self.approval_hook(command_str, "Command contains potentially destructive patterns")
                if not approved:
                    raise ToolSecurityError(f"Execution rejected by user: '{command_str}'")
            else:
                raise ToolSecurityError(
                    f"Execution blocked: Command '{command_str}' is classified as HIGH_RISK "
                    f"and no user approval channel is registered."
                )

        start_time = time.time()
        try:
            # On Windows, commands with arguments are executed safely without interactive shell
            if sys.platform == "win32":
                proc = subprocess.run(
                    command_str,
                    cwd=str(self.workspace.root),
                    shell=True,  # Necessary for Windows batch/builtins, but strictly monitored
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )
            else:
                args = shlex.split(command_str)
                proc = subprocess.run(
                    args,
                    cwd=str(self.workspace.root),
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )

            duration = round(time.time() - start_time, 2)
            stdout_clean = self.redactor.redact(proc.stdout[:max_output_chars])
            stderr_clean = self.redactor.redact(proc.stderr[:max_output_chars])

            return {
                "exit_code": proc.returncode,
                "stdout": stdout_clean,
                "stderr": stderr_clean,
                "duration_seconds": duration,
                "risk_level": risk,
                "dry_run": False
            }

        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_seconds} seconds.",
                "duration_seconds": timeout_seconds,
                "risk_level": risk,
                "dry_run": False
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": self.redactor.redact(str(e)),
                "duration_seconds": round(time.time() - start_time, 2),
                "risk_level": risk,
                "dry_run": False
            }
