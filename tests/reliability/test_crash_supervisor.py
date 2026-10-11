"""
Unit & Integration Tests for Independent Crash Supervisor
==========================================================
Verifies out-of-process watchdog supervision, exit code analysis,
bounded restart limits, and structured JSON crash dump persistence.
"""
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.crash_supervisor import CrashSupervisor, CrashReport


def test_supervisor_exit_code_interpretation():
    supervisor = CrashSupervisor()
    assert supervisor.get_exit_reason(0) == "CLEAN_SHUTDOWN"
    assert supervisor.get_exit_reason(1) == "UNHANDLED_PYTHON_EXCEPTION"
    assert supervisor.get_exit_reason(-9) == "SIGKILL_OOM_TERMINATION"
    assert supervisor.get_exit_reason(137) == "SIGKILL_OOM_TERMINATION"
    assert supervisor.get_exit_reason(-11) == "SIGSEGV_SEGMENTATION_FAULT"
    assert supervisor.get_exit_reason(3221225477) == "WINDOWS_ACCESS_VIOLATION_0xC0000005"
    assert supervisor.get_exit_reason(3221225725) == "WINDOWS_STACK_OVERFLOW_0xC00000FD"
    assert "ABNORMAL_EXIT_CODE" in supervisor.get_exit_reason(42)


def test_supervisor_bounded_restart_policy():
    """Verify that supervisor limits restarts within rolling time window to avoid restart loops."""
    supervisor = CrashSupervisor(max_restarts=3, restart_window_seconds=10.0)

    # Initial state
    assert supervisor.can_restart() is True

    # 1st restart
    supervisor.restart_history.append(time.time())
    assert supervisor.can_restart() is True

    # 2nd restart
    supervisor.restart_history.append(time.time())
    assert supervisor.can_restart() is True

    # 3rd restart - threshold reached
    supervisor.restart_history.append(time.time())
    assert supervisor.can_restart() is False

    # Simulate time passing beyond window
    now = time.time() + 15.0
    supervisor.clean_old_restarts(now)
    assert len(supervisor.restart_history) == 0
    assert supervisor.can_restart() is True


def test_supervisor_crash_report_persistence(tmp_path):
    """Verify structured JSON crash report generation and integrity."""
    reports_dir = tmp_path / "reports"
    supervisor = CrashSupervisor(reports_dir=reports_dir)

    report = CrashReport(
        timestamp=1700000000.0,
        iso_time="2026-10-11T12:00:00Z",
        exit_code=1,
        exit_reason="UNHANDLED_PYTHON_EXCEPTION",
        uptime_seconds=42.5,
        restart_count=1,
        safe_mode_activated=False,
        peak_memory_mb=185.4,
        stdout_tail=["Output line 1", "Output line 2"],
        stderr_tail=["Traceback (most recent call last):", "RuntimeError: Test Error"],
        diagnostic_details={"test_key": "test_val"}
    )

    out_file = supervisor.persist_crash_report(report)
    assert out_file.exists()

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["exit_code"] == 1
    assert data["exit_reason"] == "UNHANDLED_PYTHON_EXCEPTION"
    assert data["peak_memory_mb"] == 185.4
    assert len(data["stderr_tail"]) == 2
    assert "Traceback" in data["stderr_tail"][0]
