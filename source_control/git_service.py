"""
SUKHI IDE — Git Version Control Service Engine
Encapsulates Git CLI execution with explicit argument lists, sanitized paths,
porcelain status parsing, and robust error handling.
"""
import os
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class GitFileChange:
    status_code: str  # 'M', 'A', 'D', 'R', '?', 'U'
    file_path: str
    is_staged: bool = False


@dataclass
class GitStatus:
    branch: str = "main"
    is_repo: bool = False
    is_clean: bool = True
    staged: List[GitFileChange] = field(default_factory=list)
    unstaged: List[GitFileChange] = field(default_factory=list)
    untracked: List[str] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0


class GitService:
    """Manages Git operations inside a designated workspace."""

    def __init__(self, workspace_root: Path):
        self.root = Path(workspace_root).resolve()
        self.git_bin = shutil.which("git") or "git"

    def _run_git(self, args: List[str], timeout_seconds: int = 30) -> subprocess.CompletedProcess:
        """Runs git command with explicit argument lists and captured output."""
        cmd = [self.git_bin] + args
        try:
            return subprocess.run(
                cmd,
                cwd=str(self.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                shell=False
            )
        except Exception as e:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-1,
                stdout="",
                stderr=str(e)
            )

    def is_git_repo(self) -> bool:
        res = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return res.returncode == 0 and res.stdout.strip() == "true"

    def get_current_branch(self) -> str:
        if not self.is_git_repo():
            return ""
        res = self._run_git(["branch", "--show-current"])
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
        # Fallback to symbolic ref or commit
        res = self._run_git(["rev-parse", "--short", "HEAD"])
        return res.stdout.strip() if res.returncode == 0 else "HEAD (detached)"

    def get_status(self) -> GitStatus:
        if not self.is_git_repo():
            return GitStatus(is_repo=False)

        branch = self.get_current_branch()
        res = self._run_git(["status", "--porcelain=v1", "-b"])
        if res.returncode != 0:
            return GitStatus(branch=branch, is_repo=True)

        lines = res.stdout.splitlines()
        staged = []
        unstaged = []
        untracked = []

        for line in lines:
            if line.startswith("##"):
                continue
            if len(line) < 3:
                continue

            index_status = line[0]
            worktree_status = line[1]
            file_path = line[3:].strip()

            if line.startswith("??"):
                untracked.append(file_path)
                continue

            if index_status not in (" ", "?"):
                staged.append(GitFileChange(status_code=index_status, file_path=file_path, is_staged=True))

            if worktree_status not in (" ", "?"):
                unstaged.append(GitFileChange(status_code=worktree_status, file_path=file_path, is_staged=False))

        is_clean = len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0

        return GitStatus(
            branch=branch,
            is_repo=True,
            is_clean=is_clean,
            staged=staged,
            unstaged=unstaged,
            untracked=untracked
        )

    def get_diff(self, staged: bool = False, file_path: Optional[str] = None) -> str:
        args = ["diff"]
        if staged:
            args.append("--cached")
        if file_path:
            args.extend(["--", file_path])
        res = self._run_git(args)
        return res.stdout if res.returncode == 0 else ""

    def stage_file(self, file_path: str) -> bool:
        res = self._run_git(["add", "--", file_path])
        return res.returncode == 0

    def stage_all(self) -> bool:
        res = self._run_git(["add", "-A"])
        return res.returncode == 0

    def unstage_file(self, file_path: str) -> bool:
        res = self._run_git(["restore", "--staged", "--", file_path])
        return res.returncode == 0

    def discard_changes(self, file_path: str) -> bool:
        res = self._run_git(["restore", "--", file_path])
        return res.returncode == 0

    def commit(self, message: str) -> Dict[str, Any]:
        msg = (message or "").strip()
        if not msg:
            return {"success": False, "error": "Commit message cannot be empty."}

        res = self._run_git(["commit", "-m", msg])
        if res.returncode == 0:
            return {"success": True, "output": res.stdout.strip()}
        return {"success": False, "error": res.stderr.strip() or res.stdout.strip()}

    def list_branches(self) -> List[str]:
        res = self._run_git(["branch", "--list"])
        if res.returncode != 0:
            return []
        branches = []
        for line in res.stdout.splitlines():
            clean = line.strip().lstrip("* ").strip()
            if clean:
                branches.append(clean)
        return branches

    def get_log(self, max_count: int = 10) -> List[Dict[str, str]]:
        res = self._run_git(["log", f"-n{max_count}", "--pretty=format:%H|%an|%ad|%s"])
        if res.returncode != 0:
            return []
        commits = []
        for line in res.stdout.splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "commit_hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })
        return commits
