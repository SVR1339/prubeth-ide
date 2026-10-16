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


def test_error_vault_widget(qapp, tmp_path):
    from core.error_vault import ErrorVault, ErrorSeverity
    from ui.error_vault_widget import ErrorVaultWidget

    test_vault = ErrorVault(vault_dir=tmp_path / "vault")
    rec1 = test_vault.record_error(
        message="Null pointer dereference in memory buffer",
        error_type="NullReferenceError",
        subsystem="CORE",
        severity=ErrorSeverity.CRITICAL.value,
        file_path="src/buffer.py",
        line_number=88
    )
    rec2 = test_vault.record_error(
        message="Network timeout to API",
        error_type="TimeoutError",
        subsystem="AI_AGENT",
        severity=ErrorSeverity.WARNING.value,
        file_path="src/net.py",
        line_number=22
    )

    widget = ErrorVaultWidget(vault=test_vault)
    assert widget.card_total.lbl_value.text() == "2"
    assert widget.card_unresolved.lbl_value.text() == "2"
    assert widget.tree.topLevelItemCount() == 2

    # Test filtering by search text
    widget.search_input.setText("Null pointer")
    assert widget.tree.topLevelItemCount() == 1

    widget.search_input.clear()
    assert widget.tree.topLevelItemCount() == 2

    # Test selection and jumping to code
    widget.tree.setCurrentItem(widget.tree.topLevelItem(0))
    jump_called = []
    widget.navigate_to_source.connect(lambda f, l, c: jump_called.append((f, l, c)))
    widget._on_jump_code_clicked()
    assert len(jump_called) == 1
    assert jump_called[0][1] in (88, 22)

    # Test solve with AI signal
    solve_called = []
    widget.solve_error_requested.connect(lambda rec: solve_called.append(rec))
    widget._on_solve_ai_clicked()
    assert len(solve_called) == 1
    assert solve_called[0].error_id in (rec1.error_id, rec2.error_id)

