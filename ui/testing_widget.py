"""
PRUBETH IDE — Visual Test Explorer Widget
Live pytest discovery and real-time pass/fail streaming via QProcess.
"""
import re
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal, QProcess, QProcessEnvironment
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QProgressBar
)
from PyQt5.QtGui import QFont, QCursor, QColor

_PASS_COLOR = QColor("#10B981")
_FAIL_COLOR = QColor("#EF4444")
_WARN_COLOR = QColor("#F59E0B")
_IDLE_COLOR = QColor("#94A3B8")


class TestingWidget(QWidget):
    """VS Code-style Test Explorer with live pytest execution."""
    run_all_requested = pyqtSignal()
    test_selected = pyqtSignal(str)

    def __init__(self, workspace_root: Path, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root).resolve()
        self._process: QProcess | None = None
        self._node_map: dict[str, QTreeWidgetItem] = {}
        self._passed = 0
        self._failed = 0
        self._collect_buf = ""
        self._init_ui()
        # Auto-discover on first load
        self._discover()

    # ------------------------------------------------------------------ #
    #  UI Construction                                                      #
    # ------------------------------------------------------------------ #
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header
        header = QHBoxLayout()
        lbl = QLabel("<b>TEST EXPLORER</b>")
        lbl.setStyleSheet("color: #00F0FF; font-size: 8.5pt;")
        header.addWidget(lbl)
        header.addStretch(1)

        self.btn_discover = QPushButton("🔍 Discover", self)
        self.btn_discover.setStyleSheet(self._btn_css("#1e2b3a", "#2d3f52"))
        self.btn_discover.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_discover.clicked.connect(self._discover)
        header.addWidget(self.btn_discover)

        self.btn_run_all = QPushButton("▶ Run All", self)
        self.btn_run_all.setStyleSheet(self._btn_css("#186036", "#238647"))
        self.btn_run_all.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_run_all.clicked.connect(self._run_all)
        header.addWidget(self.btn_run_all)

        self.btn_stop = QPushButton("⏹ Stop", self)
        self.btn_stop.setStyleSheet(self._btn_css("#6b1212", "#8b1e1e"))
        self.btn_stop.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_stop.clicked.connect(self._stop)
        self.btn_stop.setEnabled(False)
        header.addWidget(self.btn_stop)

        layout.addLayout(header)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setMaximumHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar { background: #1e2433; border-radius: 3px; border: none; }
            QProgressBar::chunk { background: #10B981; border-radius: 3px; }
        """)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Test Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Test", "Status", "Duration"])
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
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree, 1)

        # Status footer
        footer = QHBoxLayout()
        self.stat_lbl = QLabel("⏳ Discovering tests…")
        self.stat_lbl.setStyleSheet("color: #94A3B8; font-size: 8pt;")
        footer.addWidget(self.stat_lbl)
        layout.addLayout(footer)

    @staticmethod
    def _btn_css(bg: str, hover: str) -> str:
        return f"""
            QPushButton {{
                background: {bg}; color: #fff; font-weight: bold;
                padding: 3px 8px; border-radius: 4px; font-size: 8.5pt;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:disabled {{ background: #1e2433; color: #4a5568; }}
        """

    # ------------------------------------------------------------------ #
    #  Discovery (pytest --collect-only -q)                                #
    # ------------------------------------------------------------------ #
    def _discover(self):
        """Run pytest --collect-only -q to populate the tree."""
        self.tree.clear()
        self._node_map.clear()
        self.stat_lbl.setText("⏳ Discovering…")
        self._collect_buf = ""

        proc = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        proc.setProcessEnvironment(env)
        proc.setWorkingDirectory(str(self.workspace_root))
        proc.readyReadStandardOutput.connect(lambda: self._on_collect_data(proc))
        proc.readyReadStandardError.connect(lambda: self._on_collect_data(proc))
        proc.finished.connect(lambda code, status: self._on_collect_done())
        proc.start("python", ["-m", "pytest", "--collect-only", "-q", "--no-header"])

    def _on_collect_data(self, proc: QProcess):
        raw = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        raw += bytes(proc.readAllStandardError()).decode("utf-8", errors="replace")
        self._collect_buf += raw

    def _on_collect_done(self):
        lines = self._collect_buf.splitlines()
        suite_items: dict[str, QTreeWidgetItem] = {}
        count = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith("=") or line.startswith("no tests"):
                continue
            # Format: tests/test_studio.py::TestClass::test_name or tests/test_studio.py::test_name
            if "::" in line:
                parts = line.split("::")
                suite_file = parts[0]
                test_name = "::".join(parts[1:])
                if suite_file not in suite_items:
                    suite_item = QTreeWidgetItem(self.tree, [suite_file, "–", "–"])
                    suite_item.setExpanded(True)
                    suite_items[suite_file] = suite_item
                parent = suite_items[suite_file]
                item = QTreeWidgetItem(parent, [test_name, "–", "–"])
                item.setForeground(1, _IDLE_COLOR)
                self._node_map[line.strip()] = item
                count += 1

        if count:
            self.btn_run_all.setText(f"▶ Run All ({count})")
            self.stat_lbl.setText(f"📋 {count} tests discovered")
        else:
            self.stat_lbl.setText("⚠️ No tests found — open a workspace folder first")

    # ------------------------------------------------------------------ #
    #  Live Test Run (pytest -v --tb=no)                                   #
    # ------------------------------------------------------------------ #
    def _run_all(self):
        if self._process and self._process.state() != QProcess.NotRunning:
            return
        self.run_all_requested.emit()
        self._passed = 0
        self._failed = 0
        self.progress.setValue(0)
        self.progress.show()
        self.btn_run_all.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.stat_lbl.setText("🏃 Running…")

        # Reset all status cells
        for item in self._node_map.values():
            item.setText(1, "⏳")
            item.setForeground(1, _IDLE_COLOR)

        self._process = QProcess(self)
        self._process.setWorkingDirectory(str(self.workspace_root))
        self._process.readyReadStandardOutput.connect(self._on_run_data)
        self._process.readyReadStandardError.connect(self._on_run_data)
        self._process.finished.connect(self._on_run_done)
        self._process.start("python", ["-m", "pytest", "-v", "--tb=no", "--no-header"])

    def _on_run_data(self):
        raw = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        raw += bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
        for line in raw.splitlines():
            # Format: tests/test_studio.py::test_foo PASSED   [  5%]
            m = re.match(r"^(.+::[\w\[\-\]]+)\s+(PASSED|FAILED|ERROR|SKIPPED)\s+\[\s*(\d+)%\]", line)
            if m:
                node_id = m.group(1).strip()
                status = m.group(2)
                pct = int(m.group(3))
                self.progress.setValue(pct)
                if status == "PASSED":
                    self._passed += 1
                    icon, color = "✓ PASS", _PASS_COLOR
                elif status in ("FAILED", "ERROR"):
                    self._failed += 1
                    icon, color = "✗ FAIL", _FAIL_COLOR
                else:
                    icon, color = "⏭ SKIP", _WARN_COLOR

                # Try exact match first, then suffix match
                item = self._node_map.get(node_id)
                if item is None:
                    for key, val in self._node_map.items():
                        if node_id.endswith(key) or key.endswith(node_id.split("::")[-1]):
                            item = val
                            break
                if item:
                    item.setText(1, icon)
                    item.setForeground(1, color)
                self.stat_lbl.setText(
                    f"✓ {self._passed} passed · ✗ {self._failed} failed"
                )

    def _on_run_done(self):
        self.progress.hide()
        self.btn_run_all.setEnabled(True)
        self.btn_stop.setEnabled(False)
        total = self._passed + self._failed
        if self._failed == 0:
            self.stat_lbl.setText(f"● {self._passed} Passed · 0 Failed · ✅ All Green")
            self.stat_lbl.setStyleSheet("color: #10B981; font-weight: bold; font-size: 8pt;")
        else:
            self.stat_lbl.setText(f"● {self._passed} Passed · {self._failed} Failed")
            self.stat_lbl.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 8pt;")
        self._process = None

    def _stop(self):
        if self._process:
            self._process.kill()
            self._process = None
        self.btn_run_all.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.hide()
        self.stat_lbl.setText("⏹ Run stopped")

    def _on_item_clicked(self, item: QTreeWidgetItem, col: int):
        self.test_selected.emit(item.text(0))

    # ------------------------------------------------------------------ #
    #  Public API (called by Studio when workspace changes)                #
    # ------------------------------------------------------------------ #
    def set_workspace(self, root: Path):
        self.workspace_root = Path(root).resolve()
        self._discover()
