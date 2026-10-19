"""
Unit tests for Setup Wizard Full (Recommended) vs Custom Installation Modes.
Verifies wizard page initialization, field registration, mode switching,
and selective component installation logic.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
INSTALLER_DIR = ROOT_DIR / "installer"
sys.path.insert(0, str(INSTALLER_DIR))

from setup_wizard import (
    SetupWizard, InstallTypePage, DirectoryPage, ReadyPage,
    InstallWorker, APP_NAME, APP_VERSION
)


@pytest.fixture(scope="module")
def qapp():
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if not app:
        app = QApplication([sys.argv[0], "-platform", "offscreen"])
    return app


def test_install_type_page_defaults(qapp):
    """Verify that InstallTypePage defaults to Full Installation (Recommended)."""
    page = InstallTypePage()
    assert page.rb_full.isChecked() is True
    assert page.rb_custom.isChecked() is False

    # In Full mode, all components are checked and locked to full profile
    assert page.chk_core.isChecked() is True
    assert page.chk_lexers.isChecked() is True
    assert page.chk_models.isChecked() is True
    assert page.chk_desktop.isChecked() is True
    assert page.chk_startmenu.isChecked() is True
    assert page.chk_path.isChecked() is True
    assert page.chk_uninstaller.isChecked() is True

    # Custom options should be disabled in Full mode
    assert page.chk_lexers.isEnabled() is False
    assert page.chk_models.isEnabled() is False


def test_install_type_page_custom_mode_toggle(qapp):
    """Verify that switching to Custom Installation enables granular component toggles."""
    page = InstallTypePage()
    page.rb_custom.setChecked(True)

    assert page.rb_custom.isChecked() is True
    # Components should now be enabled for customization
    assert page.chk_lexers.isEnabled() is True
    assert page.chk_models.isEnabled() is True
    assert page.chk_desktop.isEnabled() is True
    assert page.chk_startmenu.isEnabled() is True
    assert page.chk_path.isEnabled() is True
    assert page.chk_uninstaller.isEnabled() is True

    # Core engine must always remain mandatory
    assert page.chk_core.isEnabled() is False
    assert page.chk_core.isChecked() is True

    # User unchecks optional components
    page.chk_models.setChecked(False)
    assert page.chk_models.isChecked() is False


def test_setup_wizard_page_sequence(qapp):
    """Verify the 6-page enterprise wizard sequence."""
    wizard = SetupWizard()
    assert wizard.pageIds() == [0, 1, 2, 3, 4, 5]
    assert wizard.windowTitle() == f"{APP_NAME} IDE Setup — v{APP_VERSION}"


def test_directory_page_space_calculation(qapp, tmp_path):
    """Verify DirectoryPage updates space requirement and queries disk usage."""
    page = DirectoryPage()
    page.dir_input.setText(str(tmp_path))
    page.update_disk_space()

    assert "Space Required" in page.lbl_space_req.text()
    assert "Space Available" in page.lbl_space_avail.text()
    assert "✓ Sufficient disk space is available." in page.lbl_space_status.text()


def test_showroom_experience_priming(tmp_path, monkeypatch):
    """Verify that _prime_showroom_experience pre-seeds user settings, model profiles, and workbench patches."""
    import json
    mock_appdata = tmp_path / "AppData" / "Roaming"
    monkeypatch.setenv("APPDATA", str(mock_appdata))

    target_dir = tmp_path / "PRUBETH_IDE"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Setup mock workbench js and product.json
    bench_dir = target_dir / "resources" / "app" / "out" / "vs" / "workbench"
    bench_dir.mkdir(parents=True, exist_ok=True)
    bench_js = bench_dir / "workbench.desktop.main.js"
    bench_js.write_text("class ChatService { chatRequiresSetup(){ return this.needsSetup; } }", encoding="utf-8")

    prod_json = target_dir / "resources" / "app" / "product.json"
    prod_json.write_text(json.dumps({"nameShort": "PRUBETH"}), encoding="utf-8")

    worker = InstallWorker(target_dir=target_dir)
    worker._prime_showroom_experience()

    # 1. Verify User settings.json created with zero-friction showroom defaults
    user_settings = mock_appdata / "PRUBETH" / "User" / "settings.json"
    assert user_settings.exists()
    settings_data = json.loads(user_settings.read_text(encoding="utf-8"))
    assert settings_data["chat.commandCenter.enabled"] is True
    assert settings_data["update.mode"] == "none"
    assert settings_data["telemetry.telemetryLevel"] == "off"

    # 2. Verify chatLanguageModels.json created
    models_file = mock_appdata / "PRUBETH" / "User" / "chatLanguageModels.json"
    assert models_file.exists()
    models_data = json.loads(models_file.read_text(encoding="utf-8"))
    assert isinstance(models_data, list)
    assert len(models_data) > 0

    # 3. Verify workbench patch eliminated setup modal
    patched_js = bench_js.read_text(encoding="utf-8")
    assert "chatRequiresSetup(){return false;" in patched_js

    # 4. Verify product.json has chatSetup.disabled and defaultChatAgent
    patched_prod = json.loads(prod_json.read_text(encoding="utf-8"))
    assert patched_prod["chatSetup"]["disabled"] is True
    assert patched_prod["defaultChatAgent"]["extensionId"] == "prubeth.ai-assistant"


def test_primary_executable_resolution(tmp_path):
    """Verify dynamic executable and shortcut target discovery."""
    target_dir = tmp_path / "PRUBETH"
    target_dir.mkdir(parents=True, exist_ok=True)
    bat = target_dir / "PRUBETH.bat"
    bat.write_text("@echo off", encoding="utf-8")

    worker = InstallWorker(target_dir=target_dir)

    # With launcher bat present in target_dir, resolves to it
    exe, work_dir, icon = worker._resolve_primary_executable()
    assert exe == bat

    # When PRUBETH.exe exists, it takes precedence as the primary binary
    primary_exe = target_dir / "PRUBETH.exe"
    primary_exe.write_text("MZ...", encoding="utf-8")

    exe, work_dir, icon = worker._resolve_primary_executable()
    assert exe == primary_exe
    assert work_dir == target_dir

