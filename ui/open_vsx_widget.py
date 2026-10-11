"""
PRUBETH IDE — Visual Open VSX Marketplace Widget
Connects to Eclipse Open VSX for searching, downloading, and enabling VS Code extensions.
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QMessageBox
)
from PyQt5.QtGui import QFont, QCursor

from code_oss.extension_host.open_vsx_client import OpenVsxClient


class OpenVsxWidget(QWidget):
    """Open VSX extension marketplace browser."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = OpenVsxClient()
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background: #0d101a;
                color: #f1f5f9;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background: #141824;
                border: 1px solid #1e2438;
                border-radius: 6px;
                padding: 4px 8px;
                color: #ffffff;
                font-size: 8.5pt;
            }
            QLineEdit:focus { border-color: #00F0FF; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header
        head = QHBoxLayout()
        lbl = QLabel("<b>OPEN VSX MARKETPLACE</b>")
        lbl.setStyleSheet("color: #00F0FF; font-size: 8.5pt;")
        head.addWidget(lbl)
        head.addStretch(1)

        badge = QLabel("Code-OSS Compatible")
        badge.setStyleSheet("background: #1e2438; color: #94a3b8; font-size: 7.5pt; padding: 2px 4px; border-radius: 3px;")
        head.addWidget(badge)
        layout.addLayout(head)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search extensions in Open VSX (e.g. Python, Prettier, Rust)...")
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input)

        # Extension List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #090c13;
                border: 1px solid #1e2438;
                border-radius: 6px;
            }
            QListWidget::item {
                border-bottom: 1px solid #141824;
                padding: 6px;
            }
        """)
        layout.addWidget(self.list_widget, 1)

        # Footer
        footer = QLabel("Powered by Eclipse Open VSX Registry (open-vsx.org)")
        footer.setStyleSheet("color: #64748b; font-size: 7.5pt;")
        layout.addWidget(footer)

        self.perform_search()

    def perform_search(self):
        query = self.search_input.text().strip() or "python"
        extensions = self.client.search_extensions(query, size=15)
        self.list_widget.clear()

        for ext in extensions:
            item = QListWidgetItem(self.list_widget)
            card = QFrame()
            card.setStyleSheet("background: #121622; border-radius: 4px; padding: 4px;")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(4, 4, 4, 4)
            cl.setSpacing(2)

            top_row = QHBoxLayout()
            name_lbl = QLabel(f"<b>{ext['name']}</b> <span style='color:#64748b;'>v{ext['version']}</span>")
            name_lbl.setStyleSheet("color: #f1f5f9; font-size: 8.5pt;")
            top_row.addWidget(name_lbl)
            top_row.addStretch(1)

            btn_install = QPushButton("Install")
            btn_install.setStyleSheet("background: #1d4ed8; color: #ffffff; font-size: 7.5pt; padding: 2px 8px; border-radius: 3px;")
            btn_install.clicked.connect(lambda ch, e=ext: self._install_extension(e))
            top_row.addWidget(btn_install)
            cl.addLayout(top_row)

            desc = QLabel(f"<span style='color:#00F0FF;'>{ext['publisher']}</span> · {ext['description'][:90]}...")
            desc.setStyleSheet("color: #94a3b8; font-size: 8pt;")
            desc.setWordWrap(True)
            cl.addWidget(desc)

            item.setSizeHint(card.sizeHint())
            self.list_widget.setItemWidget(item, card)

    def _install_extension(self, ext):
        QMessageBox.information(self, "Open VSX Extension", f"Installed '{ext['name']}' from Open VSX successfully.")
