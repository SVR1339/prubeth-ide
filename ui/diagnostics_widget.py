"""
SUKHI IDE — Diagnostics & Problems UI Widget
Displays LSP syntax and semantic diagnostics across the project workspace,
with interactive filtering and code navigation.
"""
from typing import List, Dict, Any, Optional
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QTreeWidget, QTreeWidgetItem, QPushButton
)


SEVERITY_MAP = {
    1: ("❌ Error", "#EF4444"),
    2: ("⚠️ Warning", "#F59E0B"),
    3: ("ℹ️ Info", "#38BDF8"),
    4: ("💡 Hint", "#94A3B8"),
}


class DiagnosticsWidget(QWidget):
    """Problems & Diagnostics panel showing LSP compiler and linter errors/warnings."""
    navigate_to_source = pyqtSignal(str, int, int)  # file_path, line, col

    def __init__(self, parent=None):
        super().__init__(parent)
        self._diagnostics_by_uri: Dict[str, List[Dict[str, Any]]] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Filter bar
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter problems by description or symbol...")
        self.search_input.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.search_input, 1)

        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["All Severities", "Errors Only", "Warnings & Errors", "Infos & Hints"])
        self.severity_combo.currentTextChanged.connect(self._apply_filter)
        filter_row.addWidget(self.severity_combo)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.clear_diagnostics)
        filter_row.addWidget(btn_clear)
        layout.addLayout(filter_row)

        # Problems Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Severity", "Message", "File", "Line", "Source"])
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: #080c14;
                border: 1px solid #1a2230;
                border-radius: 4px;
                color: #dce7fa;
            }
            QTreeWidget::item { padding: 4px; }
            QTreeWidget::item:selected { background: #192333; color: #5aa7ff; }
        """)
        self.tree.setColumnWidth(0, 100)
        self.tree.setColumnWidth(1, 380)
        self.tree.setColumnWidth(2, 160)
        self.tree.setColumnWidth(3, 70)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree, 1)

        # Status summary bar
        self.lbl_summary = QLabel("0 Errors, 0 Warnings")
        self.lbl_summary.setStyleSheet("color: #94A3B8; font-size: 8.5pt;")
        layout.addWidget(self.lbl_summary)

    def update_diagnostics(self, uri: str, diagnostics: List[Dict[str, Any]]):
        """Updates the diagnostics for a specific file URI and refreshes the view."""
        self._diagnostics_by_uri[uri] = diagnostics
        self._apply_filter()

    def clear_diagnostics(self):
        """Clears all diagnostics from the view."""
        self._diagnostics_by_uri.clear()
        self._apply_filter()

    def _apply_filter(self):
        self.tree.clear()
        filter_text = self.search_input.text().strip().lower()
        sev_filter = self.severity_combo.currentText()

        total_errs = 0
        total_warns = 0

        for uri, diag_list in self._diagnostics_by_uri.items():
            # Extract readable file path from URI
            file_path = uri
            if file_path.startswith("file:///"):
                file_path = file_path[8:]
            elif file_path.startswith("file://"):
                file_path = file_path[7:]

            for diag in diag_list:
                sev = diag.get("severity", 1)
                if sev == 1:
                    total_errs += 1
                elif sev == 2:
                    total_warns += 1

                # Apply severity filter
                if sev_filter == "Errors Only" and sev != 1:
                    continue
                elif sev_filter == "Warnings & Errors" and sev not in (1, 2):
                    continue
                elif sev_filter == "Infos & Hints" and sev not in (3, 4):
                    continue

                msg = diag.get("message", "")
                source = diag.get("source", "LSP")

                # Apply text search filter
                if filter_text and filter_text not in msg.lower() and filter_text not in file_path.lower():
                    continue

                rng = diag.get("range", {}).get("start", {})
                line = rng.get("line", 0) + 1
                col = rng.get("character", 0) + 1

                sev_label, _ = SEVERITY_MAP.get(sev, ("Problem", "#EF4444"))
                item = QTreeWidgetItem([sev_label, msg, file_path, f"{line}:{col}", source])
                item.setData(0, Qt.UserRole, (file_path, line, col))
                self.tree.addTopLevelItem(item)

        self.lbl_summary.setText(f"{total_errs} Errors, {total_warns} Warnings, {self.tree.topLevelItemCount()} Filtered")

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if data:
            file_path, line, col = data
            self.navigate_to_source.emit(file_path, line, col)
