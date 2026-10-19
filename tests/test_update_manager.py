"""
PRUBETH IDE — Software Update Manager Verification Test Suite
==============================================================
Validates semver comparison, update manifest integrity, non-invasive
staging, SHA-256 cryptographic checking, and user consent dialogs.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Ensure offscreen Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication

from core.update_manager import (
    UpdateManager,
    UpdateDialog,
    ReleaseManifest,
    compare_semver,
    UpdateCheckWorker,
    UpdateDownloadWorker,
)


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_compare_semver():
    # 1. Update available
    assert compare_semver("1.89.0", "1.90.0") == 1
    assert compare_semver("1.89.0", "2.0.0") == 1
    assert compare_semver("1.89.0", "1.89.1") == 1
    assert compare_semver("v1.89.0", "1.90.0") == 1
    assert compare_semver("1.89.0 (Horizon Edition)", "1.90.0") == 1

    # 2. Up to date
    assert compare_semver("1.90.0", "1.90.0") == 0
    assert compare_semver("1.89.0", "1.89.0") == 0

    # 3. Development ahead of release
    assert compare_semver("2.0.0", "1.90.0") == -1
    assert compare_semver("1.91.0", "1.90.0") == -1


def test_release_manifest_file_validity():
    manifest_path = Path(__file__).resolve().parent.parent / "releases" / "latest_manifest.json"
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] in ["1.90.0", "1.91.0"]
    assert "PRUBETH" in data["display_name"]
    assert "HIRE ROBOTS" in data["tagline"]
    assert len(data["sha256"]) == 64
    assert data["size_bytes"] > 1000000
    assert len(data["changelog"]) >= 3


def test_update_check_worker_local_fallback(qapp):
    results = []

    def on_finished(avail, manifest_dict, msg):
        results.append((avail, manifest_dict, msg))

    # Point to invalid remote to force local fallback verification
    worker = UpdateCheckWorker(
        current_version="1.89.0",
        manifest_url="http://invalid-unreachable-domain-xyz.local/manifest.json",
    )
    worker.check_finished.connect(on_finished)
    worker.run()

    assert len(results) == 1
    avail, manifest_dict, msg = results[0]
    assert avail is True
    assert manifest_dict.get("version") in ["1.90.0", "1.91.0"]
    assert "is available" in msg


def test_update_download_worker_with_local_payload(qapp, tmp_path):
    # Verify non-invasive staging using the verified local payload
    manifest_path = Path(__file__).resolve().parent.parent / "releases" / "latest_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest = ReleaseManifest(
        version=data["version"],
        display_name=data["display_name"],
        tagline=data["tagline"],
        release_date=data["release_date"],
        channel=data["channel"],
        min_supported_version=data["min_supported_version"],
        download_url="http://invalid-domain.local/payload.zip",
        sha256=data["sha256"],
        size_bytes=data["size_bytes"],
        fallback_local_payload=data.get("fallback_local_payload"),
    )

    staging = tmp_path / "staging"
    worker = UpdateDownloadWorker(manifest, staging)

    progress_events = []
    finished_events = []
    worker.progress.connect(lambda p, d, t: progress_events.append((p, d, t)))
    worker.download_finished.connect(lambda ok, path, err: finished_events.append((ok, path, err)))

    worker.run()

    assert len(finished_events) == 1
    success, payload_path, msg = finished_events[0]
    assert success is True
    assert Path(payload_path).exists()
    assert len(progress_events) >= 1
    assert progress_events[-1][0] == 100


def test_update_dialog_instantiation_headless(qapp):
    manifest_path = Path(__file__).resolve().parent.parent / "releases" / "latest_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest = ReleaseManifest(
        version=data["version"],
        display_name=data["display_name"],
        tagline=data["tagline"],
        release_date=data["release_date"],
        channel=data["channel"],
        min_supported_version=data["min_supported_version"],
        download_url="https://example.com/payload.zip",
        sha256=data["sha256"],
        size_bytes=data["size_bytes"],
        changelog=data.get("changelog", []),
    )

    dialog = UpdateDialog(manifest, current_version="1.89.0")
    assert dialog.windowTitle() == "PRUBETH IDE — Software Update"
    assert dialog.manifest.version in ["1.90.0", "1.91.0"]
    assert dialog.action_btn.text() == "🚀 Update & Restart"
    assert dialog.later_btn.text() == "Remind Me Later"
    dialog.reject()
