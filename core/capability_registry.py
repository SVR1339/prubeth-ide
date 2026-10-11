"""
PRUBETH IDE — Universal Capability Registry
Pillar 1 & 2: Requirements Governance & Architecture Specification

Maintains a live, queryable registry of all user-facing components, internal subsystems,
flexibility levels (Level A: Everyday, Level B: Advanced, Level C: Developer/Operator),
and permission constraints across the entire application runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class Capability:
    """Represents a discovered or registered capability within the IDE."""
    component_id: str
    name: str
    category: str  # editor, ai, layout, terminal, workspace, settings, security, diagnostics
    flexibility_level: str  # "A" (Everyday), "B" (Advanced), "C" (Developer/Operator)
    implementation_location: str
    status: str  # "implemented", "partial", "preview", "experimental"
    description: str
    configurable: bool = True
    permission_required: str = "none"  # "none", "workspace_write", "shell_execution", "admin"
    commands: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CapabilityRegistry:
    """Central registry providing runtime capability discovery, inspection, and filtering."""

    _instance: Optional[CapabilityRegistry] = None

    def __init__(self):
        self._capabilities: Dict[str, Capability] = {}
        self._register_default_capabilities()

    @classmethod
    def get_instance(cls) -> CapabilityRegistry:
        if cls._instance is None:
            cls._instance = CapabilityRegistry()
        return cls._instance

    def register(self, cap: Capability) -> None:
        """Registers or updates a capability in the runtime catalog."""
        self._capabilities[cap.component_id] = cap

    def get(self, component_id: str) -> Optional[Capability]:
        return self._capabilities.get(component_id)

    def list_all(self) -> List[Capability]:
        return list(self._capabilities.values())

    def filter_by_level(self, level: str) -> List[Capability]:
        lvl = level.upper().strip()
        return [c for c in self._capabilities.values() if c.flexibility_level == lvl]

    def filter_by_category(self, category: str) -> List[Capability]:
        cat = category.lower().strip()
        return [c for c in self._capabilities.values() if c.category.lower() == cat]

    def search(self, query: str) -> List[Capability]:
        q = query.lower().strip()
        if not q:
            return self.list_all()
        return [
            c for c in self._capabilities.values()
            if q in c.component_id.lower() or q in c.name.lower() or q in c.description.lower() or q in c.category.lower()
        ]

    def export_inventory(self) -> Dict[str, Any]:
        """Produces a structured capability inventory dictionary for inspection and reporting."""
        caps = self.list_all()
        return {
            "total_capabilities": len(caps),
            "level_a_count": len([c for c in caps if c.flexibility_level == "A"]),
            "level_b_count": len([c for c in caps if c.flexibility_level == "B"]),
            "level_c_count": len([c for c in caps if c.flexibility_level == "C"]),
            "capabilities": [asdict(c) for c in caps]
        }

    def _register_default_capabilities(self) -> None:
        # Level A: Everyday Customization
        self.register(Capability(
            component_id="ui.editor",
            name="Code Editor & Monaco Bridge",
            category="editor",
            flexibility_level="A",
            implementation_location="code_oss/monaco/bridge.py",
            status="implemented",
            description="Multi-tab editor with Cascadia Code, line numbers, word wrap, and syntax highlighting.",
            commands=["editor.toggle_word_wrap", "editor.zoom_in", "editor.zoom_out"]
        ))
        self.register(Capability(
            component_id="ui.theme",
            name="Theme & Design System",
            category="layout",
            flexibility_level="A",
            implementation_location="ui/design_system.py",
            status="implemented",
            description="Obsidian Slate theme with Electric Cyan accents, dark canvas, and typography scales.",
            commands=["theme.toggle_dark_light", "theme.set_cyan_accent"]
        ))
        self.register(Capability(
            component_id="ui.composer",
            name="Multi-File Composer Dock",
            category="ai",
            flexibility_level="A",
            implementation_location="ui/composer_widget.py",
            status="implemented",
            description="Cursor/Windsurf-style multi-file diff authoring and atomic application.",
            commands=["composer.open", "composer.apply_diff", "composer.rollback"]
        ))
        self.register(Capability(
            component_id="ui.mission_control",
            name="Mission Control Surface",
            category="ai",
            flexibility_level="A",
            implementation_location="ui/mission_control_widget.py",
            status="implemented",
            description="Asynchronous workspace managing background subagents, ReAct stream, and mid-flight steering.",
            commands=["mission_control.toggle", "mission_control.steer_agent"]
        ))
        self.register(Capability(
            component_id="ui.settings_center",
            name="14-Category Settings Center",
            category="settings",
            flexibility_level="A",
            implementation_location="ui/settings_center.py",
            status="implemented",
            description="Searchable settings for appearance, editor, terminal, models, agents, and privacy.",
            commands=["settings.open", "settings.reset_defaults"]
        ))

        # Level B: Advanced Configuration
        self.register(Capability(
            component_id="engine.hardware_autotuner",
            name="Universal Hardware Auto-Tuner",
            category="settings",
            flexibility_level="B",
            implementation_location="horizon_engine/hardware_autotuner.py",
            status="implemented",
            description="Profiles CPU, RAM, battery, and NVIDIA CUDA VRAM; synthesizes GPU offload layers.",
            commands=["hardware.autotune", "hardware.inspect_profile"]
        ))
        self.register(Capability(
            component_id="engine.connector_gateway",
            name="Universal Connector Gateway",
            category="ai",
            flexibility_level="B",
            implementation_location="horizon_engine/connector_gateway.py",
            status="implemented",
            description="Live probing of local AI runtimes (Ollama, LM Studio, vLLM) and developer toolchains.",
            commands=["connector.scan_services", "connector.probe_port"]
        ))
        self.register(Capability(
            component_id="engine.stage_gate",
            name="PRINCE2 Stage-Gate Controller",
            category="ai",
            flexibility_level="B",
            implementation_location="horizon_engine/stage_gate.py",
            status="implemented",
            description="State machine enforcing Initiation, Gate Review, Execution, and Acceptance with ReAct logs.",
            commands=["stage_gate.advance", "stage_gate.inject_feedback"]
        ))
        self.register(Capability(
            component_id="engine.worktree_sandbox",
            name="Zero-Interference Worktree Sandbox",
            category="workspace",
            flexibility_level="B",
            implementation_location="horizon_engine/worktree_sandbox.py",
            status="implemented",
            description="Isolates agent code mutations into shadow Git worktrees without disturbing main working tree.",
            permission_required="workspace_write",
            commands=["sandbox.create_worktree", "sandbox.merge_shadow"]
        ))
        self.register(Capability(
            component_id="engine.browser_verifier",
            name="Headless Browser Verification Runner",
            category="ai",
            flexibility_level="B",
            implementation_location="horizon_engine/browser_verifier.py",
            status="implemented",
            description="Executes headless web verification inspecting DOM selectors, console JS errors, and screenshots.",
            commands=["browser.verify_url"]
        ))

        # Level C: Developer & Operator Controls
        self.register(Capability(
            component_id="dev.command_registry",
            name="Centralized Command Registry",
            category="diagnostics",
            flexibility_level="C",
            implementation_location="core/command_registry.py",
            status="implemented",
            description="Global directory of executable actions, shortcuts, audit metadata, and risk levels.",
            commands=["commands.open_palette", "commands.export_catalog"]
        ))
        self.register(Capability(
            component_id="dev.event_bus",
            name="Application Event Bus & Audit Log",
            category="diagnostics",
            flexibility_level="C",
            implementation_location="core/event_bus.py",
            status="implemented",
            description="Structured event stream with secret redaction, channel subscription, and bounded history.",
            commands=["events.view_stream", "events.clear_history"]
        ))
        self.register(Capability(
            component_id="dev.security_center",
            name="Security Gateway & DPAPI Credential Store",
            category="security",
            flexibility_level="C",
            implementation_location="core/tool_gateway.py",
            status="implemented",
            description="Redacts secrets, classifies command risk levels, and enforces DPAPI OS keyring encryption.",
            permission_required="admin",
            commands=["security.inspect_audit_log", "security.verify_dpapi"]
        ))
        self.register(Capability(
            component_id="dev.state_inspector",
            name="Live Application State Inspector",
            category="diagnostics",
            flexibility_level="C",
            implementation_location="core/health_monitor.py",
            status="implemented",
            description="Inspects active workspaces, loaded extensions, resource pressure, and diagnostic bundles.",
            commands=["dev.export_diagnostic_bundle", "dev.run_self_tests"]
        ))
