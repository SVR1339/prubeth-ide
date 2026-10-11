"""PRUBETH IDE - Configuration and Settings Recovery Chaos Tests
=============================================================
Exercises atomic file persistence, concurrent reads/writes, multi-scope
precedence conflicts, locked organization policies, and corrupted state recovery.
"""

import concurrent.futures
import json
import os
import tempfile
from pathlib import Path
import pytest

from tests.reliability.helpers.crash_harness import (
    IsolatedConfigHarness,
    FaultInjector,
    timed_operation,
)
from core.configuration_service import ConfigurationService, ConfigScope
from ui.settings_center import SettingsStore


def test_atomic_settings_persistence_and_backup():
    """SettingsStore must persist atomically and preserve valid configuration on write."""
    with IsolatedConfigHarness() as harness:
        store = SettingsStore(str(harness.settings_file))
        assert store.get("theme") == "Obsidian Slate"

        # Update and save
        store.set("font_size", 14)
        store.set("telemetry_level", "OFF")
        store.save()

        # Re-read directly from disk
        raw = json.loads(harness.settings_file.read_text(encoding="utf-8"))
        assert raw["font_size"] == 14
        assert raw["telemetry_level"] == "OFF"


def test_recovery_from_zero_byte_empty_config():
    """Empty 0-byte configuration file must trigger recovery to defaults."""
    with IsolatedConfigHarness() as harness:
        harness.settings_file.write_text("", encoding="utf-8")
        assert harness.settings_file.stat().st_size == 0

        config_service = ConfigurationService(user_config_path=str(harness.settings_file))
        val = config_service.get_effective("theme")
        assert val == "Dark"


def test_concurrent_configuration_writes_no_corruption():
    """Simultaneous threads writing different keys must not corrupt the configuration."""
    with IsolatedConfigHarness() as harness:
        config_service = ConfigurationService(user_config_path=str(harness.settings_file))

        def write_worker(idx: int):
            config_service.set(f"test_key_{idx}", f"val_{idx}", ConfigScope.SESSION)
            return config_service.get_effective(f"test_key_{idx}")

        with timed_operation(5.0):
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(write_worker, i) for i in range(24)]
                results = [f.result() for f in futures]

        assert len(results) == 24
        for idx, res in enumerate(results):
            assert res == f"val_{idx}"


def test_organization_policy_lock_enforcement():
    """Organization scope locks must prevent user overrides from taking effect."""
    with IsolatedConfigHarness() as harness:
        config_service = ConfigurationService(user_config_path=str(harness.settings_file))

        # Organization locks telemetry to OFF
        config_service.set("telemetry_level", "OFF", ConfigScope.ORGANIZATION)

        # User attempts to enable telemetry; must raise PermissionError
        with pytest.raises(PermissionError):
            config_service.set("telemetry_level", "FULL", ConfigScope.USER)

        # Effective value must remain organization-locked
        assert config_service.get_effective("telemetry_level") == "OFF"
        assert config_service.is_locked_by_org("telemetry_level") is True
