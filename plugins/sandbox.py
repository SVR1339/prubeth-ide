"""
SUKHI IDE — Sandboxed Plugin Execution Environment
Provides capability-based security boundaries, permission verification,
and restricted execution contexts for external developer extensions.
"""
from enum import Enum
from pathlib import Path
from typing import Set, Dict, Any, Optional, List
from core.workspace import WorkspaceGuard, WorkspaceSecurityError


class PluginPermission(str, Enum):
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_WRITE = "workspace:write"
    NETWORK = "network"
    PROCESS = "process"
    UI_EXTEND = "ui:extend"


class PermissionDeniedError(PermissionError):
    """Raised when a plugin attempts an action without having the required permission."""
    pass


class PluginContext:
    """Safe runtime context provided to sandboxed plugins."""

    def __init__(
        self,
        plugin_id: str,
        workspace_guard: WorkspaceGuard,
        granted_permissions: Set[PluginPermission],
        config: Optional[Dict[str, Any]] = None
    ):
        self.plugin_id = plugin_id
        self.guard = workspace_guard
        self.permissions = set(granted_permissions)
        self.config = config or {}
        self.logs: List[str] = []

    def has_permission(self, perm: PluginPermission) -> bool:
        return perm in self.permissions

    def require_permission(self, perm: PluginPermission):
        if not self.has_permission(perm):
            raise PermissionDeniedError(
                f"Plugin '{self.plugin_id}' lacks required capability: {perm.value}"
            )

    def log(self, message: str):
        entry = f"[{self.plugin_id}] {message}"
        self.logs.append(entry)

    def read_file(self, rel_path: str) -> str:
        self.require_permission(PluginPermission.WORKSPACE_READ)
        return self.guard.safe_read(rel_path)

    def write_file(self, rel_path: str, content: str) -> int:
        self.require_permission(PluginPermission.WORKSPACE_WRITE)
        return self.guard.safe_write(rel_path, content)


class PluginSandbox:
    """Executes plugin scripts within a controlled scope and restricted built-in environment."""

    SAFE_BUILTINS = {
        "abs": abs,
        "all": all,
        "any": any,
        "bin": bin,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "format": format,
        "int": int,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "iter": iter,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "next": next,
        "print": print,
        "range": range,
        "round": round,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        "True": True,
        "False": False,
        "None": None,
    }

    def __init__(self, context: PluginContext):
        self.context = context

    def execute_script(self, code: str, extra_globals: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes Python code with restricted builtins and injected plugin context."""
        scope = {
            "__builtins__": dict(self.SAFE_BUILTINS),
            "context": self.context,
            "PluginPermission": PluginPermission,
        }
        if extra_globals:
            scope.update(extra_globals)

        exec(code, scope)
        return scope
