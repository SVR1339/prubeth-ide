"""
SUKHI IDE — Plugins & Extension Host Subsystem
Provides lifecycle management, sandboxed execution, permission gating, and hook dispatching.
"""
from plugins.hooks import HookEvent, HookRegistration, HookRegistry
from plugins.sandbox import PluginPermission, PluginContext, PluginSandbox, PermissionDeniedError
from plugins.manager import PluginManifest, PluginManager

__all__ = [
    "HookEvent",
    "HookRegistration",
    "HookRegistry",
    "PluginPermission",
    "PluginContext",
    "PluginSandbox",
    "PermissionDeniedError",
    "PluginManifest",
    "PluginManager"
]
