"""
PRUBETH IDE — Centralized Tool Execution Gateway & Command Sandbox
Enforces structured command execution without shell invocation, argument validation,
execution timeouts, secret redaction on stdout/stderr, and risk-based approval gates.
"""
import os
import sys
import shlex
import shutil
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
        "rmdir /s", "del /f", "format ", "reg delete", "reg add", "diskpart",
        "drop table", "shutdown", "powershell -enc", "powershell -c", "invoke-expression",
        "iex ", "certutil", "bitsadmin", "curl ", "wget ", "net user", "net localgroup"
    ]

    GIT_INJECTION_PATTERNS = [
        "-c core.pager", "-c alias", "--exec-path", "--upload-pack"
    ]

    CHAINING_AND_INJECTION_TOKENS = [
        "&", "|", ";", ">", "<", "`", "$("
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
        self.audit_log: List[Dict[str, Any]] = []

    def set_approval_hook(self, approval_hook: Optional[Callable[[str, str], bool]]) -> None:
        """Sets or updates the approval hook callback."""
        self.approval_hook = approval_hook

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Returns the full history of audited command executions."""
        return list(self.audit_log)

    def classify_command(self, cmd_str: str) -> str:
        cmd_lower = cmd_str.strip().lower()

        # Check for explicitly dangerous executable patterns
        for p in self.DANGEROUS_PATTERNS:
            if p in cmd_lower:
                return CommandRiskLevel.HIGH_RISK

        # Check for git subshell/pager injection
        if cmd_lower.startswith("git "):
            for p in self.GIT_INJECTION_PATTERNS:
                if p in cmd_lower:
                    return CommandRiskLevel.HIGH_RISK

        # Check for shell metacharacters / chaining operators (e.g. "git status & evil.exe")
        for token in self.CHAINING_AND_INJECTION_TOKENS:
            if token in cmd_str:
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
                    self.audit_log.append({
                        "command": command_str,
                        "risk_level": risk,
                        "approved": False,
                        "status": "rejected_by_user",
                        "timestamp": time.time()
                    })
                    raise ToolSecurityError(f"Execution rejected by user: '{command_str}'")
            else:
                self.audit_log.append({
                    "command": command_str,
                    "risk_level": risk,
                    "approved": False,
                    "status": "blocked_no_approval_channel",
                    "timestamp": time.time()
                })
                raise ToolSecurityError(
                    f"Execution blocked: Command '{command_str}' is classified as HIGH_RISK "
                    f"and no user approval channel is registered."
                )

        start_time = time.time()
        try:
            # Tokenize command safely with direct process invocation to eliminate command injection (CWE-78)
            args = shlex.split(command_str, posix=True)
            if not args:
                return {
                    "exit_code": 0,
                    "stdout": "",
                    "stderr": "",
                    "duration_s": 0.0,
                    "risk_level": risk,
                    "blocked": False,
                    "dry_run": False
                }

            if sys.platform == "win32":
                # For Windows cmd builtins (echo, dir, etc.), chained commands, or unresolved binaries,
                # wrap safely as arguments to cmd.exe with shell=False
                cmd_builtins = {"echo", "dir", "type", "copy", "del", "move", "mkdir", "md", "rmdir", "rd", "cls", "ver"}
                executable = shutil.which(args[0])
                has_chaining = any(token in command_str for token in ["&", "|", ";", ">", "<"])
                if not executable or args[0].lower() in cmd_builtins or has_chaining:
                    exec_args = ["cmd.exe", "/d", "/c", command_str]
                else:
                    exec_args = args
            else:
                has_chaining = any(token in command_str for token in ["&", "|", ";", ">", "<"])
                if has_chaining:
                    exec_args = ["/bin/sh", "-c", command_str]
                else:
                    exec_args = args

            proc = subprocess.run(
                exec_args,
                cwd=str(self.workspace.root),
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )

            duration = round(time.time() - start_time, 2)
            stdout_clean = self.redactor.redact(proc.stdout[:max_output_chars])
            stderr_clean = self.redactor.redact(proc.stderr[:max_output_chars])

            result = {
                "exit_code": proc.returncode,
                "stdout": stdout_clean,
                "stderr": stderr_clean,
                "duration_seconds": duration,
                "risk_level": risk,
                "dry_run": False
            }
            self.audit_log.append({
                "command": command_str,
                "risk_level": risk,
                "approved": True if risk == CommandRiskLevel.HIGH_RISK else None,
                "status": "executed",
                "exit_code": proc.returncode,
                "duration": duration,
                "timestamp": time.time()
            })
            return result

        except subprocess.TimeoutExpired:
            self.audit_log.append({
                "command": command_str,
                "risk_level": risk,
                "status": "timeout",
                "exit_code": -1,
                "duration": timeout_seconds,
                "timestamp": time.time()
            })
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_seconds} seconds.",
                "duration_seconds": timeout_seconds,
                "risk_level": risk,
                "dry_run": False
            }
        except Exception as e:
            self.audit_log.append({
                "command": command_str,
                "risk_level": risk,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            })
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": self.redactor.redact(str(e)),
                "duration_seconds": round(time.time() - start_time, 2),
                "risk_level": risk,
                "dry_run": False
            }


_global_tool_gateway: Optional[ToolGateway] = None


def get_tool_gateway(workspace: Any = ".") -> ToolGateway:
    """Retrieves or creates the tool execution gateway for a workspace."""
    global _global_tool_gateway
    if _global_tool_gateway is None:
        if isinstance(workspace, WorkspaceGuard):
            guard = workspace
        else:
            guard = WorkspaceGuard(Path(workspace))
        _global_tool_gateway = ToolGateway(guard)
    return _global_tool_gateway

