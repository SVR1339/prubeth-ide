"""
SO NAIVE IDE — Workspace Security & Filesystem Boundary Guard
Provides canonical path resolution, symlink boundary validation,
directory traversal rejection, and atomic safe file operations.
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

IGNORE_DIRS: Set[str] = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    "dist", "build", ".idea", ".pytest_cache", ".local_ai_studio_pro"
}

TEXT_EXTENSIONS: Set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json",
    ".md", ".txt", ".rs", ".go", ".c", ".cpp", ".h", ".hpp",
    ".yaml", ".yml", ".toml", ".ini", ".sql", ".sh", ".bat", ".ps1"
}


class WorkspaceSecurityError(PermissionError):
    """Raised when an operation attempts to escape the active workspace boundary."""
    pass


class QuotaExceededError(WorkspaceSecurityError):
    """Raised when an operation exceeds workspace disk quota or file size limits."""
    pass


class WorkspaceGuard:
    """Enforces strict filesystem sandbox boundaries and storage quotas for AI tools and extensions."""

    def __init__(
        self,
        workspace_root: Path,
        max_workspace_bytes: Optional[int] = None,
        max_file_size_bytes: Optional[int] = None
    ):
        self.root = Path(workspace_root).resolve()
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)
        self.max_workspace_bytes = max_workspace_bytes
        self.max_file_size_bytes = max_file_size_bytes

    RESERVED_DEVICE_NAMES: Set[str] = {
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9"
    }

    def canonicalize(self, rel_or_abs_path: str) -> Path:
        """Resolves path and guarantees it resides strictly inside the workspace root."""
        if not rel_or_abs_path:
            return self.root

        # Reject null byte injection
        if "\0" in rel_or_abs_path:
            raise WorkspaceSecurityError(f"Access Denied: Null bytes are not permitted in path.")

        p = Path(rel_or_abs_path)

        # Reject Windows reserved device names
        if p.stem.upper() in self.RESERVED_DEVICE_NAMES:
            raise WorkspaceSecurityError(
                f"Access Denied: Path '{rel_or_abs_path}' targets reserved device name '{p.name}'."
            )

        if not p.is_absolute():
            resolved = (self.root / p).resolve()
        else:
            resolved = p.resolve()

        # Boundary check
        try:
            # Python 3.9+ Path.is_relative_to
            if not resolved.is_relative_to(self.root):
                raise WorkspaceSecurityError(
                    f"Access Denied: Path '{rel_or_abs_path}' resolves to '{resolved}', "
                    f"which escapes workspace root '{self.root}'."
                )
        except AttributeError:
            # Fallback for older python
            try:
                resolved.relative_to(self.root)
            except ValueError:
                raise WorkspaceSecurityError(
                    f"Access Denied: Path '{rel_or_abs_path}' escapes workspace root '{self.root}'."
                )

        return resolved

    def safe_read(self, rel_or_abs_path: str, max_chars: int = 120000) -> str:
        target = self.canonicalize(rel_or_abs_path)
        if not target.is_file():
            raise FileNotFoundError(f"File not found: '{rel_or_abs_path}'")
        return target.read_text(encoding="utf-8", errors="replace")[:max_chars]

    def get_workspace_size_bytes(self) -> int:
        """Calculates total size in bytes of files in the workspace (excluding ignored dirs)."""
        total = 0
        for current_root, dirs, files in os.walk(str(self.root)):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for name in files:
                fp = Path(current_root) / name
                try:
                    total += fp.stat().st_size
                except (OSError, FileNotFoundError):
                    pass
        return total

    def check_quota(self, additional_bytes: int = 0) -> None:
        """Verifies that adding additional_bytes will not exceed the workspace quota."""
        if self.max_file_size_bytes is not None and additional_bytes > self.max_file_size_bytes:
            raise QuotaExceededError(
                f"File size limit exceeded: Operation requires {additional_bytes} bytes, "
                f"maximum allowed per file is {self.max_file_size_bytes} bytes."
            )
        if self.max_workspace_bytes is not None:
            current = self.get_workspace_size_bytes()
            if current + additional_bytes > self.max_workspace_bytes:
                raise QuotaExceededError(
                    f"Workspace storage quota exceeded: Current usage is {current} bytes, "
                    f"adding {additional_bytes} bytes would exceed maximum limit of {self.max_workspace_bytes} bytes."
                )

    def safe_write(self, rel_or_abs_path: str, content: str, backup: bool = True) -> int:
        target = self.canonicalize(rel_or_abs_path)
        content_bytes_len = len(content.encode("utf-8"))

        # Enforce quota limits
        self.check_quota(additional_bytes=content_bytes_len)

        target.parent.mkdir(parents=True, exist_ok=True)

        if backup and target.exists() and target.is_file():
            bak_path = target.with_suffix(target.suffix + ".bak")
            shutil.copy2(target, bak_path)

        # Atomic write via temporary file
        temp_file = target.with_suffix(target.suffix + ".tmp_write")
        temp_file.write_text(content, encoding="utf-8")
        try:
            temp_file.replace(target)
        except OSError:
            if target.exists():
                try:
                    target.unlink()
                except Exception:
                    pass
            temp_file.rename(target)
        return len(content)

    def safe_patch(self, rel_or_abs_path: str, search: str, replace: str) -> bool:
        target = self.canonicalize(rel_or_abs_path)
        if not target.is_file():
            raise FileNotFoundError(f"Target file for patch not found: '{rel_or_abs_path}'")

        source = target.read_text(encoding="utf-8")
        if search not in source:
            return False

        bak_path = target.with_suffix(target.suffix + ".bak")
        shutil.copy2(target, bak_path)

        updated = source.replace(search, replace, 1)
        target.write_text(updated, encoding="utf-8")
        return True

    def safe_list_dir(self, rel_or_abs_path: str = ".") -> List[Dict[str, Any]]:
        target_dir = self.canonicalize(rel_or_abs_path)
        if not target_dir.is_dir():
            raise NotADirectoryError(f"Directory not found: '{rel_or_abs_path}'")

        entries = []
        for item in sorted(target_dir.iterdir()):
            if item.name in IGNORE_DIRS:
                continue
            entries.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "relative_path": str(item.relative_to(self.root)),
                "size_bytes": item.stat().st_size if item.is_file() else 0
            })
        return entries

    def safe_search_code(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        if not query:
            return []
        term = query.lower()
        results = []

        for current_root, dirs, files in os.walk(str(self.root)):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for name in files:
                fp = Path(current_root) / name
                if fp.suffix.lower() in TEXT_EXTENSIONS:
                    try:
                        lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
                        for i, line in enumerate(lines, 1):
                            if term in line.lower():
                                results.append({
                                    "file": str(fp.relative_to(self.root)),
                                    "line_number": i,
                                    "snippet": line.strip()[:180]
                                })
                                if len(results) >= max_results:
                                    return results
                    except Exception:
                        pass
        return results
