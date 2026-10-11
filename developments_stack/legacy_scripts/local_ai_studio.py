"""
[LEGACY PROTOTYPE] Local AI Studio — Early Desktop IDE Prototype.
NOTE: For the active, production SO NAIVE IDE (v3.0.0 Horizon Edition),
please run: local_ai_studio_pro.py (or run_local_ai_studio_pro.bat / run_ide.bat).
This file is preserved for historical reference and backward compatibility.
"""
import os
import sys
import json
import re
import subprocess
from pathlib import Path

import requests
from PyQt5.QtCore import Qt, QDir, QThread, pyqtSignal, QProcess, QTimer
from PyQt5.QtGui import QFont, QColor, QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QFileSystemModel, QTabWidget, QPlainTextEdit, QTextEdit,
    QLineEdit, QPushButton, QLabel, QFileDialog, QMessageBox, QInputDialog,
    QDialog, QDialogButtonBox, QAction, QToolBar, QStatusBar, QComboBox,
    QListWidget, QListWidgetItem, QDockWidget, QShortcut, QMenu, QProgressBar
)
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

APP_NAME = "Local AI Studio"
OLLAMA_BASE_DEFAULT = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:1.5b"
APP_DIR = Path.home() / ".local_ai_studio"
APP_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = APP_DIR / "settings.json"
HISTORY_FILE = APP_DIR / "history.json"
IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".idea"}
MAX_CONTEXT_CHARS = 24000


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


class AIWorker(QThread):
    succeeded = pyqtSignal(str, object)
    failed = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, base_url, model, messages, purpose, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.messages = messages
        self.purpose = purpose
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.status.emit(f"Connecting to {self.model}…")
            # Non-streaming response in a worker thread: reliable first step,
            # without freezing the Qt UI. Streaming can be added later.
            response = requests.post(
                self.base_url + "/api/chat",
                json={"model": self.model, "messages": self.messages, "stream": False},
                timeout=(8, 300),
            )
            response.raise_for_status()
            if self._cancelled:
                return
            payload = response.json()
            message = payload.get("message", {})
            answer = message.get("content", "").strip()
            if not answer:
                raise RuntimeError("Ollama returned an empty response.")
            self.succeeded.emit(answer, {"purpose": self.purpose, "model": self.model})
        except requests.exceptions.ConnectionError:
            self.failed.emit(f"Cannot connect to Ollama at {self.base_url}.\nStart the Ollama application and verify that the model is installed.")
        except requests.exceptions.Timeout:
            self.failed.emit("Ollama timed out. The model may be loading or the request may be too large. Try a shorter prompt or a smaller context.")
        except requests.RequestException as exc:
            detail = ""
            try:
                detail = exc.response.text[:1000] if exc.response is not None else ""
            except Exception:
                pass
            self.failed.emit(f"Ollama request failed: {exc}\n{detail}")
        except Exception as exc:
            self.failed.emit(str(exc))


