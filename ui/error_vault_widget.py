"""
PRUBETH IDE — Main Reporting Area & Bulletproof Bug Resolution Center
======================================================================
Native PyQt5 widget embedded in the IDE bottom panel / main reporting area.
Provides real-time visibility into all recorded runtime errors, bugs, and defects,
with 1-click "Solve & Fix Error (AI Copilot)", code navigation, and daily report generation.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QSplitter, QFrame, QMessageBox, QTabWidget, QApplication
)

from core.error_vault import ErrorVault, ErrorRecord, ErrorStatus, ErrorSeverity


SEVERITY_COLORS = {
    "CRITICAL": "#FF4444",
    "ERROR": "#FF7D86",
    "WARNING": "#FFBF69",
    "DEFECT": "#B4A9FF",
}

STATUS_COLORS = {
    "UNRESOLVED": "#FF7D86",
    "IN_PROGRESS": "#FFBF69",
    "RESOLVED": "#70D6A0",
    "AUTO_REPAIRED": "#62D4E5",
    "IGNORED": "#737B8C",
}


class StatCard(QFrame):
    """Telemetry stat card for the error vault header."""
    def __init__(self, title: str, value: str = "0", value_color: str = "#E8EAF0", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #1D2028;
                border: 1px solid #343A49;
                border-radius: 6px;
                padding: 4px 10px;
            }
        """)
        l = QVBoxLayout(self)
        l.setContentsMargins(6, 4, 6, 4)
        l.setSpacing(2)

        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("color: #737B8C; font-size: 7.5pt; font-weight: bold;")
        l.addWidget(self.lbl_title)

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: {value_color}; font-size: 13pt; font-weight: bold;")
        l.addWidget(self.lbl_value)

    def set_value(self, val: str):
        self.lbl_value.setText(val)


