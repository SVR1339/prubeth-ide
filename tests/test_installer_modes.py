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
