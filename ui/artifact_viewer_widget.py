"""
PRUBETH IDE — Interactive Artifact & Review Inspector
Provides human-in-the-loop oversight to resolve the HCI Trust Gap:
1. Implementation Plans & Checklists: Structured roadmaps inspectable before execution.
2. Interactive Diffs: Unified visual hunks highlighting modifications.
3. Google Docs-style Inline Commenting: Highlights lines within an artifact to add mid-flight
   feedback, steering agent execution without stopping or resetting the process.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QListWidget, QListWidgetItem, QSplitter, QSpinBox, QMessageBox,
    QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from horizon_engine.artifacts import ArtifactEngine, Artifact, ArtifactComment, ArtifactType


class ArtifactViewerWidget(QWidget):
    """
    Inspector widget for reviewing subagent artifacts and leaving mid-flight comments.
    """
    commentAdded = pyqtSignal(str, str)  # artifact_id, comment_text

    def __init__(self, artifact_engine: ArtifactEngine, parent=None):
        super().__init__(parent)
        self.artifact_engine = artifact_engine
        self.current_artifact: Artifact = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        self.title_label = QLabel("ARTIFACT INSPECTOR // VERIFIABLE DELIVERABLES")
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.title_label.setStyleSheet("color: #00F0FF;")
        header.addWidget(self.title_label)

        header.addStretch()

        self.refresh_btn = QPushButton("↻ Refresh Artifacts")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #161722; color: #FFFFFF; border: 1px solid #282A3A;
                border-radius: 4px; padding: 4px 10px; font-size: 11px;
            }
            QPushButton:hover { border-color: #00F0FF; color: #00F0FF; }
        """)
        self.refresh_btn.clicked.connect(self.reload_artifacts_list)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Main Splitter: Left (Artifacts List), Middle (Content Viewer), Right (Google Docs Comments)
        splitter = QSplitter(Qt.Horizontal)

        # Left: Artifacts Selector
        left_box = QWidget()
        left_lay = QVBoxLayout(left_box)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lbl = QLabel("DELIVERABLES:")
        left_lbl.setStyleSheet("color: #8F93A2; font-size: 10px; font-weight: bold;")
        left_lay.addWidget(left_lbl)

        self.artifacts_list = QListWidget()
        self.artifacts_list.setStyleSheet("""
            QListWidget {
                background-color: #111218; border: 1px solid #1E202C;
                color: #FFFFFF; border-radius: 4px;
            }
            QListWidget::item:selected { background-color: #1F2233; color: #00F0FF; }
        """)
        self.artifacts_list.currentRowChanged.connect(self._on_artifact_selected)
        left_lay.addWidget(self.artifacts_list)
        splitter.addWidget(left_box)

        # Middle: Content View (Markdown Plan or Unified Diff)
        mid_box = QWidget()
        mid_lay = QVBoxLayout(mid_box)
        mid_lay.setContentsMargins(0, 0, 0, 0)
        self.content_header = QLabel("ARTIFACT CONTENT:")
        self.content_header.setStyleSheet("color: #8F93A2; font-size: 10px; font-weight: bold;")
        mid_lay.addWidget(self.content_header)

        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)
        self.content_view.setStyleSheet("""
            QTextEdit {
                background-color: #0D0E13; color: #E0E0E0; border: 1px solid #1E202C;
                font-family: 'Consolas', monospace; font-size: 11px; border-radius: 4px;
            }
        """)
        mid_lay.addWidget(self.content_view)
        splitter.addWidget(mid_box)

        # Right: Google Docs-Style Inline Commenting Sidebar
        right_box = QWidget()
        right_lay = QVBoxLayout(right_box)
        right_lay.setContentsMargins(0, 0, 0, 0)

        comm_lbl = QLabel("INLINE COMMENTING LOOP (MID-FLIGHT STEERING):")
        comm_lbl.setStyleSheet("color: #00FF88; font-size: 10px; font-weight: bold;")
        right_lay.addWidget(comm_lbl)

        self.comments_list = QListWidget()
        self.comments_list.setStyleSheet("""
            QListWidget {
                background-color: #111218; border: 1px solid #1E202C;
                color: #FFFFFF; font-size: 11px; border-radius: 4px;
            }
        """)
        right_lay.addWidget(self.comments_list)

        # Add comment inputs
        comm_input_box = QFrame()
        comm_input_box.setStyleSheet("background-color: #161722; border: 1px solid #1E202C; border-radius: 4px; padding: 6px;")
        in_lay = QVBoxLayout(comm_input_box)
        in_lay.setContentsMargins(6, 6, 6, 6)
        in_lay.setSpacing(6)

        line_row = QHBoxLayout()
        line_row.addWidget(QLabel("Lines:"))
        self.start_line_spin = QSpinBox()
        self.start_line_spin.setRange(1, 9999)
        self.start_line_spin.setValue(1)
        line_row.addWidget(self.start_line_spin)
        line_row.addWidget(QLabel("to"))
        self.end_line_spin = QSpinBox()
        self.end_line_spin.setRange(1, 9999)
        self.end_line_spin.setValue(1)
        line_row.addWidget(self.end_line_spin)
        in_lay.addLayout(line_row)

        self.new_comment_text = QTextEdit()
        self.new_comment_text.setPlaceholderText("Highlight feedback or steering instructions for the subagent...")
        self.new_comment_text.setMaximumHeight(60)
        self.new_comment_text.setStyleSheet("background-color: #0D0E13; color: #FFF; border: 1px solid #282A3A;")
        in_lay.addWidget(self.new_comment_text)

        self.add_comment_btn = QPushButton("💬 Add Inline Feedback")
        self.add_comment_btn.setStyleSheet("""
            QPushButton {
                background-color: #1F2233; color: #00F0FF; border: 1px solid #00F0FF;
                border-radius: 4px; padding: 6px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background-color: #00F0FF; color: #0B0D13; }
        """)
        self.add_comment_btn.clicked.connect(self._add_comment)
        in_lay.addWidget(self.add_comment_btn)

        right_lay.addWidget(comm_input_box)
        splitter.addWidget(right_box)

        splitter.setSizes([180, 420, 260])
        layout.addWidget(splitter)

        self.reload_artifacts_list()

    def reload_artifacts_list(self):
        self.artifacts_list.clear()
        for art_id, art in self.artifact_engine.artifacts.items():
            item = QListWidgetItem(f"[{art.artifact_type.value[:4]}] {art.title}")
            item.setData(Qt.UserRole, art_id)
            self.artifacts_list.addItem(item)

        if self.artifacts_list.count() > 0:
            self.artifacts_list.setCurrentRow(0)

    def _on_artifact_selected(self, row: int):
        if row < 0:
            return
        item = self.artifacts_list.item(row)
        if not item:
            return
        art_id = item.data(Qt.UserRole)
        art = self.artifact_engine.artifacts.get(art_id)
        if not art:
            return

        self.current_artifact = art
        self.content_header.setText(f"CONTENT: {art.title} ({art.file_name})")
        self.content_view.setPlainText(art.content or "(Empty artifact content)")

        self._refresh_comments_list()

    def _refresh_comments_list(self):
        self.comments_list.clear()
        if not self.current_artifact:
            return

        for c in self.current_artifact.comments:
            status = "✓ [RESOLVED]" if c.resolved else "● [ACTIVE]"
            txt = f"{status} L{c.line_start}-L{c.line_end} ({c.author}):\n{c.content}"
            item = QListWidgetItem(txt)
            if c.resolved:
                item.setForeground(QColor("#666666"))
            else:
                item.setForeground(QColor("#00FF88"))
            self.comments_list.addItem(item)

    def _add_comment(self):
        if not self.current_artifact:
            QMessageBox.warning(self, "No Artifact", "Select an artifact from the list first.")
            return

        content = self.new_comment_text.toPlainText().strip()
        if not content:
            return

        start_l = self.start_line_spin.value()
        end_l = max(start_l, self.end_line_spin.value())

        self.artifact_engine.add_inline_comment(
            artifact_id=self.current_artifact.artifact_id,
            line_start=start_l,
            line_end=end_l,
            content=content,
            author="developer"
        )
        self.new_comment_text.clear()
        self._refresh_comments_list()
        self.commentAdded.emit(self.current_artifact.artifact_id, content)
