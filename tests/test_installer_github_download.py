"""
Tests for Setup Wizard GitHub Live Download and Mirror Recovery Subsystem.
Verifies that when no local payload is present on an end-user machine,
InstallWorker successfully downloads the payload archive from GitHub mirrors,
unpacks it, verifies integrity, and completes installation.
"""
import sys
import io
import zipfile
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
INSTALLER_DIR = ROOT_DIR / "installer"
sys.path.insert(0, str(INSTALLER_DIR))

from setup_wizard import InstallWorker, APP_VERSION, ONLINE_PAYLOAD_URLS


def test_online_payload_urls_configured():
    """Verify that multiple redundant GitHub mirrors are configured."""
    assert len(ONLINE_PAYLOAD_URLS) >= 3
    assert any("github.com/imyouiamyou/prubeth-ide" in url for url in ONLINE_PAYLOAD_URLS)
    assert any(f"releases/download/v{APP_VERSION}" in url or "releases/download/v1.12" in url for url in ONLINE_PAYLOAD_URLS)
    assert any("releases/latest/download" in url for url in ONLINE_PAYLOAD_URLS)


def test_installer_downloads_from_github_when_no_local_payload(tmp_path):
    """Simulate clean machine without local source repo: downloads payload from GitHub."""
    target_install = tmp_path / "installed_app"

    # Create a mock valid payload zip containing local_ai_studio_pro.py and assets
    mock_payload_buffer = io.BytesIO()
    with zipfile.ZipFile(mock_payload_buffer, 'w', compression=zipfile.ZIP_STORED) as z:
        z.writestr("local_ai_studio_pro.py", "# Mock Prubeth IDE Entrypoint\nAPP_VERSION='3.0.0'\n")
        z.writestr("README.md", "# Prubeth IDE\n")
        z.writestr("assets/icon.ico", b"MOCK_ICON_BYTES" * 100)
        z.writestr("padding.dat", b"X" * 2000)

    mock_bytes = mock_payload_buffer.getvalue()

    # Create worker with no payload zip and a target dir
    worker = InstallWorker(
        target_dir=str(target_install),
        create_desktop=False,
        create_startmenu=False,
        payload_zip=None,
        mode="online"
    )

    # Mock urllib.request.urlopen returning the mock zip payload
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {"content-length": str(len(mock_bytes))}
    mock_response.read.side_effect = [mock_bytes[:30000], mock_bytes[30000:], b""]
    mock_response.__enter__.return_value = mock_response

    progress_events = []
    worker.progress.connect(lambda pct, msg: progress_events.append((pct, msg)))

    with patch("urllib.request.urlopen", return_value=mock_response), \
         patch("setup_wizard.get_source_dir", return_value=tmp_path / "nonexistent_source"), \
         patch("setup_wizard.get_resource_dir", return_value=tmp_path / "nonexistent_res"):
        worker.run()

    # Verify installation succeeded
    assert (target_install / "local_ai_studio_pro.py").exists()
    assert (target_install / "PrubethIDE.bat").exists()
    assert any("Downloading from GitHub" in msg for _, msg in progress_events)
