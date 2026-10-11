"""
PRUBETH IDE — Live Reliability Center & PRINCE2 7 Assurance Dashboard
=====================================================================
Native PyQt5 GUI widget embedded into the IDE bottom panel / tabs.
Provides interactive controls to run, pause, stop, and inspect
the 9 Reliability Profiles, live telemetry, and stage-gate decisions.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QProgressBar, QTextEdit, QFrame, QFileDialog, QMessageBox
)

from core.reliability_engine import (
    ReliabilityEngine, ReliabilityProfile, ScenarioResult,
    Prince2Report, ScenarioStatus, StageGateDecision
)


class ReliabilityWorkerThread(QThread):
    scenario_completed = pyqtSignal(object)  # ScenarioResult
    profile_finished = pyqtSignal(object)   # Prince2Report

    def __init__(self, engine: ReliabilityEngine, profile: ReliabilityProfile):
        super().__init__()
        self.engine = engine
        self.profile = profile

    def run(self):
        self.engine.register_progress_callback(self._on_progress)
        report = self.engine.run_profile(self.profile)
        self.profile_finished.emit(report)

    def _on_progress(self, res: ScenarioResult):
        self.scenario_completed.emit(res)


class MetricCard(QFrame):
    """Small telemetry metric card for the reliability dashboard."""
    def __init__(self, title: str, value: str = "0", value_color: str = "#E8EAF0", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #1D2028;
                border: 1px solid #343A49;
                border-radius: 6px;
                padding: 6px 12px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("color: #737B8C; font-size: 8pt; font-weight: bold;")
        layout.addWidget(self.lbl_title)

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: {value_color}; font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.lbl_value)

    def set_value(self, val: str):
        self.lbl_value.setText(val)


class ReliabilityCenterWidget(QWidget):
    """
    Native Reliability Center GUI Widget.
    Embedded into IDE's bottom tabs or as standalone dialog.
    """

    def __init__(self, workspace_root: Optional[Path] = None, parent=None):
        super().__init__(parent)
        self.workspace_root = workspace_root or Path.cwd()
        self.engine = ReliabilityEngine(self.workspace_root)
        self.worker: Optional[ReliabilityWorkerThread] = None
        self.last_report: Optional[Prince2Report] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 1. Top Control Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        lbl_profile = QLabel("Profile:")
        lbl_profile.setStyleSheet("color: #E8EAF0; font-weight: 600; font-size: 10pt;")
        top_bar.addWidget(lbl_profile)

        self.combo_profile = QComboBox()
        for p in ReliabilityProfile:
            self.combo_profile.addItem(p.value, p)
        self.combo_profile.setCurrentText(ReliabilityProfile.RELEASE_CANDIDATE.value)
        self.combo_profile.setStyleSheet("""
            QComboBox {
                background: #191C23;
                color: #E8EAF0;
                border: 1px solid #343A49;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: 600;
            }
        """)
        top_bar.addWidget(self.combo_profile)

        self.btn_run = QPushButton("▶ Run Profile")
        self.btn_run.setStyleSheet("background: #9485FF; color: #FFFFFF; font-weight: bold; padding: 5px 14px; border-radius: 4px;")
        self.btn_run.clicked.connect(self.start_profile)
        top_bar.addWidget(self.btn_run)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background: #252934; color: #FF7D86; border: 1px solid #343A49; padding: 5px 12px; border-radius: 4px;")
        self.btn_stop.clicked.connect(self.stop_profile)
        top_bar.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("🧹 Clear")
        self.btn_clear.setStyleSheet("background: #252934; color: #A5ACBB; border: 1px solid #343A49; padding: 5px 12px; border-radius: 4px;")
        self.btn_clear.clicked.connect(self.clear_console)
        top_bar.addWidget(self.btn_clear)

        self.btn_export = QPushButton("📄 Export Report")
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("background: #252934; color: #62D4E5; border: 1px solid #343A49; padding: 5px 12px; border-radius: 4px;")
        self.btn_export.clicked.connect(self.export_report)
        top_bar.addWidget(self.btn_export)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        # 2. Telemetry Metric Cards
        cards_bar = QHBoxLayout()
        cards_bar.setSpacing(8)

        self.card_passed = MetricCard("Passed", "0", "#70D6A0")
        self.card_failed = MetricCard("Failed", "0", "#FF7D86")
        self.card_blocked = MetricCard("Blocked", "0", "#FFBF69")
        self.card_memory = MetricCard("Peak RSS", "0.0 MB", "#62D4E5")
        self.card_time = MetricCard("Duration", "0.0s", "#E8EAF0")

        cards_bar.addWidget(self.card_passed)
        cards_bar.addWidget(self.card_failed)
        cards_bar.addWidget(self.card_blocked)
        cards_bar.addWidget(self.card_memory)
        cards_bar.addWidget(self.card_time)
        layout.addLayout(cards_bar)

        # 3. Stage-Gate Status Banner
        self.banner_gate = QFrame()
        self.banner_gate.setStyleSheet("background: #1D2028; border: 1px solid #343A49; border-radius: 6px; padding: 6px 12px;")
        gate_layout = QHBoxLayout(self.banner_gate)
        gate_layout.setContentsMargins(8, 4, 8, 4)

        self.lbl_gate = QLabel("PRINCE2 RELEASE GATE: READY TO EXECUTE")
        self.lbl_gate.setStyleSheet("color: #9485FF; font-weight: bold; font-size: 10pt;")
        gate_layout.addWidget(self.lbl_gate)
        layout.addWidget(self.banner_gate)

        # 4. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #191C23;
                border: 1px solid #343A49;
                border-radius: 3px;
                height: 14px;
                text-align: center;
                color: #FFFFFF;
                font-size: 8pt;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9485FF, stop:1 #62D4E5);
            }
        """)
        layout.addWidget(self.progress_bar)

        # 5. Live Console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Cascadia Code", 9))
        self.console.setStyleSheet("""
            QTextEdit {
                background: #111318;
                color: #E8EAF0;
                border: 1px solid #343A49;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        layout.addWidget(self.console, 1)

    def log(self, text: str, color: str = "#E8EAF0"):
        self.console.append(f"<span style='color: {color};'>{text}</span>")

    def clear_console(self):
        self.console.clear()
        self.progress_bar.setValue(0)
        self.card_passed.set_value("0")
        self.card_failed.set_value("0")
        self.card_blocked.set_value("0")
        self.card_memory.set_value("0.0 MB")
        self.card_time.set_value("0.0s")
        self.lbl_gate.setText("PRINCE2 RELEASE GATE: READY TO EXECUTE")
        self.lbl_gate.setStyleSheet("color: #9485FF; font-weight: bold; font-size: 10pt;")

    def start_profile(self):
        profile = self.combo_profile.currentData()
        self.clear_console()
        self.log(f"=== STARTING PRINCE2 7 PROFILE: {profile.value.upper()} ===", "#9485FF")

        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_export.setEnabled(False)
        self.lbl_gate.setText("PRINCE2 RELEASE GATE: RUNNING ASSURANCE CHECKS...")
        self.lbl_gate.setStyleSheet("color: #62D4E5; font-weight: bold; font-size: 10pt;")

        self.worker = ReliabilityWorkerThread(self.engine, profile)
        self.worker.scenario_completed.connect(self._on_scenario_completed)
        self.worker.profile_finished.connect(self._on_profile_finished)
        self.worker.start()

    def stop_profile(self):
        if self.worker and self.worker.isRunning():
            self.engine.request_stop()
            self.log("[!] Emergency stop requested by user.", "#FF7D86")

    def _on_scenario_completed(self, res: ScenarioResult):
        color = "#70D6A0" if res.status == ScenarioStatus.PASSED else "#FF7D86"
        mark = "✓ PASS" if res.status == ScenarioStatus.PASSED else "✗ FAIL"
        self.log(f"[{res.category.upper()}] {res.name} — <b>{mark}</b> ({res.duration_seconds:.2f}s): {res.details or res.error}", color)

    def _on_profile_finished(self, report: Prince2Report):
        self.last_report = report
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_export.setEnabled(True)
        self.progress_bar.setValue(100)

        duration = report.end_time - report.start_time
        self.card_passed.set_value(str(report.passed_count))
        self.card_failed.set_value(str(report.failed_count))
        self.card_blocked.set_value(str(report.blocked_count))
        self.card_memory.set_value(f"{report.peak_memory_mb:.1f} MB")
        self.card_time.set_value(f"{duration:.1f}s")

        if report.stage_gate_decision == StageGateDecision.APPROVED:
            self.lbl_gate.setText(f"PRINCE2 RELEASE GATE: {report.stage_gate_decision.value}")
            self.lbl_gate.setStyleSheet("color: #70D6A0; font-weight: bold; font-size: 10pt;")
            self.log(f"\n[+] PROFILE COMPLETE: 100% QUALITY GATES SATISFIED ({report.passed_count}/{report.total_scenarios} passed)", "#70D6A0")
        else:
            self.lbl_gate.setText(f"PRINCE2 RELEASE GATE: {report.stage_gate_decision.value}")
            self.lbl_gate.setStyleSheet("color: #FF7D86; font-weight: bold; font-size: 10pt;")
            self.log(f"\n[!] PROFILE COMPLETE: GATE BLOCKED ({report.failed_count} failures detected)", "#FF7D86")

    def export_report(self):
        if not self.last_report:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save PRINCE2 Audit Report", "prince2_reliability_report.json", "JSON (*.json)")
        if path:
            try:
                import dataclasses
                report_dict = dataclasses.asdict(self.last_report)
                Path(path).write_text(json.dumps(report_dict, indent=2, default=str), encoding="utf-8")
                QMessageBox.information(self, "Report Exported", f"Audit report successfully saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed saving report: {e}")
