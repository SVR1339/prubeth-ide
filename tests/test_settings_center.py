"""
Unit tests for ui/settings_center.py, hardware_autotuner.py, and connector_gateway.py
Pillars 2, 4, 6 & 7: Architecture, Design System, Quality & Operations Governance
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

from horizon_engine.hardware_autotuner import HardwareAutoTuner, TuningResult, HardwareProfile
from horizon_engine.connector_gateway import ConnectorGateway, ConnectedService
from ui.settings_center import SettingsStore, SettingsCenterDialog, DEFAULTS

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt5.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)


def test_hardware_autotuner_detection():
    """Verify hardware discovery returns valid non-empty host specs and a recognized tier."""
    profile = HardwareAutoTuner.detect_hardware()
    assert profile.os_name in ("Windows", "Linux", "Darwin")
    assert profile.cpu_threads >= 1
    assert profile.ram_total_mb > 1000
    assert profile.tier_name in ("ULTRA_LOW", "BALANCED_LAPTOP", "HIGH_PERFORMANCE", "WORKSTATION_PRO")


def test_hardware_autotuner_synthesis_and_apply():
    """Verify synthesis generates safe performance parameters and merges into settings."""
    tuning = HardwareAutoTuner.synthesize_tuning()
    assert isinstance(tuning, TuningResult)
    assert "max_parallel_agents" in tuning.settings_delta
    assert "cache_mb" in tuning.settings_delta
    assert tuning.diagnostic_summary != ""

    settings = {"performance": {}, "agents": {}}
    updated = HardwareAutoTuner.apply_to_settings(settings, tuning)
    assert "cuda_vram_limit_mb" in updated
    assert "gguf_gpu_layers" in updated
    assert updated["hardware_tier"] == tuning.suggested_tier


def test_connector_gateway_toolchains_discovery():
    """Verify toolchains probe finds at least Python runtime."""
    toolchains = ConnectorGateway.probe_developer_toolchains()
    assert len(toolchains) >= 5
    python_svc = next((s for s in toolchains if s.service_id == "python"), None)
    assert python_svc is not None
    assert python_svc.status == "available"


def test_connector_gateway_local_ai_probe():
    """Verify local AI probing correctly returns status for standard ports without crashing."""
    results = ConnectorGateway.probe_local_ai_runtimes()
    assert len(results) >= 5
    ollama_svc = next((s for s in results if s.service_id == "ollama"), None)
    assert ollama_svc is not None
    assert ollama_svc.status in ("online", "offline")


def test_connector_gateway_full_scan():
    """Verify full system scan compiles clean metadata dict."""
    scan = ConnectorGateway.full_system_scan()
    assert "total_local_ai_scanned" in scan
    assert "available_toolchains_count" in scan
    assert scan["available_toolchains_count"] >= 1


def test_settings_store_persistence_and_legacy_bridge():
    """Verify SettingsStore writes atomically and bridges flat legacy keys for local_ai_studio_pro."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "settings.json"
        store = SettingsStore(path=test_path)
        store.data["performance"]["gguf_gpu_layers"] = 33
        store.data["performance"]["cuda_vram_limit_mb"] = 4096
        store.save()

        assert test_path.exists()
        # Verify legacy flat keys were exported for local_ai_studio_pro
        assert store.data["gguf_gpu_layers"] == 33
        assert store.data["cuda_vram_limit_mb"] == 4096
        assert store.data["max_agent_steps"] == 30
        assert "editor_tab_size" in store.data


def test_settings_center_dialog_offscreen_instantiation():
    """Verify SettingsCenterDialog instantiates cleanly with all 14 categories and can collect data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "settings.json"
        store = SettingsStore(path=test_path)
        dlg = SettingsCenterDialog(store=store)

        assert dlg.category_list.count() == 14
        assert len(dlg.controls) >= 40
        assert hasattr(dlg, "btn_autotune")

        # Test collecting controls
        data = dlg._collect_controls()
        assert "appearance" in data
        assert "performance" in data
        assert "models" in data
        assert "security" in data
