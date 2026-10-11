"""
SUKHI IDE — Gate 11 Automated Test Suite
Verifies Plugin Host & Sandboxed Execution Environment:
- Manifest discovery and permission resolution
- Automatic quarantine of malformed manifests without host disruption
- Sandbox containment: prohibited builtins (open, eval, __import__) are inaccessible
- Permission-based capability gating (workspace:read vs workspace:write)
- Complete plugin lifecycle (discover -> activate -> hook execution -> deactivate -> cleanup)
- Quarantine enforcement preventing activation of dangerous plugins
"""
import pytest
import json
from pathlib import Path
import tempfile
import shutil

from core.workspace import WorkspaceGuard
from plugins.manager import PluginManager, PluginManifest
from plugins.sandbox import PluginPermission, PermissionDeniedError
from plugins.hooks import HookEvent


def test_plugin_discovery_and_manifest_parsing():
    """PluginManager must discover and correctly parse valid extension manifests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_plugins_test_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        plugins_dir = temp_dir / "extensions"
        plugins_dir.mkdir()

        p1_dir = plugins_dir / "my_linter"
        p1_dir.mkdir()
        (p1_dir / "plugin.json").write_text(json.dumps({
            "plugin_id": "com.sukhi.linter",
            "name": "Python Linter Extension",
            "version": "1.2.0",
            "description": "Fast code linter",
            "author": "Sukhi Dev",
            "entry_point": "main.py",
            "permissions": ["workspace:read"]
        }), encoding="utf-8")
        (p1_dir / "main.py").write_text("def activate(ctx, hooks):\n    pass\n", encoding="utf-8")

        mgr = PluginManager(str(plugins_dir), workspace_guard=guard)
        discovered = mgr.discover_plugins()

        assert len(discovered) == 1
        manifest = discovered[0]
        assert manifest.plugin_id == "com.sukhi.linter"
        assert manifest.name == "Python Linter Extension"
        assert PluginPermission.WORKSPACE_READ in manifest.permissions
        assert PluginPermission.WORKSPACE_WRITE not in manifest.permissions

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_malformed_plugin_quarantine_containment():
    """Corrupted manifests or missing IDs must be automatically quarantined without crashing host."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_plugins_malformed_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        plugins_dir = temp_dir / "extensions"
        plugins_dir.mkdir()

        # 1. Valid plugin
        p_valid = plugins_dir / "valid_ext"
        p_valid.mkdir()
        (p_valid / "plugin.json").write_text(json.dumps({
            "plugin_id": "valid.ext", "name": "Valid"
        }), encoding="utf-8")

        # 2. Corrupt JSON syntax
        p_corrupt = plugins_dir / "broken_json"
        p_corrupt.mkdir()
        (p_corrupt / "plugin.json").write_text("{ this is not json }", encoding="utf-8")

        # 3. Missing plugin_id
        p_noid = plugins_dir / "missing_id"
        p_noid.mkdir()
        (p_noid / "plugin.json").write_text(json.dumps({"name": "No ID"}), encoding="utf-8")

        mgr = PluginManager(str(plugins_dir), workspace_guard=guard)
        discovered = mgr.discover_plugins()

        # Only the valid plugin is loaded into active manifests
        assert len(discovered) == 1
        assert discovered[0].plugin_id == "valid.ext"

        # The malformed extensions are quarantined safely
        assert "broken_json" in mgr.quarantined_plugins
        assert "missing_id" in mgr.quarantined_plugins

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_sandbox_builtins_isolation():
    """Untrusted plugin script cannot access dangerous builtins like eval, __import__, or open."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_sandbox_iso_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        plugins_dir = temp_dir / "extensions"
        plugins_dir.mkdir()

        p_dir = plugins_dir / "evil_probe"
        p_dir.mkdir()
        (p_dir / "plugin.json").write_text(json.dumps({
            "plugin_id": "evil.probe",
            "name": "Probe",
            "entry_point": "probe.py"
        }), encoding="utf-8")

        # Script trying to invoke eval or __import__
        (p_dir / "probe.py").write_text("""
