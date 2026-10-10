"""
SUKHI IDE — Transactional Checkpoints UI Widget
Provides visual timeline of checkpoints, modified files diffs, and atomic rollback triggers.
"""
import time
from typing import Optional
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QSplitter, QPlainTextEdit
)
from workspace.checkpoints import CheckpointManager, SessionCheckpoint


class CheckpointsWidget(QWidget):
    """Visual panel for inspecting and rolling back agent workspace checkpoints."""
    checkpoint_rolled_back = pyqtSignal(str)
    file_open_requested = pyqtSignal(str)

    def __init__(self, checkpoint_manager: CheckpointManager, parent=None):
        super().__init__(parent)
        self.mgr = checkpoint_manager
        self.selected_checkpoint_id: Optional[str] = None

        self._build_ui()
        self.refresh_checkpoints()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header bar
        head = QHBoxLayout()
        title = QLabel("<b>🛡️ Workspace Checkpoints</b>")
        title.setStyleSheet("color: #edf4ff; font-size: 9.5pt;")
        head.addWidget(title)
        head.addStretch()

        btn_new = QPushButton("＋ New")
        btn_new.setToolTip("Create a manual restore checkpoint")
        btn_new.setStyleSheet("padding: 3px 8px; font-size: 8.5pt;")
        btn_new.clicked.connect(self._create_manual_checkpoint)
        head.addWidget(btn_new)

        btn_refresh = QPushButton("⟳")
        btn_refresh.setToolTip("Refresh checkpoints timeline")
        btn_refresh.setStyleSheet("padding: 3px 8px; font-size: 8.5pt;")
        btn_refresh.clicked.connect(self.refresh_checkpoints)
        head.addWidget(btn_refresh)
        layout.addLayout(head)

        splitter = QSplitter(Qt.Vertical)

        # Checkpoints list
        self.list_checkpoints = QListWidget()
        self.list_checkpoints.setStyleSheet("""
            QListWidget {
                background: #080c14;
                border: 1px solid #1a2230;
                border-radius: 4px;
                color: #dce7fa;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #101622;
            }
            QListWidget::item:selected {
                background: #192333;
                color: #5aa7ff;
            }
        """)
        self.list_checkpoints.itemClicked.connect(self._on_checkpoint_clicked)
        splitter.addWidget(self.list_checkpoints)

        # Details / File changes
        details_widget = QWidget()
        det_layout = QVBoxLayout(details_widget)
        det_layout.setContentsMargins(0, 4, 0, 0)
        det_layout.setSpacing(4)

        det_lbl = QLabel("<b>Touched Files:</b>")
        det_lbl.setStyleSheet("color: #94A3B8; font-size: 8.5pt;")
        det_layout.addWidget(det_lbl)

        self.tree_files = QTreeWidget()
        self.tree_files.setHeaderLabels(["File", "Action", "Status"])
        self.tree_files.setStyleSheet("""
            QTreeWidget {
                background: #080c14;
                border: 1px solid #1a2230;
                border-radius: 4px;
                color: #dce7fa;
            }
            QTreeWidget::item { padding: 4px; }
        """)
        self.tree_files.itemDoubleClicked.connect(self._on_file_double_clicked)
        det_layout.addWidget(self.tree_files, 1)

        # Rollback button row
        self.btn_rollback = QPushButton("↩ Rollback to This Checkpoint")
        self.btn_rollback.setEnabled(False)
        self.btn_rollback.setStyleSheet("""
            QPushButton {
                background: #7f1d1d;
                border: 1px solid #991b1b;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #991b1b;
                border-color: #ef4444;
            }
            QPushButton:disabled {
                background: #1e293b;
                border-color: #334155;
                color: #64748b;
            }
        """)
        self.btn_rollback.clicked.connect(self._on_rollback_clicked)
        det_layout.addWidget(self.btn_rollback)

        splitter.addWidget(details_widget)
        splitter.setSizes([140, 200])
        layout.addWidget(splitter, 1)

    def refresh_checkpoints(self):
        """Reloads all checkpoints from CheckpointManager."""
        self.list_checkpoints.clear()
        self.tree_files.clear()
        self.btn_rollback.setEnabled(False)
        self.selected_checkpoint_id = None

        checkpoints = self.mgr.list_checkpoints()
        for chk in reversed(checkpoints):
            t_str = time.strftime("%H:%M:%S", time.localtime(chk.get("created_at", time.time())))
            status_symbol = "⚪ Rolled Back" if chk.get("is_rolled_back") else "🟢 Active"
            count = chk.get("file_count", chk.get("files_count", 0))
            desc = chk.get("description", "Checkpoint")
            c_id = chk.get("checkpoint_id", chk.get("id", ""))

            item = QListWidgetItem(f"[{t_str}] {desc} ({count} files)\n    Status: {status_symbol}")
            item.setData(Qt.UserRole, c_id)
            if chk.get("is_rolled_back"):
                item.setForeground(Qt.gray)
            self.list_checkpoints.addItem(item)

    def _on_checkpoint_clicked(self, item: QListWidgetItem):
        c_id = item.data(Qt.UserRole)
        self.selected_checkpoint_id = c_id
        chk: Optional[SessionCheckpoint] = self.mgr.get_checkpoint(c_id)
        self.tree_files.clear()

        if not chk:
            self.btn_rollback.setEnabled(False)
            return

        self.btn_rollback.setEnabled(not chk.is_rolled_back and len(chk.snapshots) > 0)

        for rel, snap in chk.snapshots.items():
            if not snap.existed_before:
                action = "Created"
            elif snap.post_hash is None or snap.pre_hash == snap.post_hash:
                action = "Unmodified"
            else:
                action = "Modified"

            stat_text = "Clean" if not chk.is_rolled_back else "Rolled Back"
            tree_item = QTreeWidgetItem([rel, action, stat_text])
            tree_item.setData(0, Qt.UserRole, rel)
            self.tree_files.addTopLevelItem(tree_item)

    def _on_file_double_clicked(self, item: QTreeWidgetItem, column: int):
        rel = item.data(0, Qt.UserRole)
        if rel:
            self.file_open_requested.emit(rel)

    def _create_manual_checkpoint(self):
        c_id = self.mgr.begin_checkpoint("Manual User Checkpoint")
        self.refresh_checkpoints()

    def _on_rollback_clicked(self):
        if not self.selected_checkpoint_id:
            return

        chk = self.mgr.get_checkpoint(self.selected_checkpoint_id)
        if not chk:
            return

        file_list = "\n".join(f" - {f}" for f in chk.snapshots.keys())
        reply = QMessageBox.question(
            self,
            "Confirm Transactional Rollback",
            f"Are you sure you want to rollback checkpoint '{chk.description}'?\n\n"
            f"The following files will be atomically reverted:\n{file_list}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.mgr.rollback_checkpoint(self.selected_checkpoint_id)
            if success:
                QMessageBox.information(
                    self,
                    "Rollback Successful",
                    f"Successfully reverted all modifications made in checkpoint '{self.selected_checkpoint_id}'."
                )
                self.checkpoint_rolled_back.emit(self.selected_checkpoint_id)
                self.refresh_checkpoints()
            else:
                QMessageBox.critical(
                    self,
                    "Rollback Failed",
                    f"Failed to cleanly rollback checkpoint '{self.selected_checkpoint_id}'."
                )
