"""
Tests for SUKHI IDE Plugin & Extension Host Subsystem:
HookRegistry, PluginSandbox, and PluginManager.
"""
import json
import pytest
from pathlib import Path
from core.workspace import WorkspaceGuard
from plugins.hooks import HookRegistry, HookEvent
from plugins.sandbox import PluginPermission, PluginContext, PluginSandbox, PermissionDeniedError
from plugins.manager import PluginManager, PluginManifest


def test_hook_registry_priority_and_filtering():
    reg = HookRegistry()
    calls = []

    # Register low priority
    reg.register(HookEvent.ON_FILE_SAVE, lambda **kw: calls.append("low"), priority=50, plugin_id="p1")
    # Register high priority
    reg.register(HookEvent.ON_FILE_SAVE, lambda **kw: calls.append("high"), priority=200, plugin_id="p2")

    reg.dispatch(HookEvent.ON_FILE_SAVE)
    assert calls == ["high", "low"]

    # Test waterfall filter
    reg.register(HookEvent.ON_PROMPT_PREPARE, lambda prompt, **kw: f"PREFIX: {prompt}", priority=100)
    reg.register(HookEvent.ON_PROMPT_PREPARE, lambda prompt, **kw: f"{prompt} :SUFFIX", priority=50)

    result = reg.dispatch_filter(HookEvent.ON_PROMPT_PREPARE, "Hello")
    assert result == "PREFIX: Hello :SUFFIX"


def test_plugin_sandbox_permission_enforcement(tmp_path):
    guard = WorkspaceGuard(tmp_path)
    sample_file = tmp_path / "data.txt"
    sample_file.write_text("secure content", encoding="utf-8")

    # 1. Context without write permission
    ctx_readonly = PluginContext(
        plugin_id="reader-plugin",
        workspace_guard=guard,
        granted_permissions={PluginPermission.WORKSPACE_READ}
    )
    assert ctx_readonly.read_file("data.txt") == "secure content"

    # Attempt write -> should raise PermissionDeniedError
    with pytest.raises(PermissionDeniedError):
        ctx_readonly.write_file("new.txt", "unauthorized")

    # 2. Context with write permission
    ctx_writer = PluginContext(
        plugin_id="writer-plugin",
        workspace_guard=guard,
        granted_permissions={PluginPermission.WORKSPACE_READ, PluginPermission.WORKSPACE_WRITE}
    )
    chars = ctx_writer.write_file("new.txt", "authorized write")
    assert chars > 0
    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "authorized write"


def test_plugin_manager_lifecycle_and_dependencies(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    ws_dir = tmp_path / "workspace"
    ws_dir.mkdir()
    guard = WorkspaceGuard(ws_dir)

    # Create Plugin A
    p_a_dir = plugins_dir / "plugin_a"
    p_a_dir.mkdir()
    (p_a_dir / "plugin.json").write_text(json.dumps({
        "plugin_id": "plugin_a",
        "name": "Plugin A",
        "version": "1.0.0",
        "permissions": ["workspace:read"]
    }), encoding="utf-8")
    (p_a_dir / "main.py").write_text("""
def activate(context, hooks):
    context.log("Plugin A loaded")
""", encoding="utf-8")

    # Create Plugin B (depends on Plugin A)
    p_b_dir = plugins_dir / "plugin_b"
    p_b_dir.mkdir()
    (p_b_dir / "plugin.json").write_text(json.dumps({
        "plugin_id": "plugin_b",
        "name": "Plugin B",
        "version": "1.0.0",
        "dependencies": ["plugin_a"],
        "permissions": ["workspace:read", "workspace:write"]
    }), encoding="utf-8")
    (p_b_dir / "main.py").write_text("""
def activate(context, hooks):
    def on_save(file_path="", **kw):
        context.log(f"File saved: {file_path}")
    hooks.register("on_file_save", on_save, plugin_id="plugin_b")

def deactivate(context):
    context.log("Plugin B deactivated")
""", encoding="utf-8")

    manager = PluginManager(str(plugins_dir), guard)
    manifests = manager.discover_plugins()
    assert len(manifests) == 2

    # Activating Plugin B should automatically activate Plugin A as dependency
    ok = manager.activate_plugin("plugin_b")
    assert ok is True
    assert manager.is_active("plugin_a") is True
    assert manager.is_active("plugin_b") is True

    # Test that hook registered by Plugin B executes
    manager.hooks.dispatch(HookEvent.ON_FILE_SAVE, file_path="main.py")
    b_ctx = manager.active_plugins["plugin_b"]["context"]
    assert any("File saved: main.py" in log for log in b_ctx.logs)

    # Deactivating Plugin B removes its hooks
    manager.deactivate_plugin("plugin_b")
    assert manager.is_active("plugin_b") is False
    assert len(manager.hooks._hooks[HookEvent.ON_FILE_SAVE]) == 0
