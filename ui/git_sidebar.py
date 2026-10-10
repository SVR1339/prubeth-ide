"""
SUKHI IDE — Visual Git Sidebar Widget
Presents branch status, staged/unstaged changes, and commit composer.
"""
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QPlainTextEdit, QMessageBox, QHeaderView
)
from source_control.git_service import GitService, GitStatus


class GitSidebarWidget(QWidget):
    """Visual Git Source Control sidebar pane."""

    file_diff_requested = pyqtSignal(str, bool)  # file_path, is_staged

    def __init__(self, workspace_root: Path, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root).resolve()
        self.git_service = GitService(self.workspace_root)

        self.setWindowTitle("Source Control")
        self._init_ui()
        self.refresh_status()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # 1. Header with Branch name & Refresh button
        header_layout = QHBoxLayout()
        self.branch_label = QLabel("Branch: --")
        self.branch_label.setStyleSheet("font-weight: bold; color: #8ab4f8;")
        header_layout.addWidget(self.branch_label, 1)

        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setToolTip("Refresh Git Status")
        self.refresh_btn.clicked.connect(self.refresh_status)
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)

        # 2. Changes Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File", "Status"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: 'Cascadia Code', Consolas, monospace;
                font-size: 9pt;
            }
            QTreeWidget::item:selected {
                background: #1f2937;
                color: #ffffff;
            }
        """)
        layout.addWidget(self.tree, 1)

        # Action Buttons Layout (Stage All / Unstage All)
        stage_actions = QHBoxLayout()
        self.stage_all_btn = QPushButton("+ Stage All")
        self.stage_all_btn.clicked.connect(self._on_stage_all)
        stage_actions.addWidget(self.stage_all_btn)
        layout.addLayout(stage_actions)

        # 3. Commit Message Input
        layout.addWidget(QLabel("Commit Message:"))
        self.commit_msg_input = QPlainTextEdit()
        self.commit_msg_input.setPlaceholderText("Message (Ctrl+Enter to commit)...")
        self.commit_msg_input.setFixedHeight(75)
        self.commit_msg_input.setStyleSheet("""
            QPlainTextEdit {
                background: #0d1117;
                color: #ffffff;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: 'Cascadia Code', Consolas, monospace;
            }
        """)
        layout.addWidget(self.commit_msg_input)

        # 4. Commit Button
        self.commit_btn = QPushButton("✓ Commit Changes")
        self.commit_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2ea043; }
            QPushButton:disabled { background: #21262d; color: #8b949e; }
        """)
        self.commit_btn.clicked.connect(self._on_commit)
        layout.addWidget(self.commit_btn)

    def set_workspace(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()
        self.git_service = GitService(self.workspace_root)
        self.refresh_status()

    def refresh_status(self):
        status = self.git_service.get_status()
        if not status.is_repo:
            self.branch_label.setText("Not a Git Repository")
            self.tree.clear()
            self.commit_btn.setEnabled(False)
            return

        self.branch_label.setText(f"Branch: {status.branch}")
        self.tree.clear()

        # Group 1: Staged Changes
        staged_group = QTreeWidgetItem(self.tree, [f"Staged Changes ({len(status.staged)})", ""])
        staged_group.setExpanded(True)
        for chg in status.staged:
            item = QTreeWidgetItem(staged_group, [chg.file_path, chg.status_code])
            item.setData(0, Qt.UserRole, {"file": chg.file_path, "is_staged": True})
            item.setForeground(1, Qt.green)

        # Group 2: Unstaged Changes
        unstaged_group = QTreeWidgetItem(self.tree, [f"Changes ({len(status.unstaged)})", ""])
        unstaged_group.setExpanded(True)
        for chg in status.unstaged:
            item = QTreeWidgetItem(unstaged_group, [chg.file_path, chg.status_code])
            item.setData(0, Qt.UserRole, {"file": chg.file_path, "is_staged": False})
            item.setForeground(1, Qt.yellow)

        # Group 3: Untracked
        if status.untracked:
            untracked_group = QTreeWidgetItem(self.tree, [f"Untracked ({len(status.untracked)})", ""])
            untracked_group.setExpanded(True)
            for path in status.untracked:
                item = QTreeWidgetItem(untracked_group, [path, "?"])
                item.setData(0, Qt.UserRole, {"file": path, "is_staged": False})
                item.setForeground(1, Qt.cyan)

        has_staged = len(status.staged) > 0
        self.commit_btn.setEnabled(has_staged)

    def _on_stage_all(self):
        self.git_service.stage_all()
        self.refresh_status()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if data and isinstance(data, dict):
            file_path = data.get("file")
            is_staged = data.get("is_staged", False)
            if file_path:
                self.file_diff_requested.emit(file_path, is_staged)

    def _on_commit(self):
        msg = self.commit_msg_input.toPlainText().strip()
        if not msg:
            return

        res = self.git_service.commit(msg)
        if res.get("success"):
            self.commit_msg_input.clear()
            self.refresh_status()
        else:
            QMessageBox.warning(self, "Git Commit Failed", res.get("error", "Unknown error."))
