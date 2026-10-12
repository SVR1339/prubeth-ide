"""
PRUBETH IDE â€” Extensible Plugin Lifecycle & Marketplace Manager
Discovers, validates manifests, resolves dependencies, and manages the lifecycle
(load, activate, execute, deactivate) of third-party and custom extensions.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from core.workspace import WorkspaceGuard
from plugins.hooks import HookRegistry, HookEvent
from plugins.sandbox import PluginPermission, PluginContext, PluginSandbox, PermissionDeniedError

logger = logging.getLogger("SukhiIDE.Plugins.Manager")


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    entry_point: str = "main.py"
    permissions: List[PluginPermission] = field(default_factory=list)
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)
    root_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "entry_point": self.entry_point,
            "permissions": [p.value for p in self.permissions],
            "enabled": self.enabled,
            "dependencies": list(self.dependencies)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], root_path: Optional[Path] = None) -> "PluginManifest":
        raw_perms = data.get("permissions", [])
        parsed_perms = []
        for p in raw_perms:
            try:
                parsed_perms.append(PluginPermission(p))
            except ValueError:
                pass

        return cls(
            plugin_id=data["plugin_id"],
            name=data.get("name", data["plugin_id"]),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", "Unknown"),
            entry_point=data.get("entry_point", "main.py"),
            permissions=parsed_perms,
            enabled=data.get("enabled", True),
            dependencies=data.get("dependencies", []),
            root_path=root_path
        )


class PluginManager:
    """Manages the lifecycle, discovery, activation, and sandboxing of IDE plugins."""

    def __init__(self, plugins_dir: str, workspace_guard: WorkspaceGuard):
        self.plugins_dir = Path(plugins_dir).resolve()
        self.guard = workspace_guard
        self.hooks = HookRegistry()

        self.manifests: Dict[str, PluginManifest] = {}
        self.active_plugins: Dict[str, Dict[str, Any]] = {}
        self.quarantined_plugins: Dict[str, str] = {}
        self.failed_plugins: Dict[str, str] = {}

    def quarantine_plugin(self, plugin_id: str, reason: str = "Security or stability violation"):
        """Quarantines a plugin and ensures it is deactivated and blocked from execution."""
        self.quarantined_plugins[plugin_id] = reason
        if self.is_active(plugin_id):
            self.deactivate_plugin(plugin_id)
        logger.warning(f"Plugin '{plugin_id}' has been quarantined: {reason}")

    def is_quarantined(self, plugin_id: str) -> bool:
        return plugin_id in self.quarantined_plugins

    def discover_plugins(self) -> List[PluginManifest]:
        """Discovers valid plugin directories containing 'plugin.json' manifests."""
        self.manifests.clear()
        if not self.plugins_dir.exists():
            return []

        for item in self.plugins_dir.iterdir():
            if item.is_dir():
                manifest_file = item / "plugin.json"
                if manifest_file.exists():
                    try:
                        data = json.loads(manifest_file.read_text(encoding="utf-8"))
                        if "plugin_id" in data:
                            manifest = PluginManifest.from_dict(data, root_path=item)
                            self.manifests[manifest.plugin_id] = manifest
                        else:
                            self.quarantine_plugin(item.name, "Missing plugin_id in manifest")
                    except Exception as ex:
                        logger.warning(f"Failed to parse manifest at {manifest_file}: {ex}")
                        self.quarantine_plugin(item.name, f"Malformed manifest JSON: {str(ex)}")

        return list(self.manifests.values())

    def get_manifest(self, plugin_id: str) -> Optional[PluginManifest]:
        return self.manifests.get(plugin_id)

    def is_active(self, plugin_id: str) -> bool:
        return plugin_id in self.active_plugins

    def activate_plugin(self, plugin_id: str) -> bool:
        """Loads and activates a plugin in a restricted sandbox scope."""
        if self.is_quarantined(plugin_id):
            logger.warning(f"Cannot activate quarantined plugin '{plugin_id}'.")
            return False

        if self.is_active(plugin_id):
            return True

        manifest = self.manifests.get(plugin_id)
        if not manifest or not manifest.root_path:
            return False

        # Verify dependencies
        for dep in manifest.dependencies:
            if not self.is_active(dep):
                if dep in self.manifests:
                    if not self.activate_plugin(dep):
                        logger.error(f"Failed to activate dependency '{dep}' for '{plugin_id}'")
                        return False
                else:
                    logger.error(f"Missing dependency '{dep}' for '{plugin_id}'")
                    return False

        entry_file = manifest.root_path / manifest.entry_point
        if not entry_file.exists():
            logger.error(f"Plugin '{plugin_id}' entry point '{manifest.entry_point}' not found.")
            return False

        try:
            code = entry_file.read_text(encoding="utf-8")
            ctx = PluginContext(
                plugin_id=manifest.plugin_id,
                workspace_guard=self.guard,
                granted_permissions=set(manifest.permissions)
            )

            sandbox = PluginSandbox(ctx)
            scope = sandbox.execute_script(code)

            # Check if activate() function is defined
            activate_fn = scope.get("activate")
            if callable(activate_fn):
                activate_fn(ctx, self.hooks)

            self.active_plugins[plugin_id] = {
                "manifest": manifest,
                "context": ctx,
                "scope": scope
            }
            logger.info(f"Plugin '{plugin_id}' successfully activated.")
            return True

        except Exception as ex:
            logger.error(f"Error activating plugin '{plugin_id}': {ex}", exc_info=True)
            self.failed_plugins[plugin_id] = str(ex)
            return False

    def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivates a plugin and cleans up all registered hooks."""
        if not self.is_active(plugin_id):
            return False

        info = self.active_plugins.get(plugin_id)
        if info:
            scope = info.get("scope", {})
            deactivate_fn = scope.get("deactivate")
            if callable(deactivate_fn):
                try:
                    deactivate_fn(info["context"])
                except Exception as ex:
                    logger.warning(f"Error during plugin '{plugin_id}' deactivation: {ex}")

        # Unregister all hooks installed by this plugin
        self.hooks.unregister_plugin(plugin_id)
        self.active_plugins.pop(plugin_id, None)
        logger.info(f"Plugin '{plugin_id}' deactivated.")
        return True

