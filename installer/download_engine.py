"""
PRUBETH IDE — Secure GitHub Download & Release Metadata Resolver Engine
Retrieves official releases from GitHub, validates manifest signatures, implements 10-stage
progress reporting, bounded exponential retries, HTTP Range resumption, rate-limit backoff,
atomic temporary file promotion, and cancellation support.
"""
import os
import sys
import ssl
import time
import json
import uuid
import random
import hashlib
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Callable, List

_INSTALLER_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _INSTALLER_DIR.parent
for _p in [str(_REPO_ROOT), str(_INSTALLER_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from installer.release_config import (
        APP_NAME, APP_VERSION, GITHUB_REPO, GITHUB_REPO_URL,
        DEFAULT_CHANNEL, TARGET_ARCH, TRUSTED_PUBLIC_VERIFICATION_KEY,
        verify_manifest_signature, compute_sha256
    )
    from installer.manifest_schema import (
        validate_manifest_schema, verify_manifest_compatibility, ManifestValidationError
    )
except ImportError:
    from release_config import (
        APP_NAME, APP_VERSION, GITHUB_REPO, GITHUB_REPO_URL,
        DEFAULT_CHANNEL, TARGET_ARCH, TRUSTED_PUBLIC_VERIFICATION_KEY,
        verify_manifest_signature, compute_sha256
    )
    from manifest_schema import (
        validate_manifest_schema, verify_manifest_compatibility, ManifestValidationError
    )

# 10 Standard Lifecycle Installation Stages
STAGE_NAMES = {
    1: "Checking system compatibility",
    2: "Connecting to official release",
    3: "Verifying release metadata",
    4: "Preparing download",
    5: "Downloading application files",
    6: "Verifying downloaded files",
    7: "Preparing installation",
    8: "Installing application",
    9: "Verifying installed application",
    10: "Completing setup"
}


class DownloadProgress:
    def __init__(
        self,
        stage: int,
        stage_name: str,
        downloaded_bytes: int = 0,
        total_bytes: Optional[int] = None,
        percent: Optional[float] = None,
        speed_bps: float = 0.0,
        eta_seconds: Optional[float] = None,
        status_text: str = ""
    ):
        self.stage = stage
        self.stage_name = stage_name
        self.downloaded_bytes = downloaded_bytes
        self.total_bytes = total_bytes
        self.percent = percent
        self.speed_bps = speed_bps
        self.eta_seconds = eta_seconds
        self.status_text = status_text

    @property
    def speed_mbps(self) -> float:
        return self.speed_bps / (1024 * 1024)

    @property
    def downloaded_mb(self) -> float:
        return self.downloaded_bytes / (1024 * 1024)

    @property
    def total_mb(self) -> Optional[float]:
        return (self.total_bytes / (1024 * 1024)) if self.total_bytes else None


class DownloadError(Exception):
    """General download failure exception."""
    pass


class VerificationError(Exception):
    """Cryptographic or hash mismatch failure."""
    pass


class ReleaseMetadataResolver:
    """
    Resolves official GitHub release metadata, parses and verifies release manifest
    and authenticates publication signature using embedded verification key.
    """
    def __init__(
        self,
        repo: str = GITHUB_REPO,
        version: str = APP_VERSION,
        channel: str = DEFAULT_CHANNEL,
        arch: str = TARGET_ARCH,
        timeout: int = 15
    ):
        self.repo = repo
        self.version = version
        self.channel = channel
        self.arch = arch
        self.timeout = timeout
        self.ssl_context = ssl.create_default_context()
        self.headers = {
            "User-Agent": f"PrubethIDE-Installer/{APP_VERSION} (Windows NT 10.0; Win64; x64)",
            "Accept": "application/vnd.github.v3+json, application/json, text/plain, */*"
        }

    def _fetch_url_bytes(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as resp:
            if resp.status != 200:
                raise DownloadError(f"HTTP error {resp.status} fetching '{url}'")
            return resp.read()

    def resolve_release(self, progress_callback: Optional[Callable[[DownloadProgress], None]] = None) -> Dict[str, Any]:
        """
        Resolves the exact release assets, manifest, and signature.
        Returns a validated release transaction plan.
        """
        if progress_callback:
            progress_callback(DownloadProgress(
                stage=2,
                stage_name=STAGE_NAMES[2],
                status_text=f"Connecting to official release v{self.version} on GitHub ({self.repo})..."
            ))

        tag = f"v{self.version}"
        base_release_url = f"https://github.com/{self.repo}/releases/download/{tag}"
        manifest_filename = f"Prubeth-Manifest-{self.version}.json"
        sig_filename = f"Prubeth-Manifest-{self.version}.sig"
        payload_filename = f"Prubeth-Payload-{self.version}-{self.arch}.zip"

        manifest_url = f"{base_release_url}/{manifest_filename}"
        sig_url = f"{base_release_url}/{sig_filename}"
        payload_url = f"{base_release_url}/{payload_filename}"

        if progress_callback:
            progress_callback(DownloadProgress(
                stage=3,
                stage_name=STAGE_NAMES[3],
                status_text="Retrieving and cryptographically verifying release manifest..."
            ))

        # Retrieve Manifest
        try:
            manifest_bytes = self._fetch_url_bytes(manifest_url)
            manifest_data = json.loads(manifest_bytes.decode("utf-8"))
        except Exception as e:
            # Fallback check on latest release or tag asset directory
            raise DownloadError(f"Unable to retrieve official release manifest from '{manifest_url}': {e}")

        # Retrieve Signature
        try:
            sig_bytes = self._fetch_url_bytes(sig_url)
            sig_hex = sig_bytes.decode("utf-8").strip()
        except Exception as e:
            raise DownloadError(f"Unable to retrieve manifest signature from '{sig_url}': {e}")

        # Verify Signature
        if not verify_manifest_signature(manifest_bytes, sig_hex, TRUSTED_PUBLIC_VERIFICATION_KEY):
            raise VerificationError(
                "Release manifest authenticity verification failed! "
                "The signature does not match the trusted publisher signing authority."
            )

        # Validate Schema and Compatibility
        is_compat, err_msg = verify_manifest_compatibility(
            manifest_data,
            expected_version=self.version,
            expected_channel=self.channel,
            expected_arch=self.arch
        )
        if not is_compat:
            raise ManifestValidationError(f"Incompatible release manifest: {err_msg}")

        return {
            "version": manifest_data["version"],
            "channel": manifest_data["channel"],
            "architecture": manifest_data["architecture"],
            "manifest_data": manifest_data,
            "manifest_bytes": manifest_bytes,
            "signature": sig_hex,
            "payload_url": payload_url,
            "payload_filename": manifest_data["payload_filename"],
            "payload_sha256": manifest_data["payload_sha256"],
            "payload_size_bytes": manifest_data["payload_size_bytes"],
            "min_required_disk_bytes": manifest_data["min_required_disk_bytes"],
            "required_files": manifest_data["required_files"]
        }


class SecureDownloadEngine:
    """
    Downloads application payload from official release with bounded exponential retries,
    HTTP 429 rate-limiting backoff, HTTP Range resume support, atomic staging,
    and streaming SHA-256 digest validation.
    """
    def __init__(
        self,
        max_retries: int = 4,
        base_backoff_sec: float = 1.0,
        connect_timeout: int = 15,
        read_timeout: int = 30
    ):
        self.max_retries = max_retries
        self.base_backoff_sec = base_backoff_sec
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.ssl_context = ssl.create_default_context()
        self.is_cancelled = False

    def cancel(self):
        """Signals active download to abort cleanly."""
        self.is_cancelled = True

    def download_payload(
        self,
        payload_url: str,
        expected_sha256: str,
        expected_size_bytes: int,
        destination_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> Path:
        """
        Downloads the payload file safely into destination_dir (or tempdir).
        Returns Path to verified payload zip archive.
        """
        if destination_dir is None:
            destination_dir = Path(tempfile.gettempdir())
        destination_dir.mkdir(parents=True, exist_ok=True)

        session_id = str(uuid.uuid4())[:8]
        part_file = destination_dir / f"prubeth_payload_{session_id}.part"
        verified_file = destination_dir / f"prubeth_payload_{session_id}.verified.zip"

        headers = {
            "User-Agent": f"PrubethIDE-Installer/{APP_VERSION} (Windows NT 10.0; Win64; x64)",
            "Accept": "application/octet-stream, application/zip, */*"
        }

        downloaded_bytes = 0
        if part_file.exists():
            downloaded_bytes = part_file.stat().st_size

        if progress_callback:
            progress_callback(DownloadProgress(
                stage=4,
                stage_name=STAGE_NAMES[4],
                status_text="Preparing download pipeline and verifying destination..."
            ))

        attempt = 0
        start_time = time.time()
        last_calc_time = start_time
        bytes_since_last_calc = 0
        current_speed = 0.0

        while attempt < self.max_retries and not self.is_cancelled:
            attempt += 1
            req_headers = dict(headers)
            can_resume = downloaded_bytes > 0 and downloaded_bytes < expected_size_bytes

            if can_resume:
                req_headers["Range"] = f"bytes={downloaded_bytes}-"

            req = urllib.request.Request(payload_url, headers=req_headers)

            try:
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.connect_timeout) as resp:
                    status = resp.status
                    content_range = resp.headers.get("Content-Range")
                    content_length = resp.headers.get("Content-Length")

                    # Handle Range vs Full content
                    if status == 206 and can_resume:
                        mode = "ab"
                    else:
                        # Server does not support resume or restarted
                        mode = "wb"
                        downloaded_bytes = 0

                    total_expected = expected_size_bytes
                    if content_length and not can_resume:
                        try:
                            total_expected = int(content_length)
                        except ValueError:
                            pass

                    with open(part_file, mode) as f_out:
                        chunk_size = 65536
                        while not self.is_cancelled:
                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            f_out.write(chunk)
                            downloaded_bytes += len(chunk)
                            bytes_since_last_calc += len(chunk)

                            now = time.time()
                            if now - last_calc_time >= 0.25:
                                elapsed = now - last_calc_time
                                current_speed = bytes_since_last_calc / elapsed
                                bytes_since_last_calc = 0
                                last_calc_time = now

                                remaining_bytes = max(0, total_expected - downloaded_bytes)
                                eta = (remaining_bytes / current_speed) if current_speed > 0 else None
                                pct = (downloaded_bytes / total_expected * 100.0) if total_expected > 0 else 0.0

                                if progress_callback:
                                    progress_callback(DownloadProgress(
                                        stage=5,
                                        stage_name=STAGE_NAMES[5],
                                        downloaded_bytes=downloaded_bytes,
                                        total_bytes=total_expected,
                                        percent=min(pct, 100.0),
                                        speed_bps=current_speed,
                                        eta_seconds=eta,
                                        status_text=f"Downloading: {downloaded_bytes / (1024*1024):.1f} MB / {total_expected / (1024*1024):.1f} MB ({pct:.1f}%)"
                                    ))

                        # Ensure at least one stage 5 progress event is emitted on completion
                        if progress_callback and not self.is_cancelled:
                            pct = (downloaded_bytes / total_expected * 100.0) if total_expected > 0 else 100.0
                            progress_callback(DownloadProgress(
                                stage=5,
                                stage_name=STAGE_NAMES[5],
                                downloaded_bytes=downloaded_bytes,
                                total_bytes=total_expected,
                                percent=min(pct, 100.0),
                                speed_bps=current_speed,
                                status_text=f"Download payload complete ({downloaded_bytes / (1024*1024):.1f} MB)."
                            ))

                    if self.is_cancelled:
                        if part_file.exists():
                            try:
                                part_file.unlink()
                            except OSError:
                                pass
                        raise DownloadError("Download cancelled by user.")

                    # Download complete for this attempt
                    break

            except urllib.error.HTTPError as e:
                # HTTP 429 Rate Limit Handling
                if e.code == 429:
                    retry_after = e.headers.get("Retry-After")
                    delay = int(retry_after) if retry_after and retry_after.isdigit() else (self.base_backoff_sec * (2 ** attempt))
                    if progress_callback:
                        progress_callback(DownloadProgress(
                            stage=5,
                            stage_name=STAGE_NAMES[5],
                            status_text=f"Rate limit hit (HTTP 429). Backing off for {delay}s (attempt {attempt}/{self.max_retries})..."
                        ))
                    time.sleep(delay)
                    continue

                # Permanent errors fail immediately
                if e.code in (401, 403, 404):
                    raise DownloadError(f"HTTP Permanent failure {e.code} ({e.reason}) accessing '{payload_url}'.")

                # Transient 5xx errors retry
                if attempt < self.max_retries:
                    delay = self.base_backoff_sec * (2 ** attempt) + random.uniform(0.1, 0.5)
                    if progress_callback:
                        progress_callback(DownloadProgress(
                            stage=5,
                            stage_name=STAGE_NAMES[5],
                            status_text=f"Server returned HTTP {e.code}. Retrying in {delay:.1f}s (attempt {attempt}/{self.max_retries})..."
                        ))
                    time.sleep(delay)
                    continue
                raise DownloadError(f"Download failed after {self.max_retries} attempts: HTTP {e.code} ({e.reason})")

            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if attempt < self.max_retries:
                    delay = self.base_backoff_sec * (2 ** attempt) + random.uniform(0.1, 0.5)
                    if progress_callback:
                        progress_callback(DownloadProgress(
                            stage=5,
                            stage_name=STAGE_NAMES[5],
                            status_text=f"Network interruption ({e}). Retrying in {delay:.1f}s (attempt {attempt}/{self.max_retries})..."
                        ))
                    time.sleep(delay)
                    continue
                raise DownloadError(f"Download interrupted after {self.max_retries} attempts: {e}")

        if not part_file.exists():
            raise DownloadError("Download failed: no output file created.")

        # Stage 6: Cryptographic Verification of Downloaded Payload
        if progress_callback:
            progress_callback(DownloadProgress(
                stage=6,
                stage_name=STAGE_NAMES[6],
                downloaded_bytes=downloaded_bytes,
                total_bytes=expected_size_bytes,
                percent=100.0,
                status_text="Verifying SHA-256 cryptographic checksum of downloaded archive..."
            ))

        actual_sha = compute_sha256(part_file)
        if actual_sha.lower() != expected_sha256.lower():
            try:
                part_file.unlink()
            except OSError:
                pass
            raise VerificationError(
                f"SHA-256 digest mismatch! Expected: {expected_sha256.lower()}, "
                f"Calculated: {actual_sha.lower()}. Downloaded file is corrupted or tampered."
            )

        # Atomic promotion from .part to .verified
        if verified_file.exists():
            try:
                verified_file.unlink()
            except OSError:
                pass
        part_file.rename(verified_file)
        return verified_file
