"""PRUBETH IDE - Startup and Initialization Failure Chaos Tests
============================================================
Tests resilience against missing config files, corrupted settings,
unavailable model servers, missing directories, and invalid schemas.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from tests.reliability.helpers.crash_harness import (
    DisposableWorkspace,
    IsolatedConfigHarness,
    FaultInjector,
    timed_operation,
)
from core.configuration_service import ConfigurationService, ConfigScope
from core.capability_registry import CapabilityRegistry
from core.feature_flags import FeatureFlagService


def test_startup_with_missing_config_file():
    """Startup must synthesize default settings without crashing when file does not exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        non_existent_config = Path(tmp_dir) / "missing_settings.json"
        assert not non_existent_config.exists()

        config_service = ConfigurationService(user_config_path=str(non_existent_config))
        with timed_operation(2.0):
            val = config_service.get_effective("theme")
            assert val is not None
            assert val == "Dark"


def test_startup_with_truncated_corrupt_config():
    """Startup must quarantine corrupted JSON and safely fall back to clean defaults."""
    with IsolatedConfigHarness() as harness:
        FaultInjector.corrupt_json_file(harness.settings_file)
        assert harness.settings_file.exists()

        config_service = ConfigurationService(user_config_path=str(harness.settings_file))
        with timed_operation(2.0):
            val = config_service.get_effective("theme")
            assert val == "Dark"


def test_startup_with_unsupported_future_schema_version():
    """Startup must handle future schema versions gracefully without crashing."""
    with IsolatedConfigHarness() as harness:
        future_config = {
            "schema_version": 999,
            "quantum_acceleration": True,
            "theme": "Dark",
        }
        harness.settings_file.write_text(json.dumps(future_config), encoding="utf-8")

        config_service = ConfigurationService(user_config_path=str(harness.settings_file))
        assert config_service.get_effective("theme") == "Dark"


def test_startup_with_missing_workspace_directory():
    """Initializing with a deleted/non-existent workspace path must handle path cleanly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        missing_ws = Path(tmp_dir) / "vanished_workspace"
        assert not missing_ws.exists()

        from core.workspace import WorkspaceGuard
        guard = WorkspaceGuard(missing_ws)
        assert guard.root.exists()


def test_subsystem_registration_idempotency_under_rapid_restart():
    """Subsystems must withstand repeated rapid re-registration without leaking or crashing."""
    with timed_operation(3.0):
        for _ in range(10):
            reg = CapabilityRegistry()
            caps = reg.list_all()
            assert len(caps) > 10
            matches = reg.search("editor")
            assert len(matches) >= 1


def test_feature_flags_resilience_to_corrupted_state():
    """Feature flag manager must reset to safe defaults when state file is corrupted."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_path = Path(tmp_dir) / "flags.json"
        FaultInjector.inject_invalid_bytes(state_path)

        manager = FeatureFlagService(storage_path=state_path)
        assert manager.is_enabled("preview.hardware_autotuner") is True
