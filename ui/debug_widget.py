"""
SUKHI IDE — Debug Adapter Protocol (DAP) UI Widget
Provides visual breakpoint management, call stack navigation,
variable evaluation, and interactive step/resume execution toolbar.
"""
from typing import List, Dict, Any, Optional
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QSplitter, QHeaderView
)
from debugging.dap_client import DapClient, SourceBreakpoint, StackFrame, Variable


class DebugPanelWidget(QWidget):
    """Visual panel for interactive debugging session controls and inspections."""
    continue_requested = pyqtSignal()
    step_over_requested = pyqtSignal()
    step_into_requested = pyqtSignal()
    step_out_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    frame_selected = pyqtSignal(str, int)  # file_path, line

    def __init__(self, dap_client: Optional[DapClient] = None, parent=None):
        super().__init__(parent)
        self.dap = dap_client
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Control Toolbar
        toolbar = QHBoxLayout()
        self.btn_continue = QPushButton("▶ Continue")
        self.btn_continue.setStyleSheet("background: #065f46; border-color: #10b981; font-weight: bold;")
        self.btn_continue.clicked.connect(self.continue_requested.emit)

        self.btn_step_over = QPushButton("↷ Step Over")
        self.btn_step_over.clicked.connect(self.step_over_requested.emit)

        self.btn_step_into = QPushButton("↓ Step Into")
        self.btn_step_into.clicked.connect(self.step_into_requested.emit)

        self.btn_step_out = QPushButton("↑ Step Out")
        self.btn_step_out.clicked.connect(self.step_out_requested.emit)

        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setStyleSheet("background: #7f1d1d; border-color: #991b1b;")
        self.btn_stop.clicked.connect(self.stop_requested.emit)

        toolbar.addWidget(self.btn_continue)
        toolbar.addWidget(self.btn_step_over)
        toolbar.addWidget(self.btn_step_into)
        toolbar.addWidget(self.btn_step_out)
        toolbar.addWidget(self.btn_stop)
        toolbar.addStretch()

        self.status_lbl = QLabel("Ready")
        self.status_lbl.setStyleSheet("color: #94A3B8; font-weight: bold;")
        toolbar.addWidget(self.status_lbl)
        layout.addLayout(toolbar)

        # Main splitter (Stack frames & Variables & Breakpoints)
        splitter = QSplitter(Qt.Horizontal)

        # 1. Call Stack
        stack_widget = QWidget()
        stack_layout = QVBoxLayout(stack_widget)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.addWidget(QLabel("<b>CALL STACK</b>"))

        self.tree_stack = QTreeWidget()
        self.tree_stack.setHeaderLabels(["Frame", "Source", "Line"])
        self.tree_stack.setStyleSheet("""
            QTreeWidget {
                background: #080c14;
                border: 1px solid #1a2230;
                color: #dce7fa;
            }
            QTreeWidget::item:selected { background: #192333; color: #5aa7ff; }
        """)
        self.tree_stack.itemDoubleClicked.connect(self._on_stack_item_double_clicked)
        stack_layout.addWidget(self.tree_stack, 1)
        splitter.addWidget(stack_widget)

        # 2. Variables / Scope
        var_widget = QWidget()
        var_layout = QVBoxLayout(var_widget)
        var_layout.setContentsMargins(0, 0, 0, 0)
        var_layout.addWidget(QLabel("<b>VARIABLES</b>"))

        self.tree_vars = QTreeWidget()
        self.tree_vars.setHeaderLabels(["Name", "Value", "Type"])
        self.tree_vars.setStyleSheet("""
            QTreeWidget {
                background: #080c14;
                border: 1px solid #1a2230;
                color: #dce7fa;
            }
        """)
        self.tree_vars.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        var_layout.addWidget(self.tree_vars, 1)
        splitter.addWidget(var_widget)

        # 3. Breakpoints
        bp_widget = QWidget()
        bp_layout = QVBoxLayout(bp_widget)
        bp_layout.setContentsMargins(0, 0, 0, 0)
        bp_layout.addWidget(QLabel("<b>BREAKPOINTS</b>"))

        self.tree_bp = QTreeWidget()
        self.tree_bp.setHeaderLabels(["File", "Line", "Condition"])
        self.tree_bp.setStyleSheet("""
            QTreeWidget {
                background: #080c14;
                border: 1px solid #1a2230;
                color: #dce7fa;
            }
        """)
        bp_layout.addWidget(self.tree_bp, 1)
        splitter.addWidget(bp_widget)

        splitter.setSizes([220, 260, 180])
        layout.addWidget(splitter, 1)

    def set_session_status(self, status: str):
        self.status_lbl.setText(status)
        if "Paused" in status:
            self.status_lbl.setStyleSheet("color: #F59E0B; font-weight: bold;")
        elif "Running" in status:
            self.status_lbl.setStyleSheet("color: #10B981; font-weight: bold;")
        else:
            self.status_lbl.setStyleSheet("color: #94A3B8; font-weight: bold;")

    def update_call_stack(self, frames: List[Dict[str, Any]]):
        self.tree_stack.clear()
        for f in frames:
            name = f.get("name", "anonymous")
            source = f.get("source", {}).get("name", "unknown") if isinstance(f.get("source"), dict) else str(f.get("source", "unknown"))
            path = f.get("source", {}).get("path", "") if isinstance(f.get("source"), dict) else ""
            line = str(f.get("line", 0))

            item = QTreeWidgetItem([name, source, line])
            item.setData(0, Qt.UserRole, (path, f.get("line", 0)))
            self.tree_stack.addTopLevelItem(item)

    def update_variables(self, variables: List[Dict[str, Any]]):
        self.tree_vars.clear()
        for v in variables:
            name = v.get("name", "")
            val = str(v.get("value", ""))
            v_type = v.get("type", "")
            item = QTreeWidgetItem([name, val, v_type])
            self.tree_vars.addTopLevelItem(item)

    def update_breakpoints(self, breakpoints):
        self.tree_bp.clear()
        for bp in breakpoints:
            if isinstance(bp, dict):
                f_path = bp.get("file_path", "")
                line = str(bp.get("line", 0))
                cond = bp.get("condition", "")
            else:
                f_path = getattr(bp, "file_path", str(getattr(bp, "id", "")))
                line = str(getattr(bp, "line", 0))
                cond = getattr(bp, "condition", "") or ""
            item = QTreeWidgetItem([f_path, line, cond])
            self.tree_bp.addTopLevelItem(item)

    def _on_stack_item_double_clicked(self, item: QTreeWidgetItem, col: int):
        data = item.data(0, Qt.UserRole)
        if data:
            path, line = data
            if path:
                self.frame_selected.emit(path, line)
