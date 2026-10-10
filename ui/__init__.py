"""
SUKHI IDE — User Interface & Presentation Subsystem
Provides UI dock widgets, sidebars, dialogs, and themes.
"""
from ui.git_sidebar import GitSidebarWidget
from ui.checkpoints_widget import CheckpointsWidget
from ui.diagnostics_widget import DiagnosticsWidget
from ui.debug_widget import DebugPanelWidget

__all__ = [
    "GitSidebarWidget",
    "CheckpointsWidget",
    "DiagnosticsWidget",
    "DebugPanelWidget"
]
