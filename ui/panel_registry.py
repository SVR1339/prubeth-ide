"""
PRUBETH IDE — Adaptable Panel Registry & Layout Preset Architecture
Pillar 3 & 4: Experience & Design System Governance

Governs dockable panels, containers, and 6 named layout presets:
Coding, Agent Workspace, Debugging, Code Review, Research, and Minimal.
Provides safe state recovery and persistent layout restoration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable


@dataclass
class PanelDescriptor:
    """Represents a dockable or switchable UI panel within the IDE shell."""
    panel_id: str
    title: str
    category: str  # sidebar, bottom_panel, dock, surface
    default_visible: bool = True
    default_area: str = "left"  # left, right, bottom, central
    icon: str = "📦"
    description: str = ""


@dataclass
class LayoutPreset:
    """Pre-configured workspace layout arrangement tailored for specific engineering tasks."""
    name: str
    description: str
    visible_panel_ids: List[str]
    active_surface: str = "editor"  # "editor" (Synchronous) or "mission_control" (Asynchronous)
    density: str = "Comfortable"


class PanelRegistry:
    """Central registry holding panel definitions and named layout configurations."""

    _instance: Optional[PanelRegistry] = None

    def __init__(self):
        self._panels: Dict[str, PanelDescriptor] = {}
        self._presets: Dict[str, LayoutPreset] = {}
        self._register_default_panels()
        self._register_default_presets()

    @classmethod
    def get_instance(cls) -> PanelRegistry:
        if cls._instance is None:
            cls._instance = PanelRegistry()
        return cls._instance

    def register_panel(self, panel: PanelDescriptor) -> None:
        self._panels[panel.panel_id] = panel

    def get_panel(self, panel_id: str) -> Optional[PanelDescriptor]:
        return self._panels.get(panel_id)

    def list_panels(self) -> List[PanelDescriptor]:
        return list(self._panels.values())

    def register_preset(self, preset: LayoutPreset) -> None:
        self._presets[preset.name] = preset

    def get_preset(self, name: str) -> Optional[LayoutPreset]:
        return self._presets.get(name)

    def list_presets(self) -> List[LayoutPreset]:
        return list(self._presets.values())

    def _register_default_panels(self) -> None:
        self.register_panel(PanelDescriptor(
            panel_id="panel.explorer",
            title="File Explorer",
            category="sidebar",
            default_area="left",
            icon="📁",
            description="Project tree view with file creation and deletion controls."
        ))
        self.register_panel(PanelDescriptor(
            panel_id="panel.git",
            title="Source Control",
            category="sidebar",
            default_area="left",
            icon="🌿",
            description="Git status, staging, commit, and visual diff inspection."
        ))
        self.register_panel(PanelDescriptor(
            panel_id="panel.composer",
            title="Composer Dock",
            category="dock",
            default_area="right",
            icon="✨",
            description="Cursor/Windsurf multi-file AI editing and atomic diff application."
        ))
        self.register_panel(PanelDescriptor(
            panel_id="panel.terminal",
            title="Integrated Terminal",
            category="bottom_panel",
            default_area="bottom",
            icon="💻",
            description="Multi-tab interactive PowerShell, CMD, or WSL session."
        ))
        self.register_panel(PanelDescriptor(
            panel_id="panel.diagnostics",
            title="Problems & Diagnostics",
            category="bottom_panel",
            default_area="bottom",
            icon="⚠️",
            description="Language server warnings, lint errors, and syntax anomalies."
        ))
        self.register_panel(PanelDescriptor(
            panel_id="panel.checkpoints",
            title="Time-Machine Checkpoints",
            category="sidebar",
            default_area="left",
            icon="🕒",
            description="Transactional snapshots and 1-click delta rollbacks."
        ))
        self.register_panel(PanelDescriptor(
            panel_id="panel.mission_control",
            title="Mission Control Surface",
            category="surface",
            default_area="central",
            icon="🚀",
            description="Full-screen asynchronous agent execution and ReAct log monitoring."
        ))
        self.register_panel(PanelDescriptor(
            panel_id="panel.open_vsx",
            title="Open VSX Extensions",
            category="sidebar",
            default_area="left",
            icon="🧩",
            description="Open marketplace extension browsing and installation."
        ))

    def _register_default_presets(self) -> None:
        self.register_preset(LayoutPreset(
            name="Coding",
            description="Balanced standard setup: Explorer, Editor tabs, Terminal, and Composer.",
            visible_panel_ids=["panel.explorer", "panel.terminal", "panel.composer"],
            active_surface="editor"
        ))
        self.register_preset(LayoutPreset(
            name="Agent Workspace",
            description="Optimized for autonomous multi-agent planning and ReAct observation.",
            visible_panel_ids=["panel.mission_control", "panel.terminal"],
            active_surface="mission_control"
        ))
        self.register_preset(LayoutPreset(
            name="Debugging",
            description="Focused on diagnostics, terminal output, and symbol tracebacks.",
            visible_panel_ids=["panel.diagnostics", "panel.terminal", "panel.explorer"],
            active_surface="editor"
        ))
        self.register_preset(LayoutPreset(
            name="Code Review",
            description="Optimized for Git diffs, delta inspection, and transactional checkpoints.",
            visible_panel_ids=["panel.git", "panel.checkpoints", "panel.composer"],
            active_surface="editor"
        ))
        self.register_preset(LayoutPreset(
            name="Research",
            description="Clean layout with Open VSX, codebase search, and documentation tabs.",
            visible_panel_ids=["panel.explorer", "panel.open_vsx"],
            active_surface="editor"
        ))
        self.register_preset(LayoutPreset(
            name="Minimal",
            description="Distraction-free full-screen editor with all sidebars collapsed.",
            visible_panel_ids=[],
            active_surface="editor",
            density="Compact"
        ))
