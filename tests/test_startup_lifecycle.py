"""
PRUBETH IDE — Zero-Silent-Failure Launcher & Startup Lifecycle Test Suite
Validates PathResolver, Staged State Machine, Preflight Diagnostics,
Dependency-Ordered Service Initializer, Safe Mode, and Recovery Hooks.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

from core.startup.path_resolver import PathResolver, ResolvedPaths
from core.startup.state_machine import (
    StartupStateMachine,
    StartupState,
    TransitionRecord,
    InvalidStateTransitionError
)
from core.startup.preflight import (
    PreflightChecker,
    CheckStatus,
    PreflightReport,
    PreflightItem
)
from core.startup.service_initializer import (
    ServiceInitializer,
    ServiceStatus,
    ServiceDescriptor
)
from core.startup.launcher import AuthoritativeLauncher
from core.capability_registry import CapabilityRegistry


# =====================================================================
# 1. Path Resolution & CWD Independence Tests
# =====================================================================
def test_path_resolver_independent_of_cwd():
    """Verify PathResolver determines correct root and user directories regardless of CWD."""
    with tempfile.TemporaryDirectory() as tmp_cwd:
        old_cwd = Path.cwd()
        try:
            os.chdir(tmp_cwd)
            with tempfile.TemporaryDirectory() as custom_user:
                paths = PathResolver.resolve(custom_user_dir=Path(custom_user))
                assert paths.app_root.exists()
                assert (paths.app_root / "pyproject.toml").exists()
                assert paths.user_data_dir == Path(custom_user).resolve()
                assert paths.logs_dir.exists()
                assert paths.temp_dir.exists()
        finally:
            os.chdir(old_cwd)


# =====================================================================
# 2. Startup State Machine Transition Tests
# =====================================================================
def test_startup_state_machine_valid_sequential_transitions():
    """Verify sequential startup progression through all defined states."""
    sm = StartupStateMachine()
    assert sm.current_state == StartupState.NOT_STARTED

    sm.transition_to(StartupState.PREFLIGHT)
    assert sm.current_state == StartupState.PREFLIGHT

    sm.transition_to(StartupState.CONFIGURATION_READY)
    assert sm.current_state == StartupState.CONFIGURATION_READY

    sm.transition_to(StartupState.CORE_SERVICES_READY)
    assert sm.current_state == StartupState.CORE_SERVICES_READY

    sm.transition_to(StartupState.GUI_READY)
    assert sm.current_state == StartupState.GUI_READY

    sm.transition_to(StartupState.APPLICATION_READY)
    assert sm.current_state == StartupState.APPLICATION_READY
    assert sm.is_ready is True
    assert sm.is_failed is False

    sm.transition_to(StartupState.SHUTDOWN)
    assert sm.current_state == StartupState.SHUTDOWN

    summary = sm.get_summary()
    assert summary["transition_count"] == 6
    assert summary["total_startup_duration_ms"] >= 0.0


def test_startup_state_machine_rejects_illegal_jump():
    """Verify state machine raises InvalidStateTransitionError on out-of-order state jump."""
    sm = StartupStateMachine()
    # Cannot jump directly from NOT_STARTED to APPLICATION_READY without preflight
    with pytest.raises(InvalidStateTransitionError):
        sm.transition_to(StartupState.APPLICATION_READY)


def test_startup_state_machine_listeners_receive_events():
    """Verify registered callbacks receive state change notifications."""
    sm = StartupStateMachine()
    events = []

    def on_transition(from_st, to_st, record):
        events.append((from_st, to_st, record.duration_ms))

    sm.register_listener(on_transition)
    sm.transition_to(StartupState.PREFLIGHT)
    assert len(events) == 1
    assert events[0][0] == StartupState.NOT_STARTED
    assert events[0][1] == StartupState.PREFLIGHT


# =====================================================================
# 3. Preflight Checker Tests
# =====================================================================
def test_preflight_checker_clean_reference_run():
    """Verify preflight checker passes cleanly on reference installation."""
    paths = PathResolver.resolve()
    report = PreflightChecker.run_preflight(paths)
    assert isinstance(report, PreflightReport)
    assert report.can_proceed is True
    assert report.overall_status in (CheckStatus.PASS, CheckStatus.WARN)
    assert len(report.items) >= 6


def test_preflight_checker_catches_missing_mandatory_file():
    """Verify preflight checker reports FAIL when a mandatory entry point is missing."""
    with tempfile.TemporaryDirectory() as empty_root:
        with tempfile.TemporaryDirectory() as user_dir:
            fake_paths = ResolvedPaths(
                app_root=Path(empty_root),
                assets_dir=Path(empty_root) / "assets",
                user_data_dir=Path(user_dir),
                logs_dir=Path(user_dir) / "logs",
                config_file=Path(user_dir) / "settings.json",
                workspaces_dir=Path(user_dir) / "workspaces",
                temp_dir=Path(user_dir) / "temp",
                is_frozen=False
            )
            report = PreflightChecker.run_preflight(fake_paths)
            assert report.can_proceed is False
            assert report.overall_status == CheckStatus.FAIL
            failed_item = next((it for it in report.items if it.name == "Application Entry Point"), None)
            assert failed_item is not None
            assert failed_item.status == CheckStatus.FAIL
            assert failed_item.remediation_guidance != ""


def test_preflight_checker_backs_up_corrupt_settings():
    """Verify corrupt 0-byte settings are backed up and safe mode is triggered."""
    with tempfile.TemporaryDirectory() as user_dir:
        paths = PathResolver.resolve(custom_user_dir=Path(user_dir))
        # Create corrupted 0-byte configuration
        paths.config_file.write_text("", encoding="utf-8")

        report = PreflightChecker.run_preflight(paths, allow_safe_mode_recovery=True)
        # Should allow proceeding in safe mode with warning
        assert report.can_proceed is True
        assert report.requires_safe_mode is True
        
        # Verify backup file was created
        backup_files = list(paths.user_data_dir.glob("settings.corrupted.*.bak"))
        assert len(backup_files) >= 1


# =====================================================================
# 4. Dependency-Ordered Service Initializer Tests
# =====================================================================
def test_service_initializer_dependency_order_and_telemetry():
    """Verify all 13 service initialization stages run sequentially in dependency order."""
    with tempfile.TemporaryDirectory() as user_dir:
        paths = PathResolver.resolve(custom_user_dir=Path(user_dir))
        sm = StartupStateMachine()
        initializer = ServiceInitializer(paths=paths, state_machine=sm, safe_mode=True)
        try:
            success, descriptors = initializer.initialize_all()
            assert success is True
            assert len(descriptors) == 13

            # All mandatory descriptors must be READY
            for d in descriptors:
                if d.is_mandatory:
                    assert d.status == ServiceStatus.READY
                assert d.duration_ms >= 0.0

            # State machine should have reached ready state
            assert sm.is_ready is True
        finally:
            initializer.shutdown()


def test_service_initializer_isolates_optional_failure():
    """Verify an optional service failure transitions to DEGRADED_MODE without crashing."""
    with tempfile.TemporaryDirectory() as user_dir:
        paths = PathResolver.resolve(custom_user_dir=Path(user_dir))
        sm = StartupStateMachine()
        initializer = ServiceInitializer(paths=paths, state_machine=sm, safe_mode=False)
        try:
            # Inject a failure into optional plugin engine
            def faulty_plugins():
                raise RuntimeError("Simulated extension sandbox load failure")
            initializer._init_plugins_engine = faulty_plugins

            success, descriptors = initializer.initialize_all()
            assert success is True # Core IDE still initializes!
            plugin_desc = next((d for d in descriptors if d.service_id == "plugins_engine"), None)
            assert plugin_desc is not None
            assert plugin_desc.status == ServiceStatus.DEGRADED
            assert sm.current_state == StartupState.DEGRADED_MODE
        finally:
            initializer.shutdown()


# =====================================================================
# 5. Authoritative Launcher CLI & Argument Tests
# =====================================================================
def test_authoritative_launcher_preflight_only():
    """Verify --preflight-only runs verification and exits with code 0."""
    launcher = AuthoritativeLauncher(["--preflight-only"])
    exit_code = launcher.launch()
    assert exit_code == 0


def test_authoritative_launcher_headless_mode():
    """Verify --headless executes complete service startup and exits with code 0."""
    launcher = AuthoritativeLauncher(["--headless", "--safe-mode"])
    exit_code = launcher.launch()
    assert exit_code == 0
    assert launcher.state_machine.is_ready is True


def test_authoritative_launcher_reset_settings_flag():
    """Verify --reset-settings creates backup and leaves clean config."""
    with tempfile.TemporaryDirectory() as user_dir:
        paths = PathResolver.resolve(custom_user_dir=Path(user_dir))
        paths.config_file.write_text('{"custom_test": true}', encoding="utf-8")

        launcher = AuthoritativeLauncher(["--reset-settings", "--headless"])
        launcher.paths = paths
        exit_code = launcher.launch()
        assert exit_code == 0

        # Verify backup was created
        backups = list(paths.user_data_dir.glob("settings.backup.*.bak"))
        assert len(backups) >= 1


# =====================================================================
# 6. Universal Capability Registry Integration
# =====================================================================
def test_capability_registry_startup_orchestrator():
    """Verify startup orchestrator is registered and queryable in CapabilityRegistry."""
    registry = CapabilityRegistry.get_instance()
    cap = registry.get("startup.orchestrator")
    assert cap is not None
    assert cap.status == "implemented"
    assert "startup.run_preflight" in cap.commands
