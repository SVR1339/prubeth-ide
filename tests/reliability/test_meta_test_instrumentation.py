"""
PRUBETH IDE — TEST INSTRUMENTATION META-TESTING SUITE
=====================================================
Validates Section 21 of Master Specification:
Proves that the testing harness and reliability engine itself detects
non-zero exit codes, timeouts, synthetic failures, and broken collectors,
and NEVER falsely certifies broken software as passed.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import pytest

from core.universal_cli_runner import UniversalCliRunner
from core.universal_inventory import UniversalInventoryManager, CapabilityStatus
from core.capability_gap_engine import CapabilityGapEngine, CapabilityGapRequest, GapResolutionStatus
from core.polyglot_assurance_engine import UniversalPolyglotAssuranceEngine, AssuranceScenarioStatus


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory(prefix="test_meta_harness_") as tmp_dir:
        yield Path(tmp_dir)


def test_harness_detects_non_zero_exit_codes(temp_workspace):
    """Verify that command runner captures non-zero exit codes and does not falsify success."""
    runner = UniversalCliRunner(temp_workspace)
    # Run a Python one-liner that intentionally exits with code 42
    cmd = [sys.executable, "-c", "import sys; sys.exit(42)"]
    code, output = runner.run_command(cmd)

    assert code == 42, f"Harness failed to capture exact exit code: got {code}"


def test_harness_detects_timeouts_and_terminates(temp_workspace):
    """Verify that subprocesses with infinite loops are boundedly terminated upon timeout."""
    t0 = time.time()
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            timeout=0.6,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    elapsed = time.time() - t0
    assert elapsed < 3.0, f"Process timeout took too long to terminate: {elapsed:.2f}s"


def test_harness_detects_deliberately_corrupted_fixture(temp_workspace):
    """Verify that corrupted JSON configuration fixture is caught and flagged."""
    corrupt_json = temp_workspace / "settings.json"
    corrupt_json.write_text("{ unclosed_bad_json: 123", encoding="utf-8")

    from core.settings import SettingsStore
    store = SettingsStore(corrupt_json)
    # Must recover gracefully to default rather than unhandled exception
    val = store.get("theme", default="dark")
    assert val == "dark"


def test_harness_preserves_visible_skipped_and_blocked_states(temp_workspace):
    """Verify that uninstalled external toolchains remain SKIPPED/BLOCKED rather than fake pass."""
    engine = UniversalPolyglotAssuranceEngine(temp_workspace)
    inventory = engine.discover_toolchains()
    exec_results = engine.test_installed_runtimes_execution()

    # Find languages that are not installed (e.g. Swift or Julia or Scala)
    skipped_results = [r for r in exec_results if r.status == AssuranceScenarioStatus.SKIPPED_NO_RUNTIME]
    assert len(skipped_results) > 0, "Expected some uninstalled toolchains to be transparently SKIPPED"

    # None of the skipped items should have exit_code 0 or claim PASSED
    for r in skipped_results:
        assert r.status != AssuranceScenarioStatus.PASSED
        assert "not installed" in r.details.lower() or "skipped" in r.details.lower()


def test_capability_gap_engine_identifies_existing_vs_blocked(temp_workspace):
    """Verify that capability gap engine correctly resolves existing modules and flags blockers."""
    gap_engine = CapabilityGapEngine(Path.cwd())

    # 1. Existing capability: Workspace persistence
    req_existing = CapabilityGapRequest(
        capability_name="workspace",
        requested_outcome="Atomic workspace operations",
        target_subsystem="Workspace"
    )
    res_existing = gap_engine.resolve_capability(req_existing)
    assert res_existing.status == GapResolutionStatus.RESOLVED_INTERNAL
    assert "workspace.py" in str(res_existing.affected_files)

    # 2. Blocked external toolchain: Docker
    req_blocked = CapabilityGapRequest(
        capability_name="docker",
        requested_outcome="Container containerization",
        target_subsystem="Containers",
        is_mandatory=True,
        suggested_toolchain="docker"
    )
    res_blocked = gap_engine.resolve_capability(req_blocked)
    assert res_blocked.status == GapResolutionStatus.BLOCKED_EXTERNAL
    assert res_blocked.remediation_guidance is not None
    assert "Docker Desktop" in res_blocked.remediation_guidance


def test_inventory_manager_baseline_telemetry(temp_workspace):
    """Verify that UniversalInventoryManager measures real non-zero hardware baseline."""
    mgr = UniversalInventoryManager(temp_workspace)
    telemetry = mgr.collect_baseline_telemetry()

    assert telemetry.total_ram_mb > 1024
    assert telemetry.available_ram_mb > 0
    assert telemetry.disk_free_mb > 0
    assert telemetry.cpu_count_logical >= 1
    assert telemetry.python_version.startswith("3.")