class CodeEditor(QsciScintilla):
    def __init__(self, path="", parent=None):
        super().__init__(parent)
        self.file_path = path
        self.setUtf8(True)
        self.setFont(QFont("Cascadia Code", 11))
        self.setMarginsFont(QFont("Cascadia Code", 10))
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginLineNumbers(0, True)
        self.setMarginWidth(0, "00000")
        self.setMarginsBackgroundColor(QColor("#181b24"))
        self.setMarginsForegroundColor(QColor("#70798c"))
        self.setPaper(QColor("#11141b"))
        self.setColor(QColor("#dce3f0"))
        self.setCaretForegroundColor(QColor("#f4f7ff"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#1b2230"))
        self.setSelectionBackgroundColor(QColor("#344c72"))
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setAutoIndent(True)
        self.setIndentationWidth(4)
        self.setIndentationsUseTabs(False)
        self.setTabWidth(4)
        self.setFolding(QsciScintilla.BoxedTreeFoldStyle, 2)
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.setAutoCompletionThreshold(2)
        self.setEdgeMode(QsciScintilla.EdgeLine)
        self.setEdgeColumn(100)
        self.setEdgeColor(QColor("#252c3a"))
        self.setEolMode(QsciScintilla.EolUnix)
        self.setWrapMode(QsciScintilla.WrapNone)
        self.lexer = QsciLexerPython(self)
        self.lexer.setDefaultFont(QFont("Cascadia Code", 11))
        self.lexer.setDefaultPaper(QColor("#11141b"))
        self.lexer.setDefaultColor(QColor("#dce3f0"))
        self.lexer.setColor(QColor("#c792ea"), QsciLexerPython.Keyword)
        self.lexer.setColor(QColor("#ecc48d"), QsciLexerPython.DoubleQuotedString)
        self.lexer.setColor(QColor("#ecc48d"), QsciLexerPython.SingleQuotedString)
        self.lexer.setColor(QColor("#718096"), QsciLexerPython.Comment)
        self.lexer.setColor(QColor("#82aaff"), QsciLexerPython.FunctionMethodName)
        self.lexer.setColor(QColor("#ffcb6b"), QsciLexerPython.ClassName)
        self.lexer.setColor(QColor("#f07178"), QsciLexerPython.Number)
        self.lexer.setPaper(QColor("#11141b"))
        self.setLexer(self.lexer)

    def selected_text(self):
        return self.selectedText().strip()


class ReviewDialog(QDialog):
    def __init__(self, proposed, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review proposed AI changes")
        self.resize(900, 650)
        layout = QVBoxLayout(self)
        label = QLabel("Review the proposed complete file. Apply changes only if they look correct; the file on disk is not modified until you save.")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.text = QPlainTextEdit()
        self.text.setFont(QFont("Cascadia Code", 10))
        self.text.setPlainText(proposed)
        layout.addWidget(self.text)
        buttons = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Apply).setText("Apply to editor")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class LocalAIStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_json(SETTINGS_FILE, {})
        self.base_url = self.settings.get("ollama_url", OLLAMA_BASE_DEFAULT).rstrip("/")
        self.model = self.settings.get("model", DEFAULT_MODEL)
        self.project_root = os.path.abspath(self.settings.get("project_root", os.getcwd()))
        self.history = load_json(HISTORY_FILE, [])
        if not isinstance(self.history, list):
            self.history = []
        self.workers = []
        self.process = None
        self.busy = False
        self.pending_rewrite = False
        self.setWindowTitle(APP_NAME)
        self.resize(1600, 980)
        self.setMinimumSize(1050, 680)
        self._build_ui()
        self._build_menus()
        self._restore_history()
        self.statusBar().showMessage(f"Ready • {self.model} • local Ollama")
        self.check_connection()

    def _build_ui(self):
        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(central)

        toolbar = QToolBar("Main tools")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(toolbar)
        for label, fn in [
            ("New", self.new_file), ("Open", self.open_file_dialog),
            ("Save", self.save_file), ("Save As", self.save_as),
            ("Run Python", self.run_python), ("Search Project", self.search_project),
            ("Explain", self.explain_selection), ("Debug", self.debug_with_ai),
            ("AI Edit", self.ai_rewrite),
        ]:
            act = QAction(label, self)
            act.triggered.connect(fn)
            toolbar.addAction(act)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("  Model "))
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(190)
        self.model_combo.setEditable(True)
        self.model_combo.addItem(self.model)
        self.model_combo.currentTextChanged.connect(self.change_model)
        toolbar.addWidget(self.model_combo)
        refresh_models = QAction("Refresh models", self)
        refresh_models.triggered.connect(self.refresh_models)
        toolbar.addAction(refresh_models)

        main_split = QSplitter(Qt.Horizontal)
        root_layout.addWidget(main_split, 1)

        # Explorer
        explorer = QWidget()
        ex_layout = QVBoxLayout(explorer)
        ex_layout.setContentsMargins(8, 10, 8, 8)
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("EXPLORER"))
        title_row.addStretch()
        folder_btn = QPushButton("Open Folder")
        folder_btn.clicked.connect(self.open_folder)
        title_row.addWidget(folder_btn)
        ex_layout.addLayout(title_row)
        self.fs_model = QFileSystemModel()
        self.fs_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)
        self.fs_model.setRootPath(self.project_root)
        self.tree = QTreeView()
        self.tree.setModel(self.fs_model)
        self.tree.setRootIndex(self.fs_model.index(self.project_root))
        self.tree.setHeaderHidden(True)
        for col in range(1, 4):
            self.tree.hideColumn(col)
        self.tree.doubleClicked.connect(self.open_tree_item)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.tree_context_menu)
        ex_layout.addWidget(self.tree)
        main_split.addWidget(explorer)

        # Editor and output split
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_status)
        center_layout.addWidget(self.tabs, 4)
        output_box = QWidget()
        out_layout = QVBoxLayout(output_box)
        out_layout.setContentsMargins(8, 5, 8, 8)
        out_head = QHBoxLayout()
        out_head.addWidget(QLabel("OUTPUT"))
        out_head.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.output.clear())
        out_head.addWidget(clear_btn)
        out_layout.addLayout(out_head)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Cascadia Code", 10))
        self.output.setMaximumBlockCount(5000)
        self.output.setPlaceholderText("Python output, diagnostics, and task results appear here.")
        out_layout.addWidget(self.output)
        center_layout.addWidget(output_box, 1)
        main_split.addWidget(center)

        # AI assistant
        assistant = QWidget()
        ai_layout = QVBoxLayout(assistant)
        ai_layout.setContentsMargins(10, 10, 10, 8)
        ai_head = QHBoxLayout()
        ai_head.addWidget(QLabel("LOCAL AI ASSISTANT"))
        ai_head.addStretch()
        self.connection_label = QLabel("● Checking")
        ai_head.addWidget(self.connection_label)
        ai_layout.addLayout(ai_head)
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setFont(QFont("Segoe UI", 10))
        self.chat.setPlaceholderText("Ask questions about code, errors, or your project.")
        ai_layout.addWidget(self.chat, 1)
        self.context_label = QLabel("Context: current editor")
        self.context_label.setStyleSheet("color:#8c96aa;")
        ai_layout.addWidget(self.context_label)
        prompt_row = QHBoxLayout()
        self.prompt = QPlainTextEdit()
        self.prompt.setMaximumHeight(125)
        self.prompt.setPlaceholderText("Ask, debug, plan, or edit…  Ctrl+Enter to send")
        self.prompt.installEventFilter(self)
        prompt_row.addWidget(self.prompt, 1)
        ai_layout.addLayout(prompt_row)
        ai_buttons = QHBoxLayout()
        self.ask_button = QPushButton("Send")
        self.ask_button.clicked.connect(self.ask_ai)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_ai)
        self.use_selection_button = QPushButton("Attach selection")
        self.use_selection_button.clicked.connect(self.attach_selection)
        ai_buttons.addWidget(self.ask_button)
        ai_buttons.addWidget(self.stop_button)
        ai_buttons.addWidget(self.use_selection_button)
        ai_layout.addLayout(ai_buttons)
        main_split.addWidget(assistant)
        main_split.setSizes([260, 850, 430])

        self.setStatusBar(QStatusBar())
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(140)
        self.progress.setRange(0, 1)
        self.progress.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress)

        # Useful shortcuts
        self._shortcut("Ctrl+N", self.new_file)
        self._shortcut("Ctrl+O", self.open_file_dialog)
        self._shortcut("Ctrl+S", self.save_file)
        self._shortcut("Ctrl+Shift+S", self.save_as)
        self._shortcut("Ctrl+Shift+F", self.search_project)
        self._shortcut("F5", self.run_python)
        self._shortcut("Ctrl+Enter", self.ask_ai)

    def _shortcut(self, key, fn):
        shortcut = QShortcut(QKeySequence(key), self)
        shortcut.activated.connect(fn)

    def _build_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        for text, fn in [
            ("New File", self.new_file), ("Open File…", self.open_file_dialog),
            ("Open Folder…", self.open_folder), ("Save", self.save_file),
            ("Save As…", self.save_as), ("Exit", self.close),
        ]:
            action = QAction(text, self)
            action.triggered.connect(fn)
            file_menu.addAction(action)
        edit_menu = self.menuBar().addMenu("&Edit")
        for text, fn in [("Find in Project", self.search_project), ("Explain Selection", self.explain_selection)]:
            action = QAction(text, self)
            action.triggered.connect(fn)
            edit_menu.addAction(action)
        ai_menu = self.menuBar().addMenu("&AI")
        for text, fn in [
            ("Ask AI", self.ask_ai), ("Explain Selection", self.explain_selection),
            ("Debug with AI", self.debug_with_ai), ("Rewrite with Preview", self.ai_rewrite),
            ("Clear Chat", self.clear_chat), ("Ollama Settings", self.ollama_settings),
        ]:
            action = QAction(text, self)
            action.triggered.connect(fn)
            ai_menu.addAction(action)
        help_menu = self.menuBar().addMenu("&Help")
        about = QAction("About Local AI Studio", self)
        about.triggered.connect(lambda: QMessageBox.about(self, APP_NAME,
            "Local AI Studio\nA local-first coding environment powered by Qt, QScintilla, and Ollama.\n\nAI changes are reviewed before being applied."))
        help_menu.addAction(about)

    def eventFilter(self, obj, event):
        if obj is self.prompt and event.type() == event.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ControlModifier:
                self.ask_ai()
                return True
        return super().eventFilter(obj, event)

    def current_editor(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def editor_for_path(self, path):
        target = os.path.abspath(path)
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, CodeEditor) and w.file_path and os.path.abspath(w.file_path) == target:
                return w
        return None

    def open_file(self, path=None):
        if path and os.path.isdir(path):
            return
        if path:
            path = os.path.abspath(path)
            existing = self.editor_for_path(path)
            if existing:
                self.tabs.setCurrentWidget(existing)
                return
        editor = CodeEditor(path or "")
        if path:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    editor.setText(f.read())
            except OSError as exc:
                QMessageBox.warning(self, "Open failed", str(exc))
                return
            title = os.path.basename(path)
        else:
            title = "untitled.py"
        editor.modificationChanged.connect(lambda changed, ed=editor: self._mark_modified(ed, changed))
        self.tabs.addTab(editor, title)
        self.tabs.setCurrentWidget(editor)
        self.update_status()

    def _mark_modified(self, editor, changed):
        i = self.tabs.indexOf(editor)
        if i >= 0:
            title = os.path.basename(editor.file_path) if editor.file_path else "untitled.py"
            self.tabs.setTabText(i, ("● " if changed else "") + title)

    def new_file(self):
        self.open_file()

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", self.project_root,
            "Code and text files (*.py *.pyw *.js *.ts *.jsx *.tsx *.html *.css *.json *.md *.txt *.yml *.yaml *.sh *.ps1 *.c *.cpp *.h *.java *.go *.rs);;All files (*)")
        if path:
            self.open_file(path)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open project folder", self.project_root)
        if folder:
            self.project_root = os.path.abspath(folder)
            self.fs_model.setRootPath(self.project_root)
            self.tree.setRootIndex(self.fs_model.index(self.project_root))
            self.settings["project_root"] = self.project_root
            self.save_settings()
            self.statusBar().showMessage(f"Project: {self.project_root}", 4000)

    def open_tree_item(self, index):
        path = self.fs_model.filePath(index)
        if os.path.isfile(path):
            self.open_file(path)

    def tree_context_menu(self, point):
        index = self.tree.indexAt(point)
        path = self.fs_model.filePath(index) if index.isValid() else self.project_root
        menu = QMenu(self)
        open_action = menu.addAction("Open")
        new_file_action = menu.addAction("New file here")
        copy_path_action = menu.addAction("Copy path")
        chosen = menu.exec_(self.tree.viewport().mapToGlobal(point))
        if chosen == open_action and os.path.isfile(path):
            self.open_file(path)
        elif chosen == new_file_action:
            folder = path if os.path.isdir(path) else os.path.dirname(path)
            new_path, _ = QFileDialog.getSaveFileName(self, "Create file", os.path.join(folder, "new_file.py"), "All files (*)")
            if new_path and not os.path.exists(new_path):
                Path(new_path).parent.mkdir(parents=True, exist_ok=True)
                Path(new_path).touch()
                self.fs_model.setRootPath(self.project_root)
                self.open_file(new_path)
        elif chosen == copy_path_action:
            QApplication.clipboard().setText(path)

    def close_tab(self, index):
        editor = self.tabs.widget(index)
        if isinstance(editor, CodeEditor) and editor.isModified():
            choice = QMessageBox.question(self, "Unsaved changes",
                f"Save changes to {self.tabs.tabText(index).lstrip('● ')}?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if choice == QMessageBox.Cancel:
                return
            if choice == QMessageBox.Save:
                self.tabs.setCurrentIndex(index)
                self.save_file()
                if editor.isModified():
                    return
        self.tabs.removeTab(index)
        editor.deleteLater()

    def save_file(self):
        editor = self.current_editor()
        if not editor:
            return
        if not editor.file_path:
            self.save_as()
            return
        try:
            path = editor.file_path
            if os.path.exists(path):
                backup = path + ".bak"
                try:
                    Path(backup).write_bytes(Path(path).read_bytes())
                except OSError:
                    pass
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(editor.text())
            editor.setModified(False)
            i = self.tabs.indexOf(editor)
            if i >= 0:
                self.tabs.setTabText(i, os.path.basename(path))
            self.statusBar().showMessage(f"Saved {path}", 3000)
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def save_as(self):
        editor = self.current_editor()
        if not editor:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save file", os.path.join(self.project_root, "untitled.py"), "All files (*)")
        if path:
            editor.file_path = os.path.abspath(path)
            self.save_file()

    def run_python(self):
        editor = self.current_editor()
        if not editor:
            return
        if not editor.file_path:
            self.save_as()
            if not editor.file_path:
                return
        self.save_file()
        if not editor.file_path.lower().endswith((".py", ".pyw")):
            QMessageBox.information(self, "Python runner", "Run Python supports .py and .pyw files.")
            return
        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.information(self, "Already running", "Stop the current process before starting another.")
            return
        self.output.clear()
        self.output.appendPlainText(f"> {sys.executable} {editor.file_path}\n")
        self.process = QProcess(self)
        self.process.setWorkingDirectory(os.path.dirname(editor.file_path) or self.project_root)
        self.process.setProgram(sys.executable)
        self.process.setArguments([editor.file_path])
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.process_finished)
        self.process.start()

    def read_stdout(self):
        if self.process:
            self.output.moveCursor(self.output.textCursor().End)
            self.output.insertPlainText(bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace"))
            self.output.ensureCursorVisible()

    def read_stderr(self):
        if self.process:
            self.output.moveCursor(self.output.textCursor().End)
            self.output.insertPlainText(bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace"))
            self.output.ensureCursorVisible()

    def process_finished(self, code, status):
        self.output.appendPlainText(f"\n[Process exited with code {code}]")
        self.process = None

    def search_project(self):
        term, ok = QInputDialog.getText(self, "Search project", "Text to find:")
        if not ok or not term:
            return
        results = []
        count = 0
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for filename in files:
                if filename.lower().endswith((".pyc", ".exe", ".dll", ".png", ".jpg", ".zip", ".pdf", ".db")):
                    continue
                path = os.path.join(root, filename)
                try:
                    if os.path.getsize(path) > 1_000_000:
                        continue
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_no, line in enumerate(f, 1):
                            if term.casefold() in line.casefold():
                                results.append(f"{os.path.relpath(path, self.project_root)}:{line_no}: {line.strip()[:180]}")
                                count += 1
                                if count >= 300:
                                    break
                except OSError:
                    pass
                if count >= 300:
                    break
            if count >= 300:
                break
        self.output.setPlainText("\n".join(results) if results else f"No matches found for {term!r}.")
        self.statusBar().showMessage(f"Search complete • {len(results)} matches", 4000)

    def _project_context(self, limit=MAX_CONTEXT_CHARS):
        editor = self.current_editor()
        if not editor:
            return ""
        path = editor.file_path or "untitled.py"
        text = editor.text()
        return f"Current editor file: {path}\n```text\n{text[:limit]}\n```"

    def attach_selection(self):
        editor = self.current_editor()
        if not editor or not editor.selected_text():
            QMessageBox.information(self, "Select code", "Select some code in the editor first.")
            return
        self.prompt.insertPlainText("\n\nSelected code:\n```\n" + editor.selected_text() + "\n```\n")
        self.prompt.setFocus()
        self.context_label.setText("Context: selected code + current editor")

    def ask_ai(self):
        prompt = self.prompt.toPlainText().strip()
        if not prompt or self.busy:
            return
        self.prompt.clear()
        self.add_chat_message("user", prompt)
        context = self._project_context()
        system = (
            "You are the coding assistant inside Local AI Studio. Be accurate and concise. "
            "Respect the user's request and do not add unrelated features. "
            "When asked to fix code, explain the bug and preserve unrelated behavior. "
            "Never claim code was executed unless it actually was."
        )
        messages = [{"role": "system", "content": system}]
        # Use recent persisted turns to maintain context; cap the history.
        for item in self.history[-12:]:
            if item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str):
                messages.append({"role": item["role"], "content": item["content"][:10000]})
        messages.append({"role": "user", "content": prompt + ("\n\n" + context if context else "")})
        self._start_worker(messages, "chat")

    def explain_selection(self):
        editor = self.current_editor()
        if not editor or not editor.selected_text():
            QMessageBox.information(self, "Select code", "Select code in the editor first.")
            return
        self.add_chat_message("user", "Explain the selected code.")
        messages = [
            {"role": "system", "content": "Explain code accurately in plain language. Point out likely bugs only when relevant."},
            {"role": "user", "content": "Explain this code:\n```\n" + editor.selected_text()[:12000] + "\n```"},
        ]
        self._start_worker(messages, "chat")

    def debug_with_ai(self):
        editor = self.current_editor()
        if not editor:
            QMessageBox.information(self, "No editor", "Open a file first.")
            return
        code = editor.text()
        error = self.output.toPlainText()[-8000:]
        messages = [
            {"role": "system", "content": "You are a careful debugging assistant. Identify the likely root cause, cite the relevant line or construct, and propose a minimal fix. Do not invent execution results."},
            {"role": "user", "content": f"Debug this code. Recent output/traceback:\n{error}\n\nFile {editor.file_path or 'untitled'}:\n```\n{code[:MAX_CONTEXT_CHARS]}\n```"},
        ]
        self.add_chat_message("user", "Debug the current file using the output panel.")
        self._start_worker(messages, "chat")

    def ai_rewrite(self):
        editor = self.current_editor()
        if not editor:
            return
        request, ok = QInputDialog.getText(self, "AI edit", "Describe the exact change to make:")
        if not ok or not request.strip():
            return
        messages = [
            {"role": "system", "content": "You are editing a source file. Return the COMPLETE updated file in exactly one fenced code block. Do not omit unchanged portions, use ellipses, or add commentary inside the code block. Make only the requested changes and preserve existing behavior. If you cannot safely produce the complete file, explain that instead of fabricating a partial replacement."},
            {"role": "user", "content": f"Requested change: {request}\n\nCurrent file ({editor.file_path or 'untitled'}):\n```\n{editor.text()[:MAX_CONTEXT_CHARS]}\n```"},
        ]
        self.add_chat_message("user", "AI edit request: " + request)
        self._start_worker(messages, "rewrite")

    def _start_worker(self, messages, purpose):
        self.busy = True
        self.ask_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress.setVisible(True)
        self.statusBar().showMessage(f"Waiting for {self.model} in background…")
        worker = AIWorker(self.base_url, self.model, messages, purpose, self)
        worker.succeeded.connect(self._ai_success)
        worker.failed.connect(self._ai_failure)
        worker.finished.connect(lambda w=worker: self._worker_finished(w))
        self.workers.append(worker)
        worker.start()

    def _worker_finished(self, worker):
        self.busy = False
        self.ask_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress.setVisible(False)
        if worker in self.workers:
            self.workers.remove(worker)
        worker.deleteLater()
        self.statusBar().showMessage(f"Ready • {self.model}", 4000)

    def stop_ai(self):
        # A blocking requests call in a worker cannot be force-killed safely.
        # Set cancellation flag; UI stays responsive and response is ignored.
        for worker in self.workers:
            worker.cancel()
        self.statusBar().showMessage("Cancellation requested; current HTTP request may finish in the background.", 5000)
        self.stop_button.setEnabled(False)

    def _ai_success(self, answer, meta):
        self.add_chat_message("assistant", answer)
        self.history.append({"role": "assistant", "content": answer, "model": meta.get("model")})
        self._trim_history()
        save_json(HISTORY_FILE, self.history)
        if meta.get("purpose") == "rewrite":
            proposed = self.extract_code(answer)
            if not proposed:
                QMessageBox.warning(self, "No complete code block", "Qwen did not return a fenced code block, so the editor was not changed.")
                return
            editor = self.current_editor()
            if not editor:
                return
            dialog = ReviewDialog(proposed, self)
            if dialog.exec_() == QDialog.Accepted:
                editor.setText(dialog.text.toPlainText())
                editor.setModified(True)
                self.statusBar().showMessage("AI changes applied to editor only. Save to write to disk.", 6000)

    def _ai_failure(self, error):
        self.add_chat_message("error", error)
        self.statusBar().showMessage("AI request failed", 5000)

    def add_chat_message(self, role, content):
        # Escape HTML so code/errors display safely as text.
        safe = (content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("\n", "<br>"))
        title = {"user": "You", "assistant": "Qwen", "error": "Error"}.get(role, role.title())
        color = {"user": "#8ab4f8", "assistant": "#8bd5a8", "error": "#ff8585"}.get(role, "#dce3f0")
        self.chat.append(f'<p style="margin-top:12px;color:{color};"><b>{title}</b><br><span style="color:#dce3f0;">{safe}</span></p>')
        if role in ("user", "assistant"):
            self.history.append({"role": role, "content": content})
            self._trim_history()
            save_json(HISTORY_FILE, self.history)

    def _restore_history(self):
        for item in self.history[-40:]:
            if item.get("role") in ("user", "assistant") and item.get("content"):
                safe = (item["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        .replace("\n", "<br>"))
                title = "You" if item["role"] == "user" else "Qwen"
                self.chat.append(f"<b>{title}</b><br>{safe}<br>")
        if not self.chat.toPlainText().strip():
            self.chat.setHtml(f"<h3>{APP_NAME}</h3><p>Local-first coding assistant<br>Model: {self.model}</p><p>Use Ask, Explain, Debug, or AI Edit to get started.</p>")

    def _trim_history(self):
        self.history = self.history[-80:]

    @staticmethod
    def extract_code(answer):
        match = re.search(r"```(?:[a-zA-Z0-9_+#.-]+)?\s*\n(.*?)```", answer, re.S)
        return match.group(1).rstrip() if match else ""

    def change_model(self, value):
        if value.strip():
            self.model = value.strip()
            self.settings["model"] = self.model
            self.save_settings()
            self.statusBar().showMessage(f"Model set to {self.model}", 3000)

    def refresh_models(self):
        try:
            response = requests.get(self.base_url + "/api/tags", timeout=5)
            response.raise_for_status()
            models = [m.get("name", "") for m in response.json().get("models", []) if m.get("name")]
            current = self.model
            self.model_combo.blockSignals(True)
            self.model_combo.clear()
            self.model_combo.addItems(models or [current])
            if current not in models:
                self.model_combo.addItem(current)
            self.model_combo.setCurrentText(current)
            self.model_combo.blockSignals(False)
            self.statusBar().showMessage(f"Found {len(models)} local model(s)", 4000)
        except Exception as exc:
            QMessageBox.warning(self, "Ollama models", f"Could not list models:\n{exc}")

    def check_connection(self):
        # Small non-blocking check using a worker is unnecessary for startup,
        # so run it with a short timer via a separate QThread worker.
        def finish():
            pass
        # avoid blocking the UI on a network call
        class PingWorker(QThread):
            result = pyqtSignal(bool, str)
            def run(self_inner):
                try:
                    r = requests.get(self.base_url + "/api/version", timeout=3)
                    r.raise_for_status()
                    self_inner.result.emit(True, r.json().get("version", "connected"))
                except Exception as exc:
                    self_inner.result.emit(False, str(exc))
        self.ping_worker = PingWorker(self)
        self.ping_worker.result.connect(self._connection_result)
        self.ping_worker.start()

    def _connection_result(self, ok, detail):
        if ok:
            self.connection_label.setText("● Connected")
            self.connection_label.setStyleSheet("color:#8bd5a8;")
            self.statusBar().showMessage(f"Ollama connected • {detail}", 4000)
        else:
            self.connection_label.setText("● Offline")
            self.connection_label.setStyleSheet("color:#ff8585;")
            self.statusBar().showMessage("Ollama not reachable; AI requests will fail until it starts.", 7000)

    def ollama_settings(self):
        url, ok = QInputDialog.getText(self, "Ollama settings", "Ollama base URL:", text=self.base_url)
        if not ok or not url.strip():
            return
        self.base_url = url.strip().rstrip("/")
        self.settings["ollama_url"] = self.base_url
        self.save_settings()
        self.check_connection()

    def clear_chat(self):
        choice = QMessageBox.question(self, "Clear chat", "Clear the visible chat and saved conversation history?",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if choice == QMessageBox.Yes:
            self.history = []
            save_json(HISTORY_FILE, self.history)
            self.chat.clear()
            self._restore_history()

    def save_settings(self):
        self.settings["model"] = self.model
        self.settings["ollama_url"] = self.base_url
        self.settings["project_root"] = self.project_root
        save_json(SETTINGS_FILE, self.settings)

    def update_status(self, *args):
        editor = self.current_editor()
        if editor:
            line, index = editor.getCursorPosition()
            language = "Python" if (editor.file_path or "").lower().endswith((".py", ".pyw")) else "Text"
            self.statusBar().showMessage(f"{language} • Line {line + 1}, Column {index + 1} • {self.model}")

    def closeEvent(self, event):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()
        self.save_settings()
        save_json(HISTORY_FILE, self.history)
        for worker in self.workers:
            worker.cancel()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QMainWindow, QWidget { background:#171a21; color:#dce3f0; font-family:'Segoe UI'; font-size:10pt; }
        QMenuBar, QMenu, QToolBar { background:#202530; color:#dce3f0; border:0; spacing:5px; }
        QMenuBar::item { padding:6px 10px; }
        QMenuBar::item:selected, QMenu::item:selected { background:#344c72; }
        QToolBar { padding:6px; spacing:5px; border-bottom:1px solid #303746; }
        QToolButton { background:#252b38; border:1px solid #353d4d; padding:6px 9px; border-radius:4px; }
        QToolButton:hover { background:#344c72; }
        QTreeView, QTabWidget::pane, QTabBar::tab { background:#11141b; color:#dce3f0; border:1px solid #293141; }
        QTreeView { alternate-background-color:#171a21; }
        QTreeView::item { padding:4px; }
        QTreeView::item:selected { background:#344c72; }
        QTabBar::tab { padding:8px 14px; margin-right:2px; }
        QTabBar::tab:selected { background:#344c72; }
        QPushButton { background:#283247; color:#e8edfa; border:1px solid #3b4964; padding:7px 11px; border-radius:4px; }
        QPushButton:hover { background:#344c72; }
        QPushButton:disabled { color:#70798c; background:#202530; }
        QTextEdit, QPlainTextEdit, QLineEdit, QComboBox { background:#11141b; color:#dce3f0; border:1px solid #303746; padding:6px; selection-background-color:#344c72; }
        QComboBox QAbstractItemView { background:#202530; selection-background-color:#344c72; }
        QLabel { color:#c4ccda; }
        QStatusBar { background:#252f42; color:#dce3f0; border-top:1px solid #39465e; }
        QProgressBar { border:1px solid #3b4964; text-align:center; background:#11141b; }
        QProgressBar::chunk { background:#7c8fe8; }
        QSplitter::handle { background:#303746; }
    """)
    window = LocalAIStudio()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
