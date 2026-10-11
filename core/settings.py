"""
PRUBETH IDE — SETTINGS FACADE
=============================
Re-exports SettingsStore and configuration constants from ui.settings_center
to provide clean core subsystem access.
"""

from ui.settings_center import SettingsStore, DEFAULTS

__all__ = ["SettingsStore", "DEFAULTS"]
