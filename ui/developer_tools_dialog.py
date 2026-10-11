"""
PRUBETH IDE — Developer Tools & Subsystem Operations Inspector (Level C)
Pillar 6 & 7: Quality & Operations Governance

Exposes live internal application state, structured event stream, command directory,
configuration precedence inspector, feature flags, and diagnostic bundle export.
"""

from __future__ import annotations

import json
from typing import Optional
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QPlainTextEdit, QMessageBox, QFileDialog, QHeaderView
)

from ui.design_system import DesignTokens, ComponentStyles
from core.capability_registry import CapabilityRegistry
from core.command_registry import CommandRegistry
from core.event_bus import EventBus
from core.feature_flags import FeatureFlagService
from core.configuration_service import ConfigurationService
from horizon_engine.hardware_autotuner import HardwareAutoTuner


class DeveloperToolsDialog(QDialog):
    """Level C Developer & Operator Tools Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PRUBETH IDE — Developer Tools & Subsystem Inspector")
        self.resize(1080, 720)
        self.setMinimumSize(840, 560)

        self.cap_reg = CapabilityRegistry.get_instance()
        self.cmd_reg = CommandRegistry.get_instance()
        self.event_bus = EventBus.get_instance()
        self.flags_svc = FeatureFlagService.get_instance()
        self.config_svc = ConfigurationService.get_instance()

        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("🛠 Developer Tools & Subsystem Operations")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.ACCENT_CYAN};")
        header.addWidget(title)
        header.addStretch()

        btn_export = QPushButton("📦 Export Diagnostic Bundle")
        btn_export.setStyleSheet(ComponentStyles.primary_button())
        btn_export.clicked.connect(self._export_diagnostic_bundle)
        header.addWidget(btn_export)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_capabilities_tab(), "Capabilities (Levels A/B/C)")
        self.tabs.addTab(self._build_commands_tab(), "Command Registry")
        self.tabs.addTab(self._build_events_tab(), "Live Event Stream")
        self.tabs.addTab(self._build_config_tab(), "Configuration & Precedence")
        self.tabs.addTab(self._build_flags_tab(), "Feature Flags")
        root.addWidget(self.tabs, 1)

    def _build_capabilities_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["ID", "Name", "Level", "Category", "Status", "Location"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(ComponentStyles.table_view())

        caps = self.cap_reg.list_all()
        table.setRowCount(len(caps))
        for r, c in enumerate(caps):
            table.setItem(r, 0, QTableWidgetItem(c.component_id))
            table.setItem(r, 1, QTableWidgetItem(c.name))
            table.setItem(r, 2, QTableWidgetItem(f"Level {c.flexibility_level}"))
            table.setItem(r, 3, QTableWidgetItem(c.category))
            table.setItem(r, 4, QTableWidgetItem(c.status))
            table.setItem(r, 5, QTableWidgetItem(c.implementation_location))

        layout.addWidget(table)
        return w

    def _build_commands_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Command ID", "Title", "Category", "Shortcut", "Risk Level"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(ComponentStyles.table_view())

        cmds = self.cmd_reg.list_all()
        table.setRowCount(len(cmds))
        for r, cmd in enumerate(cmds):
            table.setItem(r, 0, QTableWidgetItem(cmd.command_id))
            table.setItem(r, 1, QTableWidgetItem(cmd.title))
            table.setItem(r, 2, QTableWidgetItem(cmd.category))
            table.setItem(r, 3, QTableWidgetItem(cmd.shortcut))
            table.setItem(r, 4, QTableWidgetItem(cmd.risk_level))

        layout.addWidget(table)
        return w

    def _build_events_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        self.event_stream_view = QPlainTextEdit()
        self.event_stream_view.setReadOnly(True)
        self.event_stream_view.setStyleSheet(f"""
            background-color: {DesignTokens.CANVAS_BG};
            color: {DesignTokens.TEXT_PRIMARY};
            font-family: {DesignTokens.FONT_FAMILY_MONO};
            font-size: 11px;
            border: 1px solid {DesignTokens.BORDER_SUBTLE};
        """)

        # Populate with recent history
        events = self.event_bus.get_history(limit=50)
        lines = []
        for e in events:
            lines.append(f"[{e.severity.upper()}] [{e.channel}] {e.source}: {json.dumps(e.payload)}")
        self.event_stream_view.setPlainText("\n".join(lines) if lines else "No events captured yet.")

        layout.addWidget(self.event_stream_view)
        return w

    def _build_config_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Setting Key", "Effective Value", "Source Scope (Precedence)"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(ComponentStyles.table_view())

        bundle = self.config_svc.export_bundle()
        # Collect all unique keys
        all_keys = set()
        for s_dict in bundle.get("scopes", {}).values():
            all_keys.update(s_dict.keys())

        table.setRowCount(len(all_keys))
        for r, k in enumerate(sorted(all_keys)):
            val, src = self.config_svc.get_with_source(k)
            table.setItem(r, 0, QTableWidgetItem(k))
            table.setItem(r, 1, QTableWidgetItem(str(val)))
            table.setItem(r, 2, QTableWidgetItem(src))

        layout.addWidget(table)
        return w

    def _build_flags_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Flag ID", "Name", "Maturity", "Active"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(ComponentStyles.table_view())

        flags = self.flags_svc.list_all()
        table.setRowCount(len(flags))
        for r, f in enumerate(flags):
            table.setItem(r, 0, QTableWidgetItem(f.flag_id))
            table.setItem(r, 1, QTableWidgetItem(f.name))
            table.setItem(r, 2, QTableWidgetItem(f.maturity))
            item_act = QTableWidgetItem("Enabled" if f.enabled else "Disabled")
            item_act.setForeground(Qt.cyan if f.enabled else Qt.gray)
            table.setItem(r, 3, item_act)

        layout.addWidget(table)
        return w

    def _export_diagnostic_bundle(self):
        """Generates a sanitized JSON diagnostic bundle containing hardware, capabilities, and health."""
        hw = HardwareAutoTuner.detect_hardware()
        bundle = {
            "application": "PRUBETH IDE",
            "version": "3.0.0",
            "hardware": {
                "os": hw.os_name,
                "cpu_threads": hw.cpu_threads,
                "ram_total_mb": hw.ram_total_mb,
                "gpu": hw.gpu_name,
                "vram_total_mb": hw.vram_total_mb,
                "tier": hw.tier_name
            },
            "capabilities": self.cap_reg.export_inventory(),
            "flags": [f.flag_id for f in self.flags_svc.list_all() if f.enabled],
            "recent_events": [e.__dict__ for e in self.event_bus.get_history(limit=25)]
        }

        path, _ = QFileDialog.getSaveFileName(self, "Export Diagnostic Bundle", "prubeth_diagnostic_bundle.json", "JSON (*.json)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(bundle, f, indent=2)
                QMessageBox.information(self, "Export Successful", f"Diagnostic bundle exported cleanly to:\n{path}")
            except Exception as exc:
                QMessageBox.warning(self, "Export Failed", str(exc))

    def _apply_styles(self):
        t = DesignTokens
        self.setStyleSheet(f"""
            QDialog {{ background-color: {t.CANVAS_BG}; color: {t.TEXT_PRIMARY}; }}
            QTabWidget::pane {{ border: 1px solid {t.BORDER_SUBTLE}; background-color: {t.SURFACE_PANEL}; }}
            QTabBar::tab {{
                background-color: {t.SURFACE_ELEVATED};
                color: {t.TEXT_SECONDARY};
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {t.SURFACE_PANEL};
                color: {t.ACCENT_CYAN};
                border-bottom: 2px solid {t.ACCENT_CYAN};
            }}
        """)
