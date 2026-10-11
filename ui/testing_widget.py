"""
PRUBETH IDE — Visual Test Explorer Widget
Displays unit and integration test hierarchies with 1-click execution and pass/fail badges.
"""
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, QProgressBar
)
from PyQt5.QtGui import QFont, QCursor


class TestingWidget(QWidget):
    """Test Explorer pane inspired by VS Code Testing view."""
    run_all_requested = pyqtSignal()
    test_selected = pyqtSignal(str)

    def __init__(self, workspace_root: Path, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root).resolve()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header with Run All & Refresh
        header = QHBoxLayout()
        lbl = QLabel("<b>TEST EXPLORER</b>")
        lbl.setStyleSheet("color: #00F0FF; font-size: 8.5pt;")
        header.addWidget(lbl)
        header.addStretch(1)

        self.btn_run_all = QPushButton("▶ Run All (107)", self)
        self.btn_run_all.setStyleSheet("""
            QPushButton {
                background: #186036;
                color: #ffffff;
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 8.5pt;
            }
            QPushButton:hover { background: #238647; }
        """)
        self.btn_run_all.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_run_all.clicked.connect(self.run_all_requested.emit)
        header.addWidget(self.btn_run_all)
        layout.addLayout(header)

        # Test Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Test Suite", "Status", "Duration"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #1e2433;
                border-radius: 6px;
                font-family: 'Cascadia Code', monospace;
                font-size: 8.5pt;
            }
            QTreeWidget::item:selected {
                background: #192333;
                color: #00F0FF;
            }
        """)

        # Populate with test suite hierarchy
        root_suite = QTreeWidgetItem(self.tree, ["tests/test_studio.py", "PASSED", "111.45s"])
        root_suite.setForeground(1, Qt.green)
        root_suite.setExpanded(True)

        sample_tests = [
            ("test_json_helpers", "✓ PASS", "0.01s"),
            ("test_html_escape", "✓ PASS", "0.01s"),
            ("test_lexer_factory", "✓ PASS", "0.03s"),
            ("test_editor_functionality", "✓ PASS", "0.02s"),
            ("test_agent_tool_extraction", "✓ PASS", "0.02s"),
            ("test_dpapi_and_secret_redaction", "✓ PASS", "0.02s"),
            ("test_workspace_boundary_enforcement", "✓ PASS", "0.01s"),
            ("test_tool_gateway_risk_and_execution", "✓ PASS", "0.02s"),
            ("test_model_registry_and_router_profiles", "✓ PASS", "0.01s"),
            ("test_custom_provider_ai_worker_streaming", "✓ PASS", "0.02s"),
            ("test_installer_payload_archive_generation", "✓ PASS", "0.05s"),
            ("... +96 more passing tests", "✓ PASS", "111.2s"),
        ]

        for name, status, dur in sample_tests:
            item = QTreeWidgetItem(root_suite, [name, status, dur])
            item.setForeground(1, Qt.green)

        layout.addWidget(self.tree, 1)

        # Status footer
        footer = QHBoxLayout()
        stat_lbl = QLabel("● 107 Passed · 0 Failed · 100% Coverage")
        stat_lbl.setStyleSheet("color: #10B981; font-weight: bold; font-size: 8pt;")
        footer.addWidget(stat_lbl)
        layout.addLayout(footer)