def activate(ctx, hooks):
    # Try accessing forbidden builtin
    x = eval("1 + 1")
""", encoding="utf-8")

        mgr = PluginManager(str(plugins_dir), workspace_guard=guard)
        mgr.discover_plugins()
        success = mgr.activate_plugin("evil.probe")

        # Must fail because eval is not in SAFE_BUILTINS
        assert success is False
        assert "evil.probe" in mgr.failed_plugins
        assert "name 'eval' is not defined" in mgr.failed_plugins["evil.probe"]

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_permission_denied_enforcement():
    """Plugin without WORKSPACE_WRITE permission cannot write files through context."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_sandbox_perm_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        plugins_dir = temp_dir / "extensions"
        plugins_dir.mkdir()

        p_dir = plugins_dir / "reader_only"
        p_dir.mkdir()
        (p_dir / "plugin.json").write_text(json.dumps({
            "plugin_id": "reader.only",
            "name": "Reader Only",
            "entry_point": "main.py",
            "permissions": ["workspace:read"]
        }), encoding="utf-8")

        (p_dir / "main.py").write_text("""
def activate(ctx, hooks):
    # Attempt unauthorized write
    ctx.write_file("unauthorized.txt", "hello")
""", encoding="utf-8")

        mgr = PluginManager(str(plugins_dir), workspace_guard=guard)
        mgr.discover_plugins()
        success = mgr.activate_plugin("reader.only")

        assert success is False
        assert "reader.only" in mgr.failed_plugins
        assert "lacks required capability: workspace:write" in mgr.failed_plugins["reader.only"]

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_plugin_lifecycle_and_hook_cleanup():
    """Full lifecycle: activate, trigger registered hook, deactivate, and verify hook removal."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_lifecycle_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        plugins_dir = temp_dir / "extensions"
        plugins_dir.mkdir()

        p_dir = plugins_dir / "formatter"
        p_dir.mkdir()
        (p_dir / "plugin.json").write_text(json.dumps({
            "plugin_id": "code.formatter",
            "name": "Formatter",
            "entry_point": "main.py"
        }), encoding="utf-8")

        (p_dir / "main.py").write_text("""
def on_file_save(payload):
    payload["formatted"] = True

def activate(ctx, hooks):
    hooks.register_hook("code.formatter", "file:save", on_file_save)

def deactivate(ctx):
    pass
""", encoding="utf-8")

        mgr = PluginManager(str(plugins_dir), workspace_guard=guard)
        mgr.discover_plugins()

        assert mgr.activate_plugin("code.formatter") is True
        assert mgr.is_active("code.formatter") is True

        # Trigger registered hook
        event_data = {"filename": "test.py"}
        mgr.hooks.trigger_hook("file:save", event_data)
        assert event_data.get("formatted") is True

        # Deactivate plugin
        assert mgr.deactivate_plugin("code.formatter") is True
        assert mgr.is_active("code.formatter") is False

        # Trigger hook again; should have no effect since hook was unregistered
        event_data_2 = {"filename": "test2.py"}
        mgr.hooks.trigger_hook("file:save", event_data_2)
        assert "formatted" not in event_data_2

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_quarantine_blocks_activation():
    """Quarantining a plugin must deactivate it and block future activations."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_quarantine_block_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        plugins_dir = temp_dir / "extensions"
        plugins_dir.mkdir()

        p_dir = plugins_dir / "simple_ext"
        p_dir.mkdir()
        (p_dir / "plugin.json").write_text(json.dumps({
            "plugin_id": "simple.ext",
            "name": "Simple"
        }), encoding="utf-8")
        (p_dir / "main.py").write_text("def activate(ctx, hooks): pass", encoding="utf-8")

        mgr = PluginManager(str(plugins_dir), workspace_guard=guard)
        mgr.discover_plugins()

        mgr.quarantine_plugin("simple.ext", "Suspicious behavior detected")
        assert mgr.is_quarantined("simple.ext") is True

        # Activation attempt should fail
        assert mgr.activate_plugin("simple.ext") is False
        assert mgr.is_active("simple.ext") is False

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
