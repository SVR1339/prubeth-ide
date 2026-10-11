"""
PRUBETH IDE — Mission Control Dashboard (Asynchronous Surface)
Implements the Dual-Surface Workflow:
- Editor View (Synchronous Surface): Low-latency code editing and tab autocomplete.
- Mission Control (Asynchronous Surface): Macro dashboard where developers act as system architects,
  spawning and supervising independent background subagents across 30-to-60 minute objectives in parallel.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QTextEdit, QSplitter,
    QDialog, QLineEdit, QComboBox, QCheckBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

from antigravity.mission_control import MissionControlOrchestrator, SubagentMission
from antigravity.stage_gate import StageStatus


class SpawnMissionDialog(QDialog):
    """Dialog to spawn a new asynchronous subagent mission."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spawn Autonomous Subagent Mission")
        self.setMinimumWidth(550)
        self.setStyleSheet("""
            QDialog { background-color: #111218; color: #E0E0E0; border: 1px solid #1E202C; }
            QLabel { color: #8F93A2; font-size: 12px; font-weight: bold; }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #161722; color: #FFFFFF; border: 1px solid #282A3A;
                border-radius: 4px; padding: 6px; font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 1px solid #00F0FF; }
            QPushButton {
                background-color: #1F2233; color: #00F0FF; border: 1px solid #00F0FF;
                border-radius: 4px; padding: 8px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #00F0FF; color: #0B0D13; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel("MISSION TITLE:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Refactor OAuth2 Authentication & Session Store")
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("OBJECTIVE & REQUIREMENTS (SWE-BENCH STYLE):"))
        self.objective_input = QTextEdit()
        self.objective_input.setPlaceholderText(
            "Describe the high-level bug, feature, or refactoring objective.\n"
            "The subagent will decompose this into an implementation plan, work in an isolated worktree, and verify with tests."
        )
        self.objective_input.setMinimumHeight(120)
        layout.addWidget(self.objective_input)

        layout.addWidget(QLabel("INFERENCE ENGINE / MODEL:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "redsage-8b:latest (Local GPU Offload - GTX 1050 Ti)",
            "gemini-3.8-flash (Google Frontier Cloud)",
            "gemini-3.5-flash (Fast Cloud Fallback)"
        ])
        layout.addWidget(self.model_combo)

        self.worktree_check = QCheckBox("Enable Zero-Interference Git Worktree Isolation (Shadow Branch)")
        self.worktree_check.setChecked(True)
        self.worktree_check.setStyleSheet("color: #00FF88; font-weight: bold; margin-top: 6px;")
        layout.addWidget(self.worktree_check)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: transparent; border: 1px solid #444; color: #888;")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        spawn_btn = QPushButton("🚀 Launch Subagent")
        spawn_btn.clicked.connect(self.accept)
        btn_row.addWidget(spawn_btn)

        layout.addLayout(btn_row)

    def get_data(self):
        raw_model = self.model_combo.currentText().split()[0]
        return {
            "title": self.title_input.text().strip() or "Autonomous Subagent Task",
            "objective": self.objective_input.toPlainText().strip(),
            "model": raw_model,
            "use_isolated_worktree": self.worktree_check.isChecked()
        }


class MissionControlWidget(QWidget):
    """
    Macro dashboard for managing parallel autonomous subagents.
    Acts as the Asynchronous Surface in the Dual-Surface workflow.
    """
    switchToEditorRequested = pyqtSignal()
    openArtifactRequested = pyqtSignal(str)  # artifact_id

    def __init__(self, orchestrator: MissionControlOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.active_selected_task_id = None
        self._init_ui()

        # Telemetry refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_missions)
        self.timer.start(2500)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 1. Header with Dual-Surface Navigation Switch
        header = QHBoxLayout()
        title_label = QLabel("MISSION CONTROL // AGENT MANAGER")
        title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title_label.setStyleSheet("color: #00F0FF; letter-spacing: 1px;")
        header.addWidget(title_label)

        header.addStretch()

        self.switch_editor_btn = QPushButton("💻 Switch to Editor View")
        self.switch_editor_btn.setStyleSheet("""
            QPushButton {
                background-color: #161722; color: #FFFFFF; border: 1px solid #282A3A;
                border-radius: 4px; padding: 6px 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #202436; border-color: #00F0FF; color: #00F0FF; }
        """)
        self.switch_editor_btn.clicked.connect(self.switchToEditorRequested.emit)
        header.addWidget(self.switch_editor_btn)

        self.spawn_btn = QPushButton("+ Spawn Subagent Mission")
        self.spawn_btn.setStyleSheet("""
            QPushButton {
                background-color: #00F0FF; color: #0B0D13; border: none;
                border-radius: 4px; padding: 6px 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #33F3FF; }
        """)
        self.spawn_btn.clicked.connect(self._open_spawn_dialog)
        header.addWidget(self.spawn_btn)

        layout.addLayout(header)

        # 2. Hardware & Architecture Telemetry Card
        telemetry_frame = QFrame()
        telemetry_frame.setStyleSheet("""
            QFrame {
                background-color: #141620; border: 1px solid #1E202C;
                border-radius: 6px; padding: 6px;
            }
        """)
        tel_layout = QHBoxLayout(telemetry_frame)
        tel_layout.setContentsMargins(10, 6, 10, 6)

        self.gpu_label = QLabel("GPU: GeForce GTX 1050 Ti (4GB VRAM) • 33 Layers Offloaded")
        self.gpu_label.setStyleSheet("color: #00FF88; font-size: 11px; font-weight: bold;")
        tel_layout.addWidget(self.gpu_label)

        tel_layout.addStretch()

        self.tasks_count_label = QLabel("Active Subagents: 0 | Artifacts: 0")
        self.tasks_count_label.setStyleSheet("color: #8F93A2; font-size: 11px;")
        tel_layout.addWidget(self.tasks_count_label)

        layout.addWidget(telemetry_frame)

        # 3. Main Splitter: Task Table (Top) and Task Inspector (Bottom)
        splitter = QSplitter(Qt.Vertical)

        # Task Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Mission Title", "Objective", "Stage (PRINCE2)", "Progress", "Active Skills", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_table_row_selected)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #111218; gridline-color: #1E202C;
                color: #FFFFFF; border: 1px solid #1E202C; border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #161722; color: #8F93A2; border: 1px solid #1E202C;
                padding: 6px; font-weight: bold; font-size: 11px;
            }
            QTableWidget::item:selected { background-color: #1F2233; color: #00F0FF; }
        """)
        splitter.addWidget(self.table)

        # Inspector Panel
        inspector = QWidget()
        insp_layout = QHBoxLayout(inspector)
        insp_layout.setContentsMargins(0, 0, 0, 0)

        # Left Inspector: ReAct Traces
        trace_box = QVBoxLayout()
        trace_lbl = QLabel("ReAct REASONING & ACTION STREAM (Thought / Action / Observation):")
        trace_lbl.setStyleSheet("color: #8F93A2; font-size: 11px; font-weight: bold;")
        trace_box.addWidget(trace_lbl)

        self.trace_view = QTextEdit()
        self.trace_view.setReadOnly(True)
        self.trace_view.setStyleSheet("""
            QTextEdit {
                background-color: #0D0E13; color: #D0D0D0; border: 1px solid #1E202C;
                font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;
            }
        """)
        trace_box.addWidget(self.trace_view)
        insp_layout.addLayout(trace_box, stretch=2)

        # Right Inspector: Mid-Flight Steering & Artifact Controls
        steer_box = QVBoxLayout()
        steer_lbl = QLabel("MID-FLIGHT STEERING & DIRECTIVES:")
        steer_lbl.setStyleSheet("color: #8F93A2; font-size: 11px; font-weight: bold;")
        steer_box.addWidget(steer_lbl)

        self.steer_input = QTextEdit()
        self.steer_input.setPlaceholderText("Enter mid-flight directive to guide running subagent without restarting...")
        self.steer_input.setMaximumHeight(80)
        self.steer_input.setStyleSheet("background-color: #161722; color: #FFF; border: 1px solid #1E202C;")
        steer_box.addWidget(self.steer_input)

        send_steer_btn = QPushButton("Inject Directive into Agent Loop")
        send_steer_btn.setStyleSheet("background-color: #1F2233; color: #00FF88; border: 1px solid #00FF88; font-weight: bold;")
        send_steer_btn.clicked.connect(self._inject_directive)
        steer_box.addWidget(send_steer_btn)

        steer_box.addSpacing(10)
        art_lbl = QLabel("VERIFIABLE DELIVERABLES / ARTIFACTS:")
        art_lbl.setStyleSheet("color: #8F93A2; font-size: 11px; font-weight: bold;")
        steer_box.addWidget(art_lbl)

        self.artifacts_summary = QTextEdit()
        self.artifacts_summary.setReadOnly(True)
        self.artifacts_summary.setMaximumHeight(100)
        self.artifacts_summary.setStyleSheet("background-color: #0D0E13; color: #00F0FF; border: 1px solid #1E202C; font-size: 11px;")
        steer_box.addWidget(self.artifacts_summary)

        insp_layout.addLayout(steer_box, stretch=1)
        splitter.addWidget(inspector)

        splitter.setSizes([260, 240])
        layout.addWidget(splitter)

    def _open_spawn_dialog(self):
        dlg = SpawnMissionDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            mission = self.orchestrator.spawn_mission(
                title=data["title"],
                objective=data["objective"],
                model=data["model"],
                use_isolated_worktree=data["use_isolated_worktree"]
            )
            self.refresh_missions()
            QMessageBox.information(
                self, "Subagent Spawned",
                f"Spawned subagent '{mission.title}' (ID: {mission.task_id}).\n"
                f"Isolated worktree created. Stage-Gate: {mission.stage_gate.current_stage.value}."
            )

    def refresh_missions(self):
        missions = self.orchestrator.get_all_missions()
        self.table.setRowCount(len(missions))

        total_artifacts = sum(len(m.artifacts) for m in missions)
        self.tasks_count_label.setText(f"Active Subagents: {len(missions)} | Verifiable Artifacts: {total_artifacts}")

        for row, m in enumerate(missions):
            self.table.setItem(row, 0, QTableWidgetItem(m.title))
            self.table.setItem(row, 1, QTableWidgetItem(m.objective[:60] + "..." if len(m.objective) > 60 else m.objective))

            # Stage badge with color
            stage_str = m.stage_gate.current_stage.value if m.stage_gate else "UNKNOWN"
            stage_item = QTableWidgetItem(stage_str)
            if stage_str == StageStatus.STAGE_GATE_REVIEW.value:
                stage_item.setForeground(QColor("#FFCC00"))
            elif stage_str == StageStatus.EXECUTION.value:
                stage_item.setForeground(QColor("#00F0FF"))
            elif stage_str == StageStatus.ACCEPTANCE.value:
                stage_item.setForeground(QColor("#FF77FF"))
            elif stage_str == StageStatus.COMPLETED.value:
                stage_item.setForeground(QColor("#00FF88"))
            self.table.setItem(row, 2, stage_item)

            # Progress
            self.table.setItem(row, 3, QTableWidgetItem(f"{m.progress_pct}%"))

            # Active Skills
            skills_str = ", ".join(m.active_skills) or "None"
            self.table.setItem(row, 4, QTableWidgetItem(skills_str))

            # Action Buttons Row
            action_widget = QWidget()
            act_lay = QHBoxLayout(action_widget)
            act_lay.setContentsMargins(2, 2, 2, 2)
            act_lay.setSpacing(4)

            if m.stage_gate and m.stage_gate.current_stage == StageStatus.STAGE_GATE_REVIEW:
                app_btn = QPushButton("✓ Approve")
                app_btn.setStyleSheet("background-color: #00FF88; color: #000; font-size: 10px; font-weight: bold;")
                app_btn.clicked.connect(lambda _, t_id=m.task_id: self._approve_mission(t_id))
                act_lay.addWidget(app_btn)

            ver_btn = QPushButton("⚡ Verify")
            ver_btn.setStyleSheet("background-color: #1F2233; color: #00F0FF; font-size: 10px;")
            ver_btn.clicked.connect(lambda _, t_id=m.task_id: self._verify_mission(t_id))
            act_lay.addWidget(ver_btn)

            abort_btn = QPushButton("✕ Abort")
            abort_btn.setStyleSheet("background-color: #331A20; color: #FF4466; font-size: 10px;")
            abort_btn.clicked.connect(lambda _, t_id=m.task_id: self._abort_mission(t_id))
            act_lay.addWidget(abort_btn)

            self.table.setCellWidget(row, 5, action_widget)

    def _on_table_row_selected(self):
        row = self.table.currentRow()
        missions = self.orchestrator.get_all_missions()
        if 0 <= row < len(missions):
            mission = missions[row]
            self.active_selected_task_id = mission.task_id

            # Render ReAct traces
            if mission.stage_gate:
                trace_lines = []
                for step in mission.stage_gate.react_traces:
                    trace_lines.append(f"[{step.step_number}] THOUGHT: {step.thought}")
                    if step.action:
                        trace_lines.append(f"    ACTION: {step.action}({step.action_input})")
                    if step.observation:
                        trace_lines.append(f"    OBSERVATION: {step.observation}")
                    trace_lines.append("")
                self.trace_view.setPlainText("\n".join(trace_lines))
            else:
                self.trace_view.setPlainText("No ReAct traces recorded.")

            # Render Artifacts summary
            art_lines = [f"Artifact Count: {len(mission.artifacts)}"]
            for a_id in mission.artifacts:
                art = self.orchestrator.artifact_engine.artifacts.get(a_id)
                if art:
                    art_lines.append(f"• [{art.artifact_type.value}] {art.title} ({art.file_name})")
            self.artifacts_summary.setPlainText("\n".join(art_lines))

    def _approve_mission(self, task_id: str):
        success = self.orchestrator.approve_mission_stage(task_id, reviewer="developer", notes="Approved from Mission Control")
        if success:
            QMessageBox.information(self, "Stage Gate Approved", f"Mission '{task_id}' approved. Transitioned to EXECUTION in sandbox.")
            self.refresh_missions()

    def _verify_mission(self, task_id: str):
        res = self.orchestrator.run_mission_verification(task_id)
        if res.get("success"):
            QMessageBox.information(self, "Verification Passed", f"Mission '{task_id}' verified and completed!")
        else:
            QMessageBox.warning(self, "Verification Incomplete", f"Mission '{task_id}' verification finished: {res.get('stage')}")
        self.refresh_missions()

    def _abort_mission(self, task_id: str):
        self.orchestrator.abort_mission(task_id)
        self.refresh_missions()

    def _inject_directive(self):
        if not self.active_selected_task_id:
            QMessageBox.warning(self, "No Mission Selected", "Select a mission row from the table first.")
            return

        text = self.steer_input.toPlainText().strip()
        if text:
            self.orchestrator.inject_mission_feedback(self.active_selected_task_id, text)
            self.steer_input.clear()
            QMessageBox.information(self, "Directive Injected", "Mid-flight steering directive successfully queued into agent loop.")
            self._on_table_row_selected()
