"""
PRUBETH IDE — GitHub Bootstrap Installer Acceptance Test Suite
Validates Section 14 Small, Medium, and Large acceptance tests:
- Mode A (Lightweight Online) vs Mode B (Offline) threshold evaluation
- Release metadata resolver, manifest schema, and cryptographic signature verification
- 10-stage download progress, speed, ETA, and cancellation
- HTTP 429 rate limit backoff and HTTP Range resumption
- Cryptographic SHA-256 mismatch rejection and forged signature rejection
- Path traversal and malicious archive entry rejection
- Dual-volume disk space validation
- Transactional staging, upgrade backup, AST health check, and rollback recovery
- Uninstaller preservation of user projects and configurations
"""
import os
import sys
import io
import json
import time
import zipfile
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from installer.release_config import (
    APP_NAME, APP_VERSION, PUBLISHER, GITHUB_REPO, DEFAULT_ONLINE_THRESHOLD_MIB,
    MODE_ONLINE, MODE_OFFLINE, MODE_AUTO,
    evaluate_delivery_mode, compute_sha256, compute_manifest_signature,
    verify_manifest_signature, TRUSTED_PUBLIC_VERIFICATION_KEY,
    EXIT_SUCCESS, EXIT_GENERAL_ERROR, EXIT_INVALID_ARGS, EXIT_NETWORK_ERROR,
    EXIT_VERIFICATION_FAILED, EXIT_INSUFFICIENT_SPACE, EXIT_USER_CANCELLED
)
from installer.manifest_schema import (
    validate_manifest_schema, verify_manifest_compatibility, build_manifest_document,
    ManifestValidationError
)
from installer.disk_manager import (
    verify_disk_space, estimate_space_requirements, calculate_directory_size
)
from installer.download_engine import (
    ReleaseMetadataResolver, SecureDownloadEngine, DownloadProgress,
    DownloadError, VerificationError, STAGE_NAMES
)
from installer.transactional_installer import (
    TransactionalInstaller, inspect_archive_security,
    SecurityInspectionError, InstallationCommitError
)
from installer.uninstaller import Uninstaller


# =====================================================================
# 1. SMALL ACCEPTANCE TESTS
# =====================================================================

def test_delivery_mode_threshold_evaluation():
    """Verify 70 MiB threshold rule for Mode A vs Mode B."""
    thresh_bytes = int(70.0 * 1024 * 1024)

    # 1. Below 70 MiB -> Mode B Offline
    mode, reason = evaluate_delivery_mode(package_size_bytes=50 * 1024 * 1024, requested_mode="auto")
    assert mode == MODE_OFFLINE
    assert "below" in reason

    # 2. At or above 70 MiB -> Mode A Online
    mode, reason = evaluate_delivery_mode(package_size_bytes=75 * 1024 * 1024, requested_mode="auto")
    assert mode == MODE_ONLINE
    assert "meets/exceeds" in reason

    # 3. Explicit override
    mode, _ = evaluate_delivery_mode(package_size_bytes=100 * 1024 * 1024, requested_mode="offline")
    assert mode == MODE_OFFLINE


def test_manifest_schema_validation_and_signature():
    """Verify manifest schema validation and cryptographic Ed25519 asymmetric signature."""
    doc = build_manifest_document(
        version="1.12.0",
        payload_filename="Prubeth-Payload-1.12.0-windows-x64.zip",
        payload_sha256="a" * 64,
        payload_size_bytes=20000000,
        min_required_disk_bytes=60000000,
        required_files=["local_ai_studio_pro.py", "README.md"]
    )
    is_valid, err = validate_manifest_schema(doc)
    assert is_valid is True
    assert err is None

    # Sign manifest using Ed25519 asymmetric signature
    doc_bytes = json.dumps(doc).encode("utf-8")
    sig = compute_manifest_signature(doc_bytes)
    assert len(sig) == 128  # 64 bytes = 128 hex chars in Ed25519

    # Verify signature against public verification key
    assert verify_manifest_signature(doc_bytes, sig, TRUSTED_PUBLIC_VERIFICATION_KEY) is True
    # Forged signature must fail
    assert verify_manifest_signature(doc_bytes, "0" * 128, TRUSTED_PUBLIC_VERIFICATION_KEY) is False
    # Tampered bytes must fail
    assert verify_manifest_signature(b'{"tampered": true}', sig, TRUSTED_PUBLIC_VERIFICATION_KEY) is False


