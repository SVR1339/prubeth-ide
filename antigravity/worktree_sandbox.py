"""
PRUBETH IDE — Antigravity Multi-Tenant Sandbox & Git Worktree Isolation
Provides Zero-Interference Execution:
Each long-running subagent operates within an isolated Git worktree or shadow staging directory.
Subagents can install temporary dependencies, run destructive commands, and execute unit tests
without affecting the developer's working directory or creating file locks.
Once verification passes, the sandbox generates a clean unified diff/PR for review.
"""
import os
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class SandboxSession:
    """Represents an active isolated subagent sandbox session."""
    task_id: str
    sandbox_path: Path
    branch_name: str
    is_git_worktree: bool
    created_at: float
    base_commit: Optional[str] = None


class WorktreeSandboxManager:
    """Manages isolated Git worktrees and shadow directory sandboxes."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()
        self.sandboxes_root = self.workspace_root / ".antigravity" / "sandboxes"
        self.sandboxes_root.mkdir(parents=True, exist_ok=True)
        self.active_sandboxes: Dict[str, SandboxSession] = {}

    def _is_git_repo(self) -> bool:
        """Checks if the workspace is a valid Git repository."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=str(self.workspace_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            return res.returncode == 0 and "true" in res.stdout.lower()
        except Exception:
            return False

    def create_sandbox(self, task_id: str, base_ref: str = "HEAD") -> SandboxSession:
        """
        Creates an isolated sandbox for a subagent.
        Uses `git worktree` when possible; falls back to an isolated shadow copy.
        """
        sandbox_path = self.sandboxes_root / task_id
        if sandbox_path.exists():
            self.cleanup_sandbox(task_id)

        branch_name = f"shadow/{task_id}"
        is_git = self._is_git_repo()

        if is_git:
            try:
                # 1. Clean any dangling branch with the same name
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=str(self.workspace_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False
                )
                # 2. Spawn git worktree with isolated shadow branch
                res = subprocess.run(
                    ["git", "worktree", "add", "-b", branch_name, str(sandbox_path), base_ref],
                    cwd=str(self.workspace_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                if res.returncode == 0 and sandbox_path.exists():
                    session = SandboxSession(
                        task_id=task_id,
                        sandbox_path=sandbox_path,
                        branch_name=branch_name,
                        is_git_worktree=True,
                        created_at=os.path.getctime(str(sandbox_path))
                    )
                    self.active_sandboxes[task_id] = session
                    return session
            except Exception:
                pass

        # Fallback: Copy workspace into isolated shadow staging directory
        sandbox_path.mkdir(parents=True, exist_ok=True)
        ignore_patterns = shutil.ignore_patterns(".git", ".antigravity", ".venv", "venv", "__pycache__", "node_modules")

        for item in self.workspace_root.iterdir():
            if item.name in {".git", ".antigravity", ".venv", "venv", "__pycache__", "node_modules"}:
                continue
            dest = sandbox_path / item.name
            try:
                if item.is_dir():
                    shutil.copytree(str(item), str(dest), ignore=ignore_patterns)
                else:
                    shutil.copy2(str(item), str(dest))
            except Exception:
                pass

        session = SandboxSession(
            task_id=task_id,
            sandbox_path=sandbox_path,
            branch_name=branch_name,
            is_git_worktree=False,
            created_at=os.path.getctime(str(sandbox_path))
        )
        self.active_sandboxes[task_id] = session
        return session

    def run_command(self, task_id: str, command: List[str], timeout: int = 60) -> Dict[str, Any]:
        """Runs a command (e.g. pytest, npm test, compiler) inside the isolated sandbox."""
        session = self.active_sandboxes.get(task_id)
        if not session or not session.sandbox_path.exists():
            raise KeyError(f"No active sandbox found for task '{task_id}'")

        try:
            res = subprocess.run(
                command,
                cwd=str(session.sandbox_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "success": res.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "success": False
            }
        except Exception as ex:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(ex),
                "success": False
            }

    def generate_diff(self, task_id: str) -> str:
        """Generates unified diff of all sandbox modifications relative to base."""
        session = self.active_sandboxes.get(task_id)
        if not session or not session.sandbox_path.exists():
            return ""

        if session.is_git_worktree:
            try:
                # Stage all changes in worktree to get complete diff
                subprocess.run(["git", "add", "-A"], cwd=str(session.sandbox_path), check=False)
                res = subprocess.run(
                    ["git", "diff", "HEAD"],
                    cwd=str(session.sandbox_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                return res.stdout
            except Exception:
                pass

        # Fallback diff generation for directory-based sandbox
        import difflib
        diff_lines = []
        for root, _, files in os.walk(session.sandbox_path):
            for f in files:
                rel = Path(root).relative_to(session.sandbox_path) / f
                src_file = self.workspace_root / rel
                sbx_file = session.sandbox_path / rel

                src_lines = src_file.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True) if src_file.exists() else []
                sbx_lines = sbx_file.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True) if sbx_file.exists() else []

                if src_lines != sbx_lines:
                    file_diff = difflib.unified_diff(
                        src_lines, sbx_lines,
                        fromfile=f"a/{rel.as_posix()}",
                        tofile=f"b/{rel.as_posix()}"
                    )
                    diff_lines.extend(file_diff)

        return "".join(diff_lines)

    def cleanup_sandbox(self, task_id: str):
        """Safely removes the isolated worktree or shadow staging directory."""
        session = self.active_sandboxes.pop(task_id, None)
        path = self.sandboxes_root / task_id

        if session and session.is_git_worktree:
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(path)],
                    cwd=str(self.workspace_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False
                )
                subprocess.run(
                    ["git", "branch", "-D", session.branch_name],
                    cwd=str(self.workspace_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False
                )
                subprocess.run(
                    ["git", "worktree", "prune"],
                    cwd=str(self.workspace_root),
                    check=False
                )
            except Exception:
                pass

        if path.exists():
            shutil.rmtree(str(path), ignore_errors=True)
