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


import json
import hashlib
from release_config import compute_manifest_signature
from manifest_schema import build_manifest_document


def test_online_payload_urls_configured():
    """Verify that multiple redundant GitHub mirrors are configured."""
    assert len(ONLINE_PAYLOAD_URLS) >= 3
    assert any("github.com/imyouiamyou/prubeth-ide" in url for url in ONLINE_PAYLOAD_URLS)
    assert any(f"releases/download/v{APP_VERSION}" in url or "releases/download/v1.12" in url for url in ONLINE_PAYLOAD_URLS)
    assert any("releases/latest/download" in url for url in ONLINE_PAYLOAD_URLS)


def test_installer_downloads_from_github_when_no_local_payload(tmp_path):
    """Simulate clean machine without local source repo: downloads authenticated payload from GitHub."""
    target_install = tmp_path / "installed_app"

    # Create a mock valid payload zip containing local_ai_studio_pro.py and assets
    mock_payload_buffer = io.BytesIO()
    with zipfile.ZipFile(mock_payload_buffer, 'w', compression=zipfile.ZIP_STORED) as z:
        z.writestr("local_ai_studio_pro.py", "# Mock Prubeth IDE Entrypoint\nAPP_VERSION='1.12.0'\n")
        z.writestr("README.md", "# Prubeth IDE\n")
        z.writestr("assets/icon.ico", b"MOCK_ICON_BYTES" * 100)
        z.writestr("padding.dat", b"X" * 2000)

    mock_bytes = mock_payload_buffer.getvalue()
    payload_sha = hashlib.sha256(mock_bytes).hexdigest()

    # Generate valid release manifest and Ed25519 asymmetric signature
    manifest_doc = build_manifest_document(
        version=APP_VERSION,
        payload_filename=f"Prubeth-Payload-{APP_VERSION}-windows-x64.zip",
        payload_sha256=payload_sha,
        payload_size_bytes=len(mock_bytes),
        min_required_disk_bytes=100000,
        required_files=["local_ai_studio_pro.py"]
    )
    manifest_bytes = json.dumps(manifest_doc).encode("utf-8")
    sig_hex = compute_manifest_signature(manifest_bytes)
    sig_bytes = (sig_hex + "\n").encode("utf-8")

    # Create worker with no payload zip and a target dir
    worker = InstallWorker(
        target_dir=str(target_install),
        create_desktop=False,
        create_startmenu=False,
        payload_zip=None,
        mode="online"
    )

    def mock_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        resp = MagicMock()
        resp.status = 200
        if "Manifest" in url and url.endswith(".json"):
            resp.headers = {"content-length": str(len(manifest_bytes))}
            resp.read.side_effect = [manifest_bytes, b""]
        elif "Manifest" in url and url.endswith(".sig"):
            resp.headers = {"content-length": str(len(sig_bytes))}
            resp.read.side_effect = [sig_bytes, b""]
        else:
            resp.headers = {"content-length": str(len(mock_bytes))}
            resp.read.side_effect = [mock_bytes[:30000], mock_bytes[30000:], b""]
        resp.__enter__.return_value = resp
        return resp

    progress_events = []
    worker.progress.connect(lambda pct, msg: progress_events.append((pct, msg)))

    with patch("urllib.request.urlopen", side_effect=mock_urlopen), \
         patch("setup_wizard.get_source_dir", return_value=tmp_path / "nonexistent_source"), \
         patch("setup_wizard.get_resource_dir", return_value=tmp_path / "nonexistent_res"):
        worker.run()

    # Verify installation succeeded
    assert (target_install / "local_ai_studio_pro.py").exists()
    assert (target_install / "PrubethIDE.bat").exists()
    assert any("integrity verified" in msg.lower() or "download" in msg.lower() for _, msg in progress_events)