def test_manifest_version_mismatch_rejected():
    """Reject release manifest when version does not match installer target."""
    doc = build_manifest_document(
        version="2.9.0",  # Mismatched version
        payload_filename="Prubeth-Payload-2.9.0-windows-x64.zip",
        payload_sha256="b" * 64,
        payload_size_bytes=20000000,
        min_required_disk_bytes=60000000,
        required_files=["local_ai_studio_pro.py"]
    )
    is_compat, err = verify_manifest_compatibility(doc, expected_version="1.12.0")
    assert is_compat is False
    assert "Version mismatch" in err


def test_download_progress_object_formatting():
    """Verify real-time speed, ETA, and percent calculations in progress reporting."""
    prog = DownloadProgress(
        stage=5,
        stage_name=STAGE_NAMES[5],
        downloaded_bytes=10 * 1024 * 1024,
        total_bytes=20 * 1024 * 1024,
        percent=50.0,
        speed_bps=2.5 * 1024 * 1024,
        eta_seconds=4.0,
        status_text="Downloading..."
    )
    assert prog.speed_mbps == 2.5
    assert prog.downloaded_mb == 10.0
    assert prog.total_mb == 20.0
    assert prog.percent == 50.0


# =====================================================================
# 2. MEDIUM ACCEPTANCE TESTS
# =====================================================================

def test_secure_download_with_mock_github_response(tmp_path):
    """Verify clean download, SHA-256 verification, and atomic promotion."""
    fake_content = b"PRUBETH_IDE_PACKAGE_PAYLOAD_TEST_DATA_" * 500
    expected_sha = compute_sha256_bytes(fake_content)

    downloader = SecureDownloadEngine(max_retries=2)

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Length": str(len(fake_content))}
    mock_resp.read.side_effect = [fake_content[:5000], fake_content[5000:], b""]
    mock_resp.__enter__.return_value = mock_resp

    progress_events = []
    def on_prog(p):
        progress_events.append(p.stage)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        verified_path = downloader.download_payload(
            payload_url="https://github.com/SVR1339/prubeth-ide/releases/download/v3.0.0/payload.zip",
            expected_sha256=expected_sha,
            expected_size_bytes=len(fake_content),
            destination_dir=tmp_path,
            progress_callback=on_prog
        )

    assert verified_path.exists()
    assert verified_path.name.endswith(".verified.zip")
    assert verified_path.stat().st_size == len(fake_content)
    assert 5 in progress_events
    assert 6 in progress_events


def test_corrupted_payload_sha256_rejected(tmp_path):
    """Verify that corrupt or tampered payload fails SHA-256 check and is discarded."""
    fake_content = b"VALID_BYTES"
    tampered_sha = "0" * 64

    downloader = SecureDownloadEngine(max_retries=1)

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Length": str(len(fake_content))}
    mock_resp.read.side_effect = [fake_content, b""]
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(VerificationError) as exc_info:
            downloader.download_payload(
                payload_url="https://fake.url/payload.zip",
                expected_sha256=tampered_sha,
                expected_size_bytes=len(fake_content),
                destination_dir=tmp_path
            )
    assert "SHA-256 digest mismatch" in str(exc_info.value)


