"""
PRUBETH IDE — User Interface & Presentation Subsystem
Provides UI dock widgets, sidebars, activity bar, breadcrumbs, composer, dialogs, and themes.
"""
from ui.git_sidebar import GitSidebarWidget
from ui.checkpoints_widget import CheckpointsWidget
from ui.diagnostics_widget import DiagnosticsWidget
from ui.debug_widget import DebugPanelWidget
from ui.activity_bar import ActivityBarWidget
from ui.breadcrumb_bar import BreadcrumbBarWidget
from ui.testing_widget import TestingWidget
from ui.gpu_telemetry_widget import GpuTelemetryWidget
from ui.composer_widget import ComposerWidget
from ui.open_vsx_widget import OpenVsxWidget
from ui.settings_dialog import SettingsDialog

__all__ = [
    "GitSidebarWidget",
    "CheckpointsWidget",
    "DiagnosticsWidget",
    "DebugPanelWidget",
    "ActivityBarWidget",
    "BreadcrumbBarWidget",
    "TestingWidget",
    "GpuTelemetryWidget",
    "ComposerWidget",
    "OpenVsxWidget",
    "SettingsDialog"
]
