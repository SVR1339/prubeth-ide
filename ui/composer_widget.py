"""
PRUBETH IDE — Visual Composer Widget (Cursor & Windsurf Style)
Provides multi-file agentic code generation with inline diff inspection, atomic accept, and rollback.
"""
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QSplitter, QFrame, QMessageBox
)
from PyQt5.QtGui import QFont, QCursor

from code_oss.composer.engine import ComposerEngine, FileDiffPlan


class ComposerWidget(QWidget):
    """Cursor & Windsurf style multi-file Composer panel."""
    plan_generated = pyqtSignal(list)
    changes_applied = pyqtSignal(dict)
    rollback_requested = pyqtSignal()

    def __init__(self, workspace_root: Path, checkpoint_manager=None, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root).resolve()
        self.engine = ComposerEngine(self.workspace_root, checkpoint_manager)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background: #0b0e17;
                color: #f1f5f9;
                font-family: 'Segoe UI', sans-serif;
            }
            QFrame.card {
                background: #141824;
                border: 1px solid #1e2438;
                border-radius: 8px;
            }
            QPushButton {
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 8.5pt;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        icon = QLabel("⚡")
        icon.setFont(QFont("Segoe UI Emoji", 14))
        header.addWidget(icon)

        title = QLabel("<b>PRUBETH COMPOSER</b> · Code-OSS Agent Core")
        title.setStyleSheet("color: #00F0FF; font-size: 9.5pt;")
        header.addWidget(title)
        header.addStretch(1)

        model_badge = QLabel("Model: redsage-8b [CUDA]")
        model_badge.setStyleSheet("background: #064e3b; color: #34d399; font-size: 8pt; padding: 2px 6px; border-radius: 4px; font-family: monospace;")
        header.addWidget(model_badge)
        layout.addLayout(header)

        # Context Chips (Cursor style @Codebase, @Files, @Terminal, @Git)
        chips = QHBoxLayout()
        chips.setSpacing(4)
        for tag in ["@Codebase", "@Files", "@Terminal", "@Git"]:
            btn = QPushButton(tag, self)
            btn.setStyleSheet("""
                QPushButton {
                    background: #181d2b;
                    color: #8fa0b8;
                    border: 1px solid #232a3d;
                    padding: 2px 8px;
                    font-size: 7.5pt;
                    font-family: monospace;
                }
                QPushButton:hover { color: #00F0FF; border-color: #00F0FF; }
            """)
            btn.clicked.connect(lambda ch, t=tag: self._add_chip_to_prompt(t))
            chips.addWidget(btn)
        chips.addStretch(1)
        layout.addLayout(chips)

        # Instruction input
        self.prompt_input = QPlainTextEdit(self)
        self.prompt_input.setPlaceholderText("Describe multi-file feature or refactoring (e.g. 'Add new settings mod and wire into router')...")
        self.prompt_input.setMaximumHeight(80)
        self.prompt_input.setStyleSheet("""
            QPlainTextEdit {
                background: #121622;
                border: 1px solid #1e2438;
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 9pt;
                padding: 6px;
            }
            QPlainTextEdit:focus { border-color: #00F0FF; }
        """)
        layout.addWidget(self.prompt_input)

        # Generate / Action bar
        act_bar = QHBoxLayout()
        self.btn_generate = QPushButton("⚡ Generate Multi-File Plan", self)
        self.btn_generate.setStyleSheet("background: #1d4ed8; color: #ffffff;")
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        act_bar.addWidget(self.btn_generate)
        act_bar.addStretch(1)
        layout.addLayout(act_bar)

        # Multi-file change tree and diff preview splitter
        split = QSplitter(Qt.Vertical)

        # Files Tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Planned File", "+Add", "-Del"])
        self.file_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.file_tree.setMaximumHeight(140)
        self.file_tree.setStyleSheet("""
            QTreeWidget {
                background: #0d101a;
                color: #c9d1d9;
                border: 1px solid #1e2438;
                border-radius: 6px;
                font-family: monospace;
                font-size: 8.5pt;
            }
        """)
        self.file_tree.itemClicked.connect(self._on_file_selected)
        split.addWidget(self.file_tree)

        # Unified Diff Preview
        self.diff_view = QPlainTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Cascadia Code", 9))
        self.diff_view.setPlaceholderText("Select a file above to inspect planned diff (+additions / -deletions)...")
        self.diff_view.setStyleSheet("""
            QPlainTextEdit {
                background: #090b12;
                color: #c9d1d9;
                border: 1px solid #1e2438;
                border-radius: 6px;
            }
        """)
        split.addWidget(self.diff_view)

        layout.addWidget(split, 1)

        # Commit & Rollback Bottom Bar
        footer = QHBoxLayout()
        self.btn_accept = QPushButton("✓ Accept All (Ctrl+Enter)", self)
        self.btn_accept.setStyleSheet("background: #1D3D2A; color: #70D6A0; border: 1px solid #285A3E; border-radius: 4px; padding: 5px 12px; font-weight: 600;")
        self.btn_accept.clicked.connect(self._on_accept_clicked)
        footer.addWidget(self.btn_accept)

        self.btn_rollback = QPushButton("✕ Reject / Rollback", self)
        self.btn_rollback.setStyleSheet("background: #381E24; color: #FF7D86; border: 1px solid #5A2732; border-radius: 4px; padding: 5px 12px; font-weight: 600;")
        self.btn_rollback.clicked.connect(self._on_rollback_clicked)
        footer.addWidget(self.btn_rollback)

        footer.addStretch(1)
        self.status_lbl = QLabel("Ready for prompt")
        self.status_lbl.setStyleSheet("color: #64748b; font-size: 8pt;")
        footer.addWidget(self.status_lbl)
        layout.addLayout(footer)

    def _add_chip_to_prompt(self, chip: str):
        self.prompt_input.insertPlainText(f"{chip} ")
        self.prompt_input.setFocus()

    def set_ai_worker_factory(self, factory):
        """Inject a callable factory(prompt, model) → AIWorker from Studio."""
        self._ai_worker_factory = factory

    def _on_generate_clicked(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Composer", "Please enter an instruction or query.")
            return

        factory = getattr(self, "_ai_worker_factory", None)
        if factory is None:
            # Fallback: show stub plan so UI is still useful without AI wiring
            self.status_lbl.setText("⚠️  AI not connected — stub plan shown")
            self.engine.plan_file_change(
                "ui/settings_dialog.py",
                "# Stub: connect AI worker via set_ai_worker_factory\n"
            )
            self.refresh_plan_ui()
            return

        # Build a composer-style system prompt
        system = (
            "You are PRUBETH Composer, an agentic code editor. "
            "The user will describe a code change. "
            "Reply with the FULL updated content of each file you would modify, "
            "prefixed with: FILE: <relative_path>\\n```<lang>\\n<content>\\n```\\n. "
            "Do not add explanations outside the file blocks."
        )
        full_prompt = f"{system}\n\nUSER INSTRUCTION:\n{prompt}"

        self.status_lbl.setText("⏳ Generating with AI…")
        self.btn_generate = self.findChild(type(self.btn_accept), "btn_generate") or None

        worker = factory(full_prompt)
        worker.chunk_received.connect(self._on_ai_chunk)
        worker.finished.connect(self._on_ai_done)
        worker.error_occurred.connect(self._on_ai_error)
        self._ai_response_buf = ""
        self._ai_worker = worker
        worker.start()

    def _on_ai_chunk(self, chunk: str):
        self._ai_response_buf += chunk
        self.status_lbl.setText(f"⏳ Streaming… ({len(self._ai_response_buf)} chars)")

    def _on_ai_done(self):
        try:
            plans = self.engine.parse_composer_response(self._ai_response_buf)
            if plans:
                self.refresh_plan_ui()
                self.status_lbl.setText(f"✓ {len(plans)} file(s) staged")
            else:
                self.status_lbl.setText("⚠️  No file blocks found in AI response")
                self.diff_view.setPlainText(self._ai_response_buf)
        except Exception as exc:
            self.status_lbl.setText(f"⚠️  Parse error: {exc}")
            self.diff_view.setPlainText(self._ai_response_buf)

    def _on_ai_error(self, msg: str):
        self.status_lbl.setText(f"✗ AI error: {msg}")

    def refresh_plan_ui(self):
        self.file_tree.clear()
        for rel_path, plan in self.engine.current_plan.items():
            item = QTreeWidgetItem(self.file_tree, [rel_path, f"+{plan.additions_count}", f"-{plan.deletions_count}"])
            item.setForeground(1, Qt.green)
            item.setForeground(2, Qt.red)
        if self.engine.current_plan:
            first_path = list(self.engine.current_plan.keys())[0]
            self.diff_view.setPlainText(self.engine.current_plan[first_path].diff_unified)

    def _on_file_selected(self, item, col):
        path = item.text(0)
        if path in self.engine.current_plan:
            self.diff_view.setPlainText(self.engine.current_plan[path].diff_unified)

    def _on_accept_clicked(self):
        res = self.engine.apply_all("Composer atomic apply")
        if res.get("success"):
            self.status_lbl.setText(f"✓ Committed {res['file_count']} file(s)")
            self.changes_applied.emit(res)
            QMessageBox.information(self, "Composer", f"Successfully applied changes to {res['file_count']} files!")
        else:
            QMessageBox.warning(self, "Composer Error", res.get("error", "Failed to apply."))

    def _on_rollback_clicked(self):
        res = self.engine.rollback()
        self.refresh_plan_ui()
        self.diff_view.clear()
        self.status_lbl.setText("Rolled back changes")
        self.rollback_requested.emit()