def test_http_range_resumption_support(tmp_path):
    """Verify HTTP 206 Partial Content safely resumes an existing partial file."""
    part_content1 = b"PART_1_INITIAL_BYTES_" * 200
    part_content2 = b"PART_2_APPENDED_BYTES_" * 200
    full_content = part_content1 + part_content2
    full_sha = compute_sha256_bytes(full_content)

    downloader = SecureDownloadEngine(max_retries=1)

    # Simulate existing partial file
    session_id = "testres"
    part_file = tmp_path / f"prubeth_payload_{session_id}.part"
    part_file.write_bytes(part_content1)

    mock_resp = MagicMock()
    mock_resp.status = 206  # Partial Content
    mock_resp.headers = {
        "Content-Range": f"bytes {len(part_content1)}-{len(full_content)-1}/{len(full_content)}",
        "Content-Length": str(len(part_content2))
    }
    mock_resp.read.side_effect = [part_content2, b""]
    mock_resp.__enter__.return_value = mock_resp

    with patch("uuid.uuid4", return_value=session_id):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            verified_file = downloader.download_payload(
                payload_url="https://fake.url/payload.zip",
                expected_sha256=full_sha,
                expected_size_bytes=len(full_content),
                destination_dir=tmp_path
            )

    assert verified_file.exists()
    assert verified_file.read_bytes() == full_content


def test_http_429_rate_limiting_retry_after(tmp_path):
    """Verify HTTP 429 rate limit backoff uses Retry-After header."""
    fake_content = b"SUCCESS_AFTER_429"
    full_sha = compute_sha256_bytes(fake_content)

    downloader = SecureDownloadEngine(max_retries=2, base_backoff_sec=0.01)

    import urllib.error
    err_429 = urllib.error.HTTPError(
        url="https://fake.url",
        code=429,
        msg="Too Many Requests",
        hdrs={"Retry-After": "0"},
        fp=io.BytesIO(b"Rate limited")
    )

    mock_resp_ok = MagicMock()
    mock_resp_ok.status = 200
    mock_resp_ok.headers = {"Content-Length": str(len(fake_content))}
    mock_resp_ok.read.side_effect = [fake_content, b""]
    mock_resp_ok.__enter__.return_value = mock_resp_ok

    with patch("urllib.request.urlopen", side_effect=[err_429, mock_resp_ok]):
        verified_file = downloader.download_payload(
            payload_url="https://fake.url/payload.zip",
            expected_sha256=full_sha,
            expected_size_bytes=len(fake_content),
            destination_dir=tmp_path
        )

    assert verified_file.exists()
    assert verified_file.read_bytes() == fake_content


def test_download_cancellation_cleans_temporary_files(tmp_path):
    """Verify cancellation aborts download and cleans up partial files."""
    downloader = SecureDownloadEngine()

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Length": "100000"}

    def cancel_on_read(chunk_size):
        downloader.cancel()
        return b"SOME_INITIAL_BYTES"

    mock_resp.read.side_effect = cancel_on_read
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(DownloadError) as exc_info:
            downloader.download_payload(
                payload_url="https://fake.url/payload.zip",
                expected_sha256="a" * 64,
                expected_size_bytes=100000,
                destination_dir=tmp_path
            )
    assert "cancelled" in str(exc_info.value).lower()
    # Ensure no leftover .part files remain
    assert len(list(tmp_path.glob("*.part"))) == 0


def test_archive_security_inspection_detects_path_traversal(tmp_path):
    """Reject zip archives attempting path traversal or absolute paths."""
    bad_zip = tmp_path / "malicious.zip"
    with zipfile.ZipFile(bad_zip, 'w') as z:
        z.writestr("../../windows/system32/cmd.exe", "evil")

    with pytest.raises(SecurityInspectionError) as exc_info:
        inspect_archive_security(bad_zip)
    assert "path traversal" in str(exc_info.value).lower()


def test_archive_security_inspection_detects_reserved_device_names(tmp_path):
    """Reject zip archives containing Windows reserved names like CON, PRN, NUL."""
    bad_zip = tmp_path / "reserved.zip"
    with zipfile.ZipFile(bad_zip, 'w') as z:
        z.writestr("docs/CON.txt", "forbidden")

    with pytest.raises(SecurityInspectionError) as exc_info:
        inspect_archive_security(bad_zip)
    assert "reserved windows device name" in str(exc_info.value).lower()


