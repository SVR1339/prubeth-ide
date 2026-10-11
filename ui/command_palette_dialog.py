"""
PRUBETH IDE — Global Command Palette (Ctrl+Shift+P)
Pillar 3 & 4: Experience & Design System Governance

Floating modal command palette providing instant fuzzy search, recently used commands,
category badges, shortcut indicators, and safe execution dispatch.
"""

from __future__ import annotations

from typing import Optional, List
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QWidget
)

from ui.design_system import DesignTokens, ComponentStyles
from core.command_registry import CommandRegistry, Command


class CommandPaletteDialog(QDialog):
    """Floating modal command palette for rapid keyboard-driven IDE navigation."""

    def __init__(self, registry: Optional[CommandRegistry] = None, parent=None):
        super().__init__(parent)
        self.registry = registry or CommandRegistry.get_instance()
        self.selected_command: Optional[Command] = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(680, 420)

        self._build_ui()
        self._load_commands()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command or search actions… (e.g. Settings, Autotune, Preset, Diff)")
        self.search_input.setStyleSheet(ComponentStyles.input_field())
        self.search_input.textChanged.connect(self._filter_commands)
        root.addWidget(self.search_input)

        # Command List
        self.command_list = QListWidget()
        self.command_list.itemActivated.connect(self._on_item_activated)
        root.addWidget(self.command_list, 1)

        # Footer shortcut hint
        hint = QLabel("↑/↓ to navigate • Enter to select • Esc to dismiss")
        hint.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")
        root.addWidget(hint)

    def _load_commands(self, query: str = ""):
        self.command_list.clear()
        commands = self.registry.search(query)

        # If no query, show recent first
        if not query:
            recents = self.registry.get_recent_commands()
            recent_ids = {c.command_id for c in recents}
            display_cmds = recents + [c for c in commands if c.command_id not in recent_ids]
        else:
            display_cmds = commands

        for cmd in display_cmds:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, cmd.command_id)

            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(8, 4, 8, 4)

            title_lbl = QLabel(f"[{cmd.category}] {cmd.title}")
            title_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_PRIMARY}; font-weight: 600;")
            layout.addWidget(title_lbl)
            layout.addStretch()

            if cmd.shortcut:
                sc_lbl = QLabel(cmd.shortcut)
                sc_lbl.setStyleSheet(f"""
                    background-color: {DesignTokens.SURFACE_ELEVATED};
                    color: {DesignTokens.ACCENT_CYAN};
                    border: 1px solid {DesignTokens.BORDER_MUTED};
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-size: 10px;
                """)
                layout.addWidget(sc_lbl)

            item.setSizeHint(widget.sizeHint())
            self.command_list.addItem(item)
            self.command_list.setItemWidget(item, widget)

        if self.command_list.count() > 0:
            self.command_list.setCurrentRow(0)

    def _filter_commands(self, text: str):
        self._load_commands(text.strip())

    def _on_item_activated(self, item: QListWidgetItem):
        cid = item.data(Qt.UserRole)
        cmd = self.registry.get(cid)
        if cmd:
            self.selected_command = cmd
            self.accept()
            # Execute command safely
            try:
                self.registry.execute(cmd.command_id)
            except Exception:
                pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Down:
            curr = self.command_list.currentRow()
            if curr < self.command_list.count() - 1:
                self.command_list.setCurrentRow(curr + 1)
        elif event.key() == Qt.Key_Up:
            curr = self.command_list.currentRow()
            if curr > 0:
                self.command_list.setCurrentRow(curr - 1)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            curr_item = self.command_list.currentItem()
            if curr_item:
                self._on_item_activated(curr_item)
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def _apply_styles(self):
        t = DesignTokens
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t.CANVAS_BG};
                border: 2px solid {t.ACCENT_CYAN};
                border-radius: {t.RADIUS_MD};
            }}
            QListWidget {{
                background-color: {t.SURFACE_PANEL};
                border: 1px solid {t.BORDER_SUBTLE};
                border-radius: {t.RADIUS_SM};
            }}
            QListWidget::item:selected {{
                background-color: {t.SURFACE_HOVER};
                border-left: 3px solid {t.ACCENT_CYAN};
            }}
        """)
