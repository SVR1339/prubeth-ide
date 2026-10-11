"""
PRUBETH IDE — Automated Test Suite for Adaptive Architecture & Universal Flexibility
Pillars 1, 2, 4, 6 & 7: Requirements, Architecture, Design System, Quality & Operations

Tests:
- Capability Registry (Levels A, B, C query, search, and export)
- Command Registry (Registration, execution, risk-levels, audit history)
- Event Bus (Typed channels, secret redaction, subscriber dispatch)
- Feature Flags (Toggles, maturity, and persistent state)
- Multi-Scope Configuration Service (Hierarchical precedence & Organization lock)
- Provider Adapters & Inference Registry (Ollama, OpenAI-compatible, custom)
- Agent Studio & 10 Templates (FileConflictGuard concurrent write blocking)
- Panel Registry & 6 Layout Presets (Coding, Agent, Debug, Review, Research, Minimal)
- Headless GUI Verification of Command Palette and Developer Tools Console
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

from core.capability_registry import CapabilityRegistry, Capability
from core.command_registry import CommandRegistry, Command, CommandRiskLevel
from core.event_bus import EventBus, EventChannel, EventSeverity
from core.feature_flags import FeatureFlagService, FeatureFlag, FeatureMaturity
from core.configuration_service import ConfigurationService, ConfigScope
from core.provider_adapters import ProviderRegistry, OllamaAdapter, OpenAICompatibleAdapter
from ai.agent_studio import AgentStudio, AgentSpec, FileConflictGuard, FileConflictError
from ui.panel_registry import PanelRegistry

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt5.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)
from ui.command_palette_dialog import CommandPaletteDialog
from ui.developer_tools_dialog import DeveloperToolsDialog


def test_capability_registry_levels_and_query():
    reg = CapabilityRegistry()
    assert len(reg.list_all()) >= 10
    level_a = reg.filter_by_level("A")
    level_b = reg.filter_by_level("B")
    level_c = reg.filter_by_level("C")

    assert len(level_a) >= 4
    assert len(level_b) >= 4
    assert len(level_c) >= 3

    # Test search
    res = reg.search("Composer")
    assert any(c.component_id == "ui.composer" for c in res)

    # Test export
    inv = reg.export_inventory()
    assert inv["total_capabilities"] >= 10
    assert inv["level_a_count"] >= 4


def test_command_registry_execution_and_audit():
    reg = CommandRegistry()
    executed = []

    cmd = Command(
        command_id="test.action",
        title="Test Action",
        category="Test",
        handler=lambda: executed.append(True),
        risk_level=CommandRiskLevel.SAFE_EXECUTION,
        shortcut="Ctrl+T"
    )
    reg.register(cmd)

    assert reg.get("test.action") is not None
    reg.execute("test.action")
    assert len(executed) == 1

    history = reg.get_history()
    assert len(history) >= 1
    assert history[-1].command_id == "test.action"
    assert history[-1].success is True

    # Test unavailable command
    unavail_cmd = Command(
        command_id="test.unavail",
        title="Unavailable Action",
        category="Test",
        handler=lambda: None,
        is_available=lambda: False
    )
    reg.register(unavail_cmd)
    with pytest.raises(PermissionError):
        reg.execute("test.unavail")


def test_event_bus_channels_and_secret_redaction():
    bus = EventBus()
    received = []

    bus.subscribe(EventChannel.MODEL, lambda ev: received.append(ev))

    # Publish event with sensitive keys
    ev = bus.publish(
        EventChannel.MODEL,
        "TestRunner",
        {"prompt": "hello", "api_key": "sk-1234567890abcdef1234567890abcdef", "token": "AIzaSyD1234567890"}
    )

    assert len(received) == 1
    payload = received[0].payload
    assert payload["api_key"] == "[REDACTED_SECRET]"
    assert payload["token"] == "[REDACTED_SECRET]"
    assert payload["prompt"] == "hello"


def test_feature_flags_service_toggles():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Path(tmpdir) / "flags.json"
        svc = FeatureFlagService(storage_path=storage)

        assert svc.is_enabled("preview.composer_v2") is True
        svc.set_enabled("preview.composer_v2", False)
        assert svc.is_enabled("preview.composer_v2") is False

        # Reload from storage
        svc2 = FeatureFlagService(storage_path=storage)
        assert svc2.is_enabled("preview.composer_v2") is False


def test_configuration_service_precedence_and_org_lock():
    with tempfile.TemporaryDirectory() as tmpdir:
        user_cfg = Path(tmpdir) / "user_settings.json"
        workspace_dir = Path(tmpdir) / "workspace"
        workspace_dir.mkdir()

        svc = ConfigurationService(user_config_path=user_cfg, workspace_root=workspace_dir)

        # Default value
        assert svc.get("editor_tab_size") == 4
        assert svc.get_with_source("editor_tab_size")[1] == ConfigScope.APPLICATION_DEFAULT

        # Override in USER scope
        svc.set("editor_tab_size", 2, scope=ConfigScope.USER)
        assert svc.get("editor_tab_size") == 2
        assert svc.get_with_source("editor_tab_size")[1] == ConfigScope.USER

        # Override in WORKSPACE scope (higher precedence than USER)
        svc.set("editor_tab_size", 8, scope=ConfigScope.WORKSPACE)
        assert svc.get("editor_tab_size") == 8
        assert svc.get_with_source("editor_tab_size")[1] == ConfigScope.WORKSPACE

        # Set ORGANIZATION lock (highest precedence)
        svc.set("editor_tab_size", 4, scope=ConfigScope.ORGANIZATION)
        assert svc.get("editor_tab_size") == 4
        assert svc.get_with_source("editor_tab_size")[1] == ConfigScope.ORGANIZATION

        # Attempting to override an Organization locked key raises PermissionError
        with pytest.raises(PermissionError):
            svc.set("editor_tab_size", 2, scope=ConfigScope.USER)


def test_provider_adapters_registry_and_discovery():
    reg = ProviderRegistry()
    adapters = reg.list_adapters()
    assert len(adapters) >= 4

    ollama = reg.get_adapter("ollama")
    assert ollama is not None
    assert ollama.is_local is True

    health = reg.probe_all_health()
    assert "ollama" in health
    assert "lmstudio" in health


def test_agent_studio_templates_and_conflict_guard():
    studio = AgentStudio()
    agents = studio.list_agents()
    assert len(agents) >= 10  # 10 industry standard templates

    planner = studio.get_agent("template.planner")
    assert planner is not None
    assert planner.role == "Planner"

    # Test FileConflictGuard
    guard = studio.conflict_guard
    guard.acquire_lock("agent_1", "src/main.py")
    assert "src/main.py" in guard.get_locked_files()

    # Same agent acquiring same file is allowed
    guard.acquire_lock("agent_1", "src/main.py")

    # Concurrent agent attempting to acquire same file raises FileConflictError
    with pytest.raises(FileConflictError):
        guard.acquire_lock("agent_2", "src/main.py")

    # Release
    guard.release_lock("agent_1", "src/main.py")
    guard.acquire_lock("agent_2", "src/main.py")
    assert guard.get_locked_files()["src/main.py"] == "agent_2"


def test_panel_registry_and_layout_presets():
    reg = PanelRegistry()
    panels = reg.list_panels()
    presets = reg.list_presets()

    assert len(panels) >= 7
    assert len(presets) == 6  # Coding, Agent Workspace, Debugging, Code Review, Research, Minimal

    coding = reg.get_preset("Coding")
    assert coding is not None
    assert "panel.explorer" in coding.visible_panel_ids
    assert coding.active_surface == "editor"

    agent_ws = reg.get_preset("Agent Workspace")
    assert agent_ws is not None
    assert agent_ws.active_surface == "mission_control"


def test_command_palette_and_developer_tools_dialog_headless():
    cmd_reg = CommandRegistry.get_instance()
    cmd_reg.register(Command(
        command_id="dev.test_ping",
        title="Test Ping Action",
        category="Developer",
        handler=lambda: "pong"
    ))

    # Test CommandPaletteDialog
    palette = CommandPaletteDialog(registry=cmd_reg)
    assert palette.command_list.count() > 0

    # Test DeveloperToolsDialog
    dev_tools = DeveloperToolsDialog()
    assert dev_tools.tabs.count() == 5