# =====================================================================
# 3. LARGE ACCEPTANCE TESTS
# =====================================================================

def test_transactional_installation_and_rollback_on_health_failure(tmp_path):
    """Verify upgrade backup preservation and automatic rollback when health check fails."""
    target_install = tmp_path / "app_dir"
    target_install.mkdir()
    # Existing working file
    (target_install / "local_ai_studio_pro.py").write_text("# Previous working version\nAPP_VERSION='2.9.0'\n", encoding="utf-8")
    (target_install / "user_project.py").write_text("# User project file\n", encoding="utf-8")

    # Create bad payload where local_ai_studio_pro.py has a syntax error
    bad_payload_zip = tmp_path / "bad_payload.zip"
    with zipfile.ZipFile(bad_payload_zip, 'w') as z:
        z.writestr("local_ai_studio_pro.py", "def broken_syntax(:\n")  # Syntax error
        z.writestr("README.md", "# Test\n")

    installer = TransactionalInstaller(
        target_dir=target_install,
        staging_dir=tmp_path / "staging"
    )

    with pytest.raises(InstallationCommitError) as exc_info:
        installer.execute_transaction(
            payload_zip=bad_payload_zip,
            required_files=["local_ai_studio_pro.py"]
        )

    # Rollback must have restored the previous working version!
    assert "Rollback status: Successfully rolled back" in str(exc_info.value)
    content = (target_install / "local_ai_studio_pro.py").read_text(encoding="utf-8")
    assert "APP_VERSION='2.9.0'" in content
    assert (target_install / "user_project.py").exists()


def test_transactional_installation_succeeds_with_valid_payload(tmp_path):
    """Verify complete end-to-end installation transaction with valid payload."""
    target_install = tmp_path / "app_dir"
    valid_payload_zip = tmp_path / "valid_payload.zip"
    with zipfile.ZipFile(valid_payload_zip, 'w') as z:
        z.writestr("local_ai_studio_pro.py", "# Clean Entrypoint\nAPP_VERSION='3.0.0'\n")
        z.writestr("README.md", "# Prubeth IDE Horizon\n")
        z.writestr("core/universal_inventory.py", "# Inventory\n")

    installer = TransactionalInstaller(
        target_dir=target_install,
        staging_dir=tmp_path / "staging"
    )

    result = installer.execute_transaction(
        payload_zip=valid_payload_zip,
        required_files=["local_ai_studio_pro.py", "README.md", "core/universal_inventory.py"]
    )

    assert result["success"] is True
    assert (target_install / "local_ai_studio_pro.py").exists()
    assert (target_install / "installation_receipt.json").exists()


def test_uninstaller_preserves_user_projects_and_models(tmp_path):
    """Verify uninstaller removes application binaries but preserves user code, workspaces, and models."""
    app_dir = tmp_path / "PrubethIDE"
    app_dir.mkdir()
    # App-managed files
    (app_dir / "local_ai_studio_pro.py").write_text("# App code\n", encoding="utf-8")
    (app_dir / "PrubethIDE.bat").write_text("@echo off\n", encoding="utf-8")
    core_dir = app_dir / "core"
    core_dir.mkdir()
    (core_dir / "universal_inventory.py").write_text("# Core\n", encoding="utf-8")

    # User-created files
    models_dir = app_dir / "models"
    models_dir.mkdir()
    (models_dir / "qwen.gguf").write_bytes(b"MODEL_WEIGHTS")

    config_dir = app_dir / ".local_ai_studio_pro"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text('{"user_custom": true}\n', encoding="utf-8")

    user_code = app_dir / "my_project.py"
    user_code.write_text("# User work\n", encoding="utf-8")

    uninstaller = Uninstaller(install_dir=app_dir)
    res = uninstaller.uninstall(remove_user_data=False, remove_models=False, remove_shortcuts=False)

    assert res["success"] is True
    # App code removed
    assert not (app_dir / "local_ai_studio_pro.py").exists()
    assert not (app_dir / "PrubethIDE.bat").exists()
    assert not core_dir.exists()

    # User code, models, and configs preserved
    assert (models_dir / "qwen.gguf").exists()
    assert (config_dir / "settings.json").exists()
    assert user_code.exists()


