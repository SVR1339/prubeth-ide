"""
Tests for SUKHI IDE Presentation & UI Widgets:
CheckpointsWidget, DiagnosticsWidget, and DebugPanelWidget.
"""
import pytest
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from core.workspace import WorkspaceGuard
from workspace.checkpoints import CheckpointManager
from ui.checkpoints_widget import CheckpointsWidget
from ui.diagnostics_widget import DiagnosticsWidget
from ui.debug_widget import DebugPanelWidget
from debugging.dap_client import SourceBreakpoint


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_checkpoints_widget_lifecycle(qapp, tmp_path):
    guard = WorkspaceGuard(tmp_path)
    mgr = CheckpointManager(guard)

    test_file = tmp_path / "hello.py"
    test_file.write_text("print('v1')", encoding="utf-8")

    c_id = mgr.begin_checkpoint("Initial state")
    mgr.track_file_before_edit(c_id, str(test_file))
    test_file.write_text("print('v2')", encoding="utf-8")
    mgr.track_file_after_edit(c_id, str(test_file))

    widget = CheckpointsWidget(mgr)
    assert widget.list_checkpoints.count() == 1

    item = widget.list_checkpoints.item(0)
    widget._on_checkpoint_clicked(item)

    assert widget.tree_files.topLevelItemCount() == 1
    assert widget.btn_rollback.isEnabled() is True


def test_diagnostics_widget_filtering(qapp):
    widget = DiagnosticsWidget()

    uri = "file:///c:/project/main.py"
    sample_diags = [
        {
            "severity": 1,
            "message": "SyntaxError: invalid syntax",
            "range": {"start": {"line": 10, "character": 4}},
            "source": "flake8"
        },
        {
            "severity": 2,
            "message": "Unused import 'math'",
            "range": {"start": {"line": 2, "character": 0}},
            "source": "flake8"
        },
        {
            "severity": 3,
            "message": "Consider using list comprehension",
            "range": {"start": {"line": 20, "character": 8}},
            "source": "pylint"
        }
    ]

    widget.update_diagnostics(uri, sample_diags)
    assert widget.tree.topLevelItemCount() == 3

    # Filter to errors only
    widget.severity_combo.setCurrentText("Errors Only")
    assert widget.tree.topLevelItemCount() == 1

    # Filter by search text
    widget.severity_combo.setCurrentText("All Severities")
    widget.search_input.setText("Unused")
    assert widget.tree.topLevelItemCount() == 1

    # Clear filter
    widget.search_input.clear()
    assert widget.tree.topLevelItemCount() == 3


def test_debug_panel_widget_state(qapp):
    widget = DebugPanelWidget()

    widget.set_session_status("Paused on breakpoint")
    assert "Paused" in widget.status_lbl.text()

    widget.update_call_stack([
        {"name": "process_data", "source": {"name": "app.py", "path": "/path/app.py"}, "line": 42},
        {"name": "main", "source": {"name": "main.py", "path": "/path/main.py"}, "line": 10}
    ])
    assert widget.tree_stack.topLevelItemCount() == 2

    widget.update_variables([
        {"name": "x", "value": "100", "type": "int"},
        {"name": "name", "value": "'Sukhi'", "type": "str"}
    ])
    assert widget.tree_vars.topLevelItemCount() == 2

    widget.update_breakpoints([
        SourceBreakpoint(line=42, condition="x > 50")
    ])
    assert widget.tree_bp.topLevelItemCount() == 1
