"""
PRUBETH IDE — Visual Breadcrumb Navigation Bar
Provides path hierarchy and editor action shortcuts above the active document canvas.
"""
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt5.QtGui import QFont, QCursor


class BreadcrumbBarWidget(QWidget):
    """Horizontal bar displaying file path hierarchy and quick actions."""
    run_requested = pyqtSignal()
    quick_edit_requested = pyqtSignal()
    split_requested = pyqtSignal()
    diff_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background: #1D2028;
                border-bottom: 1px solid #343A49;
                color: #A5ACBB;
                font-size: 8.5pt;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #A5ACBB;
                padding: 2px 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #252934;
                color: #E8EAF0;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        # Left: Path segments
        self.path_label = QLabel("heretic-work  ›  ui  ›  settings_dialog.py  ›  SettingsDialog")
        self.path_label.setStyleSheet("color: #A5ACBB; font-family: 'Cascadia Code', monospace; font-size: 8pt;")
        layout.addWidget(self.path_label)

        layout.addStretch(1)

        # Right: Action shortcuts
        self.btn_run = QPushButton("▶ Run (F5)", self)
        self.btn_run.setToolTip("Run active file in terminal")
        self.btn_run.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_run.clicked.connect(self.run_requested.emit)
        layout.addWidget(self.btn_run)

        self.btn_ai = QPushButton("⚡ AI Edit (Ctrl+K)", self)
        self.btn_ai.setStyleSheet("color: #9485FF; font-weight: 600;")
        self.btn_ai.setToolTip("Inline code refactoring and generation")
        self.btn_ai.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_ai.clicked.connect(self.quick_edit_requested.emit)
        layout.addWidget(self.btn_ai)

        self.btn_split = QPushButton("◫ Split Right", self)
        self.btn_split.setToolTip("Split editor canvas side-by-side")
        self.btn_split.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_split.clicked.connect(self.split_requested.emit)
        layout.addWidget(self.btn_split)

    def set_path(self, filepath: str, symbol: str = ""):
        if not filepath:
            self.path_label.setText("Welcome  ›  PRUBETH IDE")
            return
        p = Path(filepath)
        parts = list(p.parts)
        if len(parts) > 3:
            parts = parts[-3:]
        display = "  ›  ".join(parts)
        if symbol:
            display += f"  ›  ⚡ {symbol}"
        self.path_label.setText(display)