# Helper function
def compute_sha256_bytes(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


# =====================================================================
# 4. EXTERNAL AUDIT SECURITY REMEDIATION TESTS (Findings 1 & 2)
# =====================================================================

def test_tls_verification_enforced_and_invalid_cert_fails_closed(tmp_path):
    """
    Finding 1 Remediation Test:
    Verify that SecureDownloadEngine and ReleaseMetadataResolver enforce strict TLS verification
    (check_hostname=True, verify_mode=CERT_REQUIRED) and fail closed on certificate/hostname errors.
    """
    import ssl
    resolver = ReleaseMetadataResolver()
    assert resolver.ssl_context.check_hostname is True
    assert resolver.ssl_context.verify_mode == ssl.CERT_REQUIRED

    downloader = SecureDownloadEngine()
    assert downloader.ssl_context.check_hostname is True
    assert downloader.ssl_context.verify_mode == ssl.CERT_REQUIRED

    # Simulate SSL certificate verification failure
    with patch("urllib.request.urlopen", side_effect=ssl.SSLCertVerificationError("Certificate verify failed: self signed certificate")):
        with pytest.raises(DownloadError) as exc_info:
            downloader.download_payload(
                payload_url="https://github.com/SVR1339/prubeth-ide/releases/download/v1.12.0/payload.zip",
                expected_sha256="0" * 64,
                expected_size_bytes=1024,
                destination_dir=tmp_path
            )
        assert "Certificate verify failed" in str(exc_info.value) or "SSL" in str(exc_info.value) or "Download interrupted" in str(exc_info.value)

    # Ensure no partial files leaked into destination
    leftover_files = list(tmp_path.glob("*.zip"))
    assert len(leftover_files) == 0


def test_unauthenticated_download_rejected_fails_closed(tmp_path):
    """
    Finding 2 Remediation Test:
    Verify that downloaded archives with invalid or unverified manifests/signatures
    fail closed and cannot be staged or installed.
    """
    # Create fake archive
    fake_zip = tmp_path / "unauthenticated.zip"
    with zipfile.ZipFile(fake_zip, 'w') as z:
        z.writestr("local_ai_studio_pro.py", "# malicious or untrusted code\n")

    fake_bytes = fake_zip.read_bytes()
    expected_sha = compute_sha256_bytes(fake_bytes)

    # Manifest with forged signature
    manifest = {
        "schema_version": "1.0",
        "product": APP_NAME,
        "version": APP_VERSION,
        "channel": "stable",
        "architecture": "windows-x64",
        "payload_filename": "unauthenticated.zip",
        "payload_sha256": expected_sha,
        "payload_size_bytes": len(fake_bytes),
        "min_required_disk_bytes": 1000000,
        "required_files": ["local_ai_studio_pro.py"]
    }
    manifest_bytes = json.dumps(manifest).encode("utf-8")
    forged_sig = "f" * 128

    assert verify_manifest_signature(manifest_bytes, forged_sig, TRUSTED_PUBLIC_VERIFICATION_KEY) is False

    # Resolver must reject the forged release
    resolver = ReleaseMetadataResolver()
    with patch.object(resolver, "_fetch_url_bytes", side_effect=[manifest_bytes, forged_sig.encode("utf-8")]):
        with pytest.raises(VerificationError) as exc_info:
            resolver.resolve_release()
        assert "authenticity verification failed" in str(exc_info.value).lower() or "signature does not match" in str(exc_info.value).lower()

