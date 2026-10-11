"""
PRUBETH IDE — Visual Activity Bar Widget
Provides a vertical 48px navigation rail for PRUBETH Horizon IDE.
"""
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QButtonGroup, QFrame, QLabel, QSizePolicy, QToolTip
)
from PyQt5.QtGui import QFont, QCursor


class ActivityBarButton(QPushButton):
    """Custom icon button for the Horizon visual Activity Bar."""
    def __init__(self, icon_text: str, tooltip: str, parent=None):
        super().__init__(icon_text, parent)
        self.setToolTip(tooltip)
        self.setFixedSize(44, 44)
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFont(QFont("Segoe UI Emoji", 14))
        self._update_style(False)

    def _update_style(self, checked: bool):
        if checked:
            self.setStyleSheet("""
                QPushButton {
                    background: #252934;
                    color: #9485FF;
                    border: none;
                    border-left: 3px solid #9485FF;
                    border-radius: 0px;
                    padding-left: 2px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #A5ACBB;
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0px;
                    padding-left: 2px;
                }
                QPushButton:hover {
                    background: #1D2028;
                    color: #E8EAF0;
                }
            """)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style(checked)


class ActivityBarWidget(QWidget):
    """
    Vertical 48px activity icon bar for switching primary sidebars and quick mod access.
    """
    view_changed = pyqtSignal(int)         # Emits index of selected view
    settings_requested = pyqtSignal()     # Emits when settings gear clicked
    accounts_requested = pyqtSignal()     # Emits when account avatar clicked
    toggle_requested = pyqtSignal()       # Emits to toggle/collapse sidebar

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(48)
        self._current_index = 0
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("background: #111318; border-right: 1px solid #343A49;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 6, 2, 6)
        layout.setSpacing(4)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # Primary Views
        self.btn_explorer = ActivityBarButton("📁", "Explorer (Ctrl+Shift+E)", self)
        self.btn_search = ActivityBarButton("🔍", "Search & Grep (Ctrl+Shift+F)", self)
        self.btn_git = ActivityBarButton("🌿", "Source Control (Ctrl+Shift+G)", self)
        self.btn_tests = ActivityBarButton("🧪", "Testing & QA Suite (Ctrl+Shift+T)", self)
        self.btn_checkpoints = ActivityBarButton("🛡️", "Checkpoints & Rollbacks", self)
        self.btn_models = ActivityBarButton("⚡", "Local Models & GPU Hub (CUDA)", self)
        self.btn_plugins = ActivityBarButton("🧩", "Extensions & MCP Marketplace", self)

        views = [
            (self.btn_explorer, 0),
            (self.btn_search, 1),
            (self.btn_git, 2),
            (self.btn_tests, 3),
            (self.btn_checkpoints, 4),
            (self.btn_models, 5),
            (self.btn_plugins, 6),
        ]

        for btn, idx in views:
            self.button_group.addButton(btn, idx)
            layout.addWidget(btn)
            btn.clicked.connect(lambda checked, i=idx: self._on_button_clicked(i))

        self.btn_explorer.setChecked(True)

        layout.addStretch(1)

        # Bottom Actions (Accounts & Settings)
        self.btn_accounts = ActivityBarButton("👤", "Accounts & DPAPI Key Vault", self)
        self.btn_accounts.setCheckable(False)
        self.btn_accounts.clicked.connect(self.accounts_requested.emit)
        layout.addWidget(self.btn_accounts)

        self.btn_settings = ActivityBarButton("⚙️", "Settings & Subsystem Mod Hub (Ctrl+,)", self)
        self.btn_settings.setCheckable(False)
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        layout.addWidget(self.btn_settings)

    def _on_button_clicked(self, index: int):
        if self._current_index == index:
            # Clicking active icon toggles/collapses sidebar like VS Code
            self.toggle_requested.emit()
        else:
            self._current_index = index
            self.view_changed.emit(index)

    def set_active_index(self, index: int):
        self._current_index = index
        btn = self.button_group.button(index)
        if btn:
            btn.setChecked(True)
