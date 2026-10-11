"""
PRUBETH IDE — Centralized Multi-Scope Configuration Service
Pillar 1, 2 & 7: Requirements, Architecture & Operations Governance

Implements deterministic hierarchical configuration precedence:
  1. ORGANIZATION (enforced org/admin policies, immutable by user)
  2. SESSION (in-memory runtime overrides)
  3. WORKSPACE (project-specific .prubeth/settings.json)
  4. USER_PROFILE (named profiles: Low Resource, Development, Secure)
  5. USER (persistent user configuration ~/.local_ai_studio_pro/settings.json)
  6. APPLICATION_DEFAULT (built-in base defaults)

Supports atomic persistence, schema migrations, source-of-value inspection,
extension-owned schema contributions, and typed event propagation.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Callable

from core.event_bus import EventBus, EventChannel, EventSeverity


class ConfigScope:
    ORGANIZATION = "ORGANIZATION"
    SESSION = "SESSION"
    WORKSPACE = "WORKSPACE"
    USER_PROFILE = "USER_PROFILE"
    USER = "USER"
    APPLICATION_DEFAULT = "APPLICATION_DEFAULT"


# Precedence order from highest (overrides all) to lowest
PRECEDENCE_ORDER = [
    ConfigScope.ORGANIZATION,
    ConfigScope.SESSION,
    ConfigScope.WORKSPACE,
    ConfigScope.USER_PROFILE,
    ConfigScope.USER,
    ConfigScope.APPLICATION_DEFAULT,
]


DEFAULT_GLOBAL_CONFIG: Dict[str, Any] = {
    "schema_version": 1,
    "theme": "Dark",
    "accent_color": "#00F0FF",
    "density": "Comfortable",
    "ui_scale": 100,
    "editor_font_family": "Cascadia Code",
    "editor_font_size": 11,
    "editor_tab_size": 4,
    "editor_word_wrap": False,
    "editor_line_numbers": True,
    "terminal_shell": "PowerShell",
    "local_model": "qwen2.5:1.5b",
    "default_model_id": "ollama-qwen",
    "max_parallel_agents": 2,
    "max_agent_steps": 30,
    "cache_mb": 512,
    "cuda_vram_limit_mb": 4096,
    "gguf_gpu_layers": 33,
    "low_memory_mode": False,
    "allow_telemetry": False,
    "allow_crash_reports": False,
    "safe_mode": True,
    "workspace_boundary": True,
    "auto_checkpoint_on_edit": True,
    "fast_diff_engine": True
}


class ConfigurationService:
    """Central configuration platform with hierarchical scope resolution."""

    _instance: Optional[ConfigurationService] = None

    def __init__(self, user_config_path: Optional[Path] = None, workspace_root: Optional[Path] = None):
        self.user_config_path = user_config_path or (Path.home() / ".local_ai_studio_pro" / "settings.json")
        self.workspace_root = Path(workspace_root) if workspace_root else None
        
        # Scoped configuration stores
        self._scopes: Dict[str, Dict[str, Any]] = {
            ConfigScope.ORGANIZATION: {},
            ConfigScope.SESSION: {},
            ConfigScope.WORKSPACE: {},
            ConfigScope.USER_PROFILE: {},
            ConfigScope.USER: {},
            ConfigScope.APPLICATION_DEFAULT: copy.deepcopy(DEFAULT_GLOBAL_CONFIG)
        }
        
        self._extension_schemas: Dict[str, Dict[str, Any]] = {}
        self._load_user_config()
        self._load_workspace_config()

    @classmethod
    def get_instance(cls) -> ConfigurationService:
        if cls._instance is None:
            cls._instance = ConfigurationService()
        return cls._instance

    def set_workspace_root(self, root: Optional[Path]) -> None:
        """Switches active workspace context and reloads project-specific settings."""
        self.workspace_root = Path(root) if root else None
        self._load_workspace_config()
        EventBus.get_instance().publish(
            EventChannel.CONFIG,
            "ConfigurationService",
            {"event": "workspace_switched", "workspace_root": str(root) if root else None}
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves effective value by traversing scopes in documented precedence order."""
        val, _ = self.get_with_source(key, default)
        return val

    def get_with_source(self, key: str, default: Any = None) -> Tuple[Any, str]:
        """Returns (effective_value, source_scope_name) showing where the value originated."""
        for scope in PRECEDENCE_ORDER:
            store = self._scopes[scope]
            if key in store:
                return store[key], scope
        return default, "NOT_SET"

    def set(self, key: str, value: Any, scope: str = ConfigScope.USER) -> None:
        """Sets a value within a specific scope. Enforces organization lock."""
        if scope not in self._scopes:
            raise ValueError(f"Invalid configuration scope: '{scope}'")

        # Organization policies cannot be overridden by user or workspace
        if scope != ConfigScope.ORGANIZATION and key in self._scopes[ConfigScope.ORGANIZATION]:
            raise PermissionError(f"Setting '{key}' is locked by Organization Policy and cannot be overridden.")

        old_val, old_source = self.get_with_source(key)
        self._scopes[scope][key] = value
        new_val, new_source = self.get_with_source(key)

        EventBus.get_instance().publish(
            EventChannel.CONFIG,
            "ConfigurationService",
            {"key": key, "old_value": old_val, "new_value": new_val, "scope": scope, "effective_source": new_source}
        )

    def save(self, scope: str = ConfigScope.USER) -> None:
        """Atomically persists a scope to disk."""
        if scope == ConfigScope.USER:
            self._save_atomic(self.user_config_path, self._scopes[ConfigScope.USER])
        elif scope == ConfigScope.WORKSPACE and self.workspace_root:
            w_path = self.workspace_root / ".prubeth" / "settings.json"
            self._save_atomic(w_path, self._scopes[ConfigScope.WORKSPACE])

    def reset_scope(self, scope: str) -> None:
        """Clears overrides in a specific scope."""
        if scope in self._scopes and scope != ConfigScope.APPLICATION_DEFAULT:
            self._scopes[scope].clear()
            self.save(scope)

    def register_extension_schema(self, extension_id: str, schema: Dict[str, Any], defaults: Dict[str, Any]) -> None:
        """Allows extensions to register their own typed configuration fields dynamically."""
        self._extension_schemas[extension_id] = schema
        for k, v in defaults.items():
            self._scopes[ConfigScope.APPLICATION_DEFAULT][f"{extension_id}.{k}"] = v

    def export_bundle(self) -> Dict[str, Any]:
        """Exports a full configuration snapshot with all scopes and source metadata."""
        return {
            "scopes": copy.deepcopy(self._scopes),
            "precedence": PRECEDENCE_ORDER,
            "timestamp": copy.deepcopy(self._scopes[ConfigScope.USER].get("timestamp"))
        }

    def import_bundle(self, bundle: Dict[str, Any]) -> None:
        """Safely imports user and profile scopes from a configuration bundle."""
        if "scopes" in bundle and isinstance(bundle["scopes"], dict):
            if ConfigScope.USER in bundle["scopes"]:
                self._scopes[ConfigScope.USER] = copy.deepcopy(bundle["scopes"][ConfigScope.USER])
                self.save(ConfigScope.USER)
            if ConfigScope.USER_PROFILE in bundle["scopes"]:
                self._scopes[ConfigScope.USER_PROFILE] = copy.deepcopy(bundle["scopes"][ConfigScope.USER_PROFILE])

    def _load_user_config(self) -> None:
        if not self.user_config_path.exists():
            return
        try:
            data = json.loads(self.user_config_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._scopes[ConfigScope.USER] = data
        except Exception:
            pass

    def _load_workspace_config(self) -> None:
        self._scopes[ConfigScope.WORKSPACE].clear()
        if not self.workspace_root:
            return
        w_path = self.workspace_root / ".prubeth" / "settings.json"
        if w_path.exists():
            try:
                data = json.loads(w_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._scopes[ConfigScope.WORKSPACE] = data
            except Exception:
                pass

    @staticmethod
    def _save_atomic(target_path: Path, data: Dict[str, Any]) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, ensure_ascii=False)
        fd, temp_name = tempfile.mkstemp(prefix="config-", suffix=".tmp", dir=str(target_path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as s:
                s.write(payload)
                s.flush()
                os.fsync(s.fileno())
            os.replace(temp_name, target_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