class ErrorVaultWidget(QWidget):
    """
    Main Reporting Area for PRUBETH IDE.
    Displays persistent error ledger and enables 1-click AI resolution.
    """
    solve_error_requested = pyqtSignal(object)       # Emits ErrorRecord
    navigate_to_source = pyqtSignal(str, int, int)    # Emits file_path, line, col

    def __init__(self, parent=None, vault: Optional[ErrorVault] = None):
        super().__init__(parent)
        self.vault = vault or ErrorVault.get_instance()
        self.selected_record: Optional[ErrorRecord] = None
        self._init_ui()
        self.vault.register_listener(self._on_vault_updated)
        self.refresh_records()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # 1. Top Telemetry Cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(6)
        self.card_total = StatCard("Total Bugs Logged", "0", "#E8EAF0")
        self.card_unresolved = StatCard("Active Unresolved", "0", "#FF7D86")
        self.card_in_progress = StatCard("In Progress", "0", "#FFBF69")
        self.card_resolved = StatCard("Resolved / Fixed", "0", "#70D6A0")
        self.card_health = StatCard("Reliability Index", "100%", "#62D4E5")

        cards_row.addWidget(self.card_total)
        cards_row.addWidget(self.card_unresolved)
        cards_row.addWidget(self.card_in_progress)
        cards_row.addWidget(self.card_resolved)
        cards_row.addWidget(self.card_health)
        cards_row.addStretch()

        # Action buttons on header
        self.btn_daily_report = QPushButton("📄 Daily Report")
        self.btn_daily_report.setStyleSheet("background: #252934; color: #62D4E5; border: 1px solid #343A49; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        self.btn_daily_report.clicked.connect(self.generate_and_show_daily_report)
        cards_row.addWidget(self.btn_daily_report)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setStyleSheet("background: #252934; color: #E8EAF0; border: 1px solid #343A49; padding: 6px 12px; border-radius: 4px;")
        self.btn_refresh.clicked.connect(self.refresh_records)
        cards_row.addWidget(self.btn_refresh)

        self.btn_clear_resolved = QPushButton("🧹 Clear Resolved")
        self.btn_clear_resolved.setStyleSheet("background: #252934; color: #A5ACBB; border: 1px solid #343A49; padding: 6px 10px; border-radius: 4px;")
        self.btn_clear_resolved.clicked.connect(self.clear_resolved)
        cards_row.addWidget(self.btn_clear_resolved)

        main_layout.addLayout(cards_row)

        # 2. Filter Bar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter errors by message, type, file, or error ID...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #191C23;
                color: #E8EAF0;
                border: 1px solid #343A49;
                border-radius: 4px;
                padding: 5px 8px;
            }
        """)
        self.search_input.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_input, 2)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "Unresolved & In Progress", "Unresolved Only", "Resolved", "Auto-Repaired"])
        self.status_filter.setStyleSheet("background: #191C23; color: #E8EAF0; border: 1px solid #343A49; padding: 4px 8px; border-radius: 4px;")
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        filter_row.addWidget(self.status_filter)

        self.subsystem_filter = QComboBox()
        self.subsystem_filter.addItems(["All Subsystems", "CORE", "AI_AGENT", "UI", "TOOL_ENGINE", "RUNTIME", "BACKGROUND_WORKER", "QT_CORE"])
        self.subsystem_filter.setStyleSheet("background: #191C23; color: #E8EAF0; border: 1px solid #343A49; padding: 4px 8px; border-radius: 4px;")
        self.subsystem_filter.currentTextChanged.connect(self._apply_filters)
        filter_row.addWidget(self.subsystem_filter)

        self.date_filter = QComboBox()
        self.date_filter.addItems(["All Time", "Today Only", "Past 7 Days"])
        self.date_filter.setStyleSheet("background: #191C23; color: #E8EAF0; border: 1px solid #343A49; padding: 4px 8px; border-radius: 4px;")
        self.date_filter.currentTextChanged.connect(self._apply_filters)
        filter_row.addWidget(self.date_filter)

        main_layout.addLayout(filter_row)

        # 3. Main Splitter: Top = Error List, Bottom = Inspector & Actions
        splitter = QSplitter(Qt.Vertical)

        # Top: Error Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Severity", "Error ID", "Status", "Subsystem", "Error Message", "Hits", "Last Seen", "Location"])
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: #111318;
                border: 1px solid #343A49;
                border-radius: 4px;
                color: #E8EAF0;
            }
            QTreeWidget::item { padding: 4px; }
            QTreeWidget::item:selected { background: #252934; color: #9485FF; }
        """)
        self.tree.setColumnWidth(0, 95)
        self.tree.setColumnWidth(1, 160)
        self.tree.setColumnWidth(2, 110)
        self.tree.setColumnWidth(3, 110)
        self.tree.setColumnWidth(4, 380)
        self.tree.setColumnWidth(5, 50)
        self.tree.setColumnWidth(6, 140)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        splitter.addWidget(self.tree)

        # Bottom: Detail & Auto-Remediation Pane
        inspector_frame = QFrame()
        inspector_frame.setStyleSheet("""
            QFrame {
                background: #15171D;
                border: 1px solid #343A49;
                border-radius: 4px;
            }
        """)
        insp_layout = QVBoxLayout(inspector_frame)
        insp_layout.setContentsMargins(8, 8, 8, 8)
        insp_layout.setSpacing(6)

        # Action & Inspector Header Bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self.lbl_selected_title = QLabel("Select an error above to view diagnosis and fix actions.")
        self.lbl_selected_title.setStyleSheet("color: #E8EAF0; font-weight: bold; font-size: 9.5pt;")
        action_bar.addWidget(self.lbl_selected_title, 1)

        self.btn_solve_ai = QPushButton("✨ Solve & Fix Error (AI Agent)")
        self.btn_solve_ai.setEnabled(False)
        self.btn_solve_ai.setStyleSheet("""
            QPushButton {
                background: #9485FF;
                color: #FFFFFF;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background: #343A49;
                color: #737B8C;
            }
        """)
        self.btn_solve_ai.clicked.connect(self._on_solve_ai_clicked)
        action_bar.addWidget(self.btn_solve_ai)

        self.btn_jump_code = QPushButton("📂 Jump to Code")
        self.btn_jump_code.setEnabled(False)
        self.btn_jump_code.setStyleSheet("background: #252934; color: #62D4E5; border: 1px solid #343A49; padding: 6px 12px; border-radius: 4px;")
        self.btn_jump_code.clicked.connect(self._on_jump_code_clicked)
        action_bar.addWidget(self.btn_jump_code)

        self.btn_mark_resolved = QPushButton("✓ Mark Resolved")
        self.btn_mark_resolved.setEnabled(False)
        self.btn_mark_resolved.setStyleSheet("background: #252934; color: #70D6A0; border: 1px solid #343A49; padding: 6px 12px; border-radius: 4px;")
        self.btn_mark_resolved.clicked.connect(self._on_mark_resolved_clicked)
        action_bar.addWidget(self.btn_mark_resolved)

        self.btn_copy_traceback = QPushButton("📋 Copy Traceback")
        self.btn_copy_traceback.setEnabled(False)
        self.btn_copy_traceback.setStyleSheet("background: #252934; color: #A5ACBB; border: 1px solid #343A49; padding: 6px 10px; border-radius: 4px;")
        self.btn_copy_traceback.clicked.connect(self._on_copy_traceback_clicked)
        action_bar.addWidget(self.btn_copy_traceback)

        insp_layout.addLayout(action_bar)

        # Inspector Tabs: Traceback vs Context Dump vs Remediation Notes
        self.inspector_tabs = QTabWidget()
        self.inspector_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #343A49; background: #111318; }
            QTabBar::tab { background: #1D2028; color: #A5ACBB; padding: 4px 10px; border: 1px solid #343A49; }
            QTabBar::tab:selected { background: #252934; color: #9485FF; font-weight: bold; }
        """)

        self.txt_traceback = QTextEdit()
        self.txt_traceback.setReadOnly(True)
        self.txt_traceback.setFont(QFont("Cascadia Code", 9))
        self.txt_traceback.setStyleSheet("background: #111318; color: #E8EAF0; border: none; padding: 6px;")
        self.inspector_tabs.addTab(self.txt_traceback, "Traceback & Stack")

        self.txt_context = QTextEdit()
        self.txt_context.setReadOnly(True)
        self.txt_context.setFont(QFont("Cascadia Code", 9))
        self.txt_context.setStyleSheet("background: #111318; color: #CBD5E1; border: none; padding: 6px;")
        self.inspector_tabs.addTab(self.txt_context, "Execution Context")

        self.txt_remediation = QTextEdit()
        self.txt_remediation.setFont(QFont("Segoe UI", 9))
        self.txt_remediation.setPlaceholderText("Remediation notes, root cause explanations, and patch details will appear here...")
        self.txt_remediation.setStyleSheet("background: #111318; color: #70D6A0; border: none; padding: 6px;")
        self.inspector_tabs.addTab(self.txt_remediation, "Remediation Notes")

        insp_layout.addWidget(self.inspector_tabs, 1)
        splitter.addWidget(inspector_frame)

        splitter.setSizes([320, 220])
        main_layout.addWidget(splitter, 1)

    def _on_vault_updated(self, record: ErrorRecord):
        """Triggered from background or worker threads when error is saved."""
        try:
            # We defer execution to Qt event loop via singleShot or direct refresh if in GUI thread
            self.refresh_records()
        except Exception:
            pass

    def refresh_records(self):
        """Reloads all records and updates telemetry cards and table."""
        all_errors = self.vault.get_all_errors()
        total_count = len(all_errors)
        unresolved_count = sum(1 for r in all_errors if r.status == ErrorStatus.UNRESOLVED.value)
        in_progress_count = sum(1 for r in all_errors if r.status == ErrorStatus.IN_PROGRESS.value)
        resolved_count = sum(1 for r in all_errors if r.status in (ErrorStatus.RESOLVED.value, ErrorStatus.AUTO_REPAIRED.value))

        reliability_pct = (resolved_count / total_count * 100.0) if total_count > 0 else 100.0

        self.card_total.set_value(str(total_count))
        self.card_unresolved.set_value(str(unresolved_count))
        self.card_in_progress.set_value(str(in_progress_count))
        self.card_resolved.set_value(str(resolved_count))
        self.card_health.set_value(f"{reliability_pct:.1f}%")

        self._apply_filters()

    def _apply_filters(self):
        self.tree.clear()
        errors = self.vault.get_all_errors()

        search_text = self.search_input.text().strip().lower()
        status_filter = self.status_filter.currentText()
        subsystem_filter = self.subsystem_filter.currentText()
        date_filter = self.date_filter.currentText()
        today_str = datetime.now().strftime("%Y-%m-%d")

        for err in errors:
            # Status filter
            if status_filter == "Unresolved & In Progress" and err.status not in (ErrorStatus.UNRESOLVED.value, ErrorStatus.IN_PROGRESS.value):
                continue
            elif status_filter == "Unresolved Only" and err.status != ErrorStatus.UNRESOLVED.value:
                continue
            elif status_filter == "Resolved" and err.status != ErrorStatus.RESOLVED.value:
                continue
            elif status_filter == "Auto-Repaired" and err.status != ErrorStatus.AUTO_REPAIRED.value:
                continue

            # Subsystem filter
            if subsystem_filter != "All Subsystems" and err.subsystem != subsystem_filter:
                continue

            # Date filter
            if date_filter == "Today Only" and not (err.first_seen_iso.startswith(today_str) or err.last_seen_iso.startswith(today_str)):
                continue

            # Text filter
            if search_text:
                full_searchable = f"{err.error_id} {err.error_type} {err.message} {err.file_path or ''} {err.traceback_str}".lower()
                if search_text not in full_searchable:
                    continue

            # Location label
            loc_label = f"{os.path.basename(err.file_path)}:{err.line_number}" if err.file_path and err.line_number else "N/A"
            clean_date = err.last_seen_iso.replace("T", " ")[:19]

            item = QTreeWidgetItem([
                err.severity,
                err.error_id,
                err.status,
                err.subsystem,
                err.message[:120],
                str(err.occurrence_count),
                clean_date,
                loc_label
            ])

            # Apply badge colors
            sev_color = SEVERITY_COLORS.get(err.severity, "#E8EAF0")
            status_color = STATUS_COLORS.get(err.status, "#E8EAF0")
            item.setForeground(0, QColor(sev_color))
            item.setForeground(2, QColor(status_color))

            item.setData(0, Qt.UserRole, err.error_id)
            self.tree.addTopLevelItem(item)

        if self.tree.topLevelItemCount() > 0:
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    def _on_selection_changed(self):
        items = self.tree.selectedItems()
        if not items:
            self.selected_record = None
            self.lbl_selected_title.setText("Select an error above to view diagnosis and fix actions.")
            self.btn_solve_ai.setEnabled(False)
            self.btn_jump_code.setEnabled(False)
            self.btn_mark_resolved.setEnabled(False)
            self.btn_copy_traceback.setEnabled(False)
            self.txt_traceback.clear()
            self.txt_context.clear()
            self.txt_remediation.clear()
            return

        error_id = items[0].data(0, Qt.UserRole)
        rec = self.vault.get_error(error_id)
        if not rec:
            return

        self.selected_record = rec
        self.btn_solve_ai.setEnabled(True)
        self.btn_jump_code.setEnabled(bool(rec.file_path and rec.line_number))
        self.btn_mark_resolved.setEnabled(rec.status != ErrorStatus.RESOLVED.value)
        self.btn_copy_traceback.setEnabled(True)

        loc_str = f"in {os.path.basename(rec.file_path)}:{rec.line_number}" if rec.file_path else ""
        self.lbl_selected_title.setText(f"<b>[{rec.severity}]</b> {rec.error_type} {loc_str} (Occurrences: {rec.occurrence_count})")

        self.txt_traceback.setPlainText(rec.traceback_str or f"{rec.error_type}: {rec.message}")
        self.txt_context.setPlainText(json.dumps(rec.context_dump, indent=2, default=str))
        self.txt_remediation.setPlainText(rec.remediation_notes or "No notes recorded yet.")

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        self._on_jump_code_clicked()

    def _on_jump_code_clicked(self):
        if self.selected_record and self.selected_record.file_path and self.selected_record.line_number:
            self.navigate_to_source.emit(
                self.selected_record.file_path,
                self.selected_record.line_number,
                0
            )

    def _on_solve_ai_clicked(self):
        """Dispatches selected bug to AI Copilot for autonomous remediation."""
        if not self.selected_record:
            return

        # Mark bug status as IN_PROGRESS
        self.vault.update_status(self.selected_record.error_id, ErrorStatus.IN_PROGRESS.value, "AI Auto-Fix initiated")
        self.refresh_records()

        # Emit solve request signal to IDE host
        self.solve_error_requested.emit(self.selected_record)

    def _on_mark_resolved_clicked(self):
        if not self.selected_record:
            return

        notes = self.txt_remediation.toPlainText().strip()
        if not notes:
            notes = "Marked resolved manually via Error Vault."

        self.vault.resolve_error(self.selected_record.error_id, notes=notes, resolved_by="USER")
        self.refresh_records()
        QMessageBox.information(self, "Bug Resolved", f"Error {self.selected_record.error_id} has been marked as RESOLVED.")

    def _on_copy_traceback_clicked(self):
        if not self.selected_record:
            return
        payload = (
            f"ERROR ID: {self.selected_record.error_id}\n"
            f"TYPE: {self.selected_record.error_type}\n"
            f"MESSAGE: {self.selected_record.message}\n"
            f"LOCATION: {self.selected_record.file_path}:{self.selected_record.line_number}\n"
            f"TRACEBACK:\n{self.selected_record.traceback_str}\n"
        )
        cb = QApplication.clipboard()
        cb.setText(payload)
        QMessageBox.information(self, "Copied", "Error details and traceback copied to clipboard.")

    def clear_resolved(self):
        """Clears resolved bugs from the active view."""
        count = self.vault.clear_resolved_errors()
        self.refresh_records()
        QMessageBox.information(self, "Cleared", f"Pruned {count} resolved bugs from active view (historical records preserved in immutable ledger).")

    def generate_and_show_daily_report(self):
        """Generates daily report and displays preview dialog."""
        report = self.vault.generate_daily_report()
        today_str = report["report_date"]
        fix_rate = report["fix_rate_percentage"]
        unique_cnt = report["total_unique_bugs_active"]
        unresolved = report["unresolved"]

        md_path = self.vault.daily_dir / f"daily_report_{today_str}.md"
        content = md_path.read_text(encoding="utf-8") if md_path.exists() else "Report generated."

        dlg = QMessageBox(self)
        dlg.setWindowTitle(f"PRUBETH Daily Error Report — {today_str}")
        dlg.setText(f"<h3>Daily Reliability Audit: {today_str}</h3>"
                     f"<p><b>Total Unique Bugs:</b> {unique_cnt}<br>"
                     f"<b>Active Unresolved:</b> {unresolved}<br>"
                     f"<b>Daily Fix Rate:</b> {fix_rate:.1f}%</p>"
                     f"<p>Report saved to: <code>{md_path}</code></p>")
        dlg.setDetailedText(content)
        dlg.exec_()
