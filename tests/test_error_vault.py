"""
Tests for PRUBETH IDE — Bulletproof ErrorVault Subsystem
========================================================
Validates error recording, fingerprinting, deduplication, JSONL ledger persistence,
daily report aggregation, and exception hook integrations.
"""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
import pytest

from core.error_vault import (
    ErrorVault, ErrorRecord, ErrorSeverity, ErrorStatus,
    compute_error_fingerprint, install_global_hooks
)


@pytest.fixture
def temp_vault_dir():
    d = tempfile.mkdtemp(prefix="prubeth_test_vault_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def vault(temp_vault_dir):
    return ErrorVault.reset_instance_for_testing(vault_dir=temp_vault_dir)


def test_error_fingerprint_normalization():
    # Varying memory addresses should yield identical fingerprints
    fp1 = compute_error_fingerprint("ZeroDivisionError", "calc.py", 42, "division by zero at 0x7ffd12ab45")
    fp2 = compute_error_fingerprint("ZeroDivisionError", "calc.py", 42, "division by zero at 0x99aa56ef00")
    assert fp1 == fp2
    assert len(fp1) == 16


def test_record_error_and_persistence(vault, temp_vault_dir):
    rec = vault.record_error(
        message="Simulated connection failure to model engine",
        error_type="ConnectionError",
        traceback_str='  File "ai/engine.py", line 105, in connect\n    raise ConnectionError("timeout")',
        subsystem="AI_AGENT",
        severity=ErrorSeverity.ERROR.value
    )

    assert rec.error_id.startswith("BUG-")
    assert rec.occurrence_count == 1
    assert rec.status == ErrorStatus.UNRESOLVED.value
    assert rec.subsystem == "AI_AGENT"
    assert rec.file_path == "ai/engine.py"
    assert rec.line_number == 105

    # Check that ledger file and index file exist on disk
    assert (temp_vault_dir / "error_ledger.jsonl").exists()
    assert (temp_vault_dir / "error_index.json").exists()

    # Re-instantiate vault to verify reload from disk
    vault2 = ErrorVault(vault_dir=temp_vault_dir)
    reloaded = vault2.get_error(rec.error_id)
    assert reloaded is not None
    assert reloaded.error_id == rec.error_id
    assert reloaded.message == rec.message
    assert reloaded.occurrence_count == 1


def test_error_deduplication_and_occurrence_counting(vault):
    # Log same error three times
    rec1 = vault.record_error(
        message="Index out of bounds in AST visitor",
        error_type="IndexError",
        file_path="core/parser.py",
        line_number=55
    )
    rec2 = vault.record_error(
        message="Index out of bounds in AST visitor",
        error_type="IndexError",
        file_path="core/parser.py",
        line_number=55
    )
    rec3 = vault.record_error(
        message="Index out of bounds in AST visitor",
        error_type="IndexError",
        file_path="core/parser.py",
        line_number=55
    )

    assert rec1.error_id == rec2.error_id == rec3.error_id
    assert rec3.occurrence_count == 3
    assert len(vault.get_all_errors()) == 1


def test_record_exception_automated_traceback(vault):
    try:
        1 / 0
    except ZeroDivisionError as e:
        rec = vault.record_exception(e, subsystem="CALCULATIONS")

    assert rec.error_type == "ZeroDivisionError"
    assert "division by zero" in rec.message
    assert "test_error_vault.py" in str(rec.file_path)
    assert rec.line_number is not None
    assert rec.subsystem == "CALCULATIONS"


def test_resolve_and_reopen_regression(vault):
    rec = vault.record_error("Flaky buffer overflow", error_type="BufferError")
    e_id = rec.error_id

    # Resolve error
    ok = vault.resolve_error(e_id, notes="Fixed by increasing max buffer limit to 64MB", resolved_by="Engineer")
    assert ok is True

    resolved_rec = vault.get_error(e_id)
    assert resolved_rec.status == ErrorStatus.RESOLVED.value
    assert "Fixed by increasing max buffer limit" in resolved_rec.remediation_notes
    assert len(vault.get_unresolved_errors()) == 0

    # Simulate same error happening again tomorrow -> Regression detected!
    rec_regressed = vault.record_error("Flaky buffer overflow", error_type="BufferError")
    assert rec_regressed.error_id == e_id
    assert rec_regressed.status == ErrorStatus.UNRESOLVED.value
    assert "REGRESSION DETECTED" in rec_regressed.remediation_notes
    assert len(vault.get_unresolved_errors()) == 1


def test_daily_report_generation(vault, temp_vault_dir):
    # Record multiple errors
    vault.record_error("Issue A", error_type="TypeError", subsystem="CORE", severity="CRITICAL")
    vault.record_error("Issue B", error_type="KeyError", subsystem="UI", severity="WARNING")
    vault.record_error("Issue C", error_type="TimeoutError", subsystem="AI_AGENT", severity="ERROR")

    # Generate daily report
    report = vault.generate_daily_report()
    assert report["total_unique_bugs_active"] == 3
    assert report["unresolved"] == 3
    assert report["severity_breakdown"]["CRITICAL"] == 1
    assert report["severity_breakdown"]["WARNING"] == 1
    assert report["severity_breakdown"]["ERROR"] == 1
    assert report["subsystem_breakdown"]["CORE"] == 1

    # Check generated files
    daily_dir = temp_vault_dir / "daily_reports"
    json_reports = list(daily_dir.glob("daily_report_*.json"))
    md_reports = list(daily_dir.glob("daily_report_*.md"))
    assert len(json_reports) == 1
    assert len(md_reports) == 1

    md_text = md_reports[0].read_text(encoding="utf-8")
    assert "Daily Error & Reliability Audit Report" in md_text
    assert "Issue A" in md_text


def test_thread_exception_capture(vault):
    import threading

    def bad_worker():
        raise ValueError("Background thread catastrophic failure")

    t = threading.Thread(target=bad_worker, name="WorkerThread-99")
    
    # We install hooks and simulate the thread exception
    install_global_hooks()
    
    # Simulate threading.excepthook invocation
    from core.error_vault import _global_threading_excepthook
    
    class FakeArgs:
        exc_type = ValueError
        exc_value = ValueError("Background thread catastrophic failure")
        exc_traceback = None
        thread = t

    _global_threading_excepthook(FakeArgs())

    errors = vault.get_all_errors()
    assert any("Background thread catastrophic failure" in e.message for e in errors)
    matching = [e for e in errors if "Background thread catastrophic failure" in e.message][0]
    assert matching.subsystem == "BACKGROUND_WORKER"

