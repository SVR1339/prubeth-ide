"""
PRUBETH IDE — Release Configuration, Delivery Modes & Cryptographic Trust Anchors
Defines official repository coordinates, release asset layouts, 70 MiB size threshold,
delivery modes (Mode A Online vs Mode B Offline), and release signature verification.
"""
import os
import hmac
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# --- Product Metadata ---
APP_NAME = "PRUBETH"
APP_DISPLAY_NAME = "PRUBETH IDE — Horizon Edition"
APP_TAGLINE = "Bloom, ideas unfolding"
APP_VERSION = "3.0.0"
PUBLISHER = "BSVR Technologies"
WEBSITE_URL = "https://www.bsvr.work/"
GITHUB_REPO = "imyouiamyou/prubeth-ide"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO}"
DEFAULT_CHANNEL = "stable"
SUPPORTED_CHANNELS = ["stable", "beta", "dev"]
TARGET_ARCH = "windows-x64"

# --- Threshold & Delivery Mode Configuration ---
# Threshold rule: if the complete offline distributable is >= 70 MiB (binary),
# publish a lightweight online Setup.exe that retrieves the version-matched payload.
# 70 MiB binary = 70 * 1024 * 1024 = 73,400,320 bytes.
# Configurable via environment variable or CLI.
DEFAULT_ONLINE_THRESHOLD_MIB = 70.0
ONLINE_THRESHOLD_BYTES = int(DEFAULT_ONLINE_THRESHOLD_MIB * 1024 * 1024)

# Delivery Mode Constants
MODE_ONLINE = "online"    # Mode A: Lightweight bootstrap installer (< 70 MiB rule)
MODE_OFFLINE = "offline"  # Mode B: Full standalone installer with embedded payload
MODE_AUTO = "auto"        # Automatically select based on package size threshold

# --- Cryptographic Trust Anchor ---
# Trusted public verification anchor embedded into the bootstrapper.
# In production release signing, manifests are signed using HMAC-SHA256 with the
# release signing authority key, or verified against this cryptographic trust digest.
TRUSTED_RELEASE_SIGNER_ID = "BSVR-PRUBETH-RELEASE-SIGNING-AUTHORITY-v3"
TRUSTED_PUBLIC_VERIFICATION_KEY = (
    "9f8a3c5e7b1d4f2a8e6c0b3d5a7f9e1c2b4d6a8f0e2c4a6b8d0e2f4a6b8c0d2e"
)

# Documented Exit Codes for Automation
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_INVALID_ARGS = 2
EXIT_NETWORK_ERROR = 3
EXIT_VERIFICATION_FAILED = 4
EXIT_INSUFFICIENT_SPACE = 5
EXIT_USER_CANCELLED = 6


def get_configured_threshold_bytes() -> int:
    """Returns the effective online threshold in bytes (checking environment override)."""
    env_thresh = os.environ.get("PRUBETH_INSTALLER_THRESHOLD_MIB")
    if env_thresh:
        try:
            val = float(env_thresh)
            return int(val * 1024 * 1024)
        except ValueError:
            pass
    return ONLINE_THRESHOLD_BYTES


def evaluate_delivery_mode(package_size_bytes: int, requested_mode: str = MODE_AUTO) -> Tuple[str, str]:
    """
    Evaluates whether Mode A (Online) or Mode B (Offline) should be published.
    Returns (mode, reason).
    """
    if requested_mode == MODE_ONLINE:
        return MODE_ONLINE, "Explicitly configured for Mode A (Lightweight Online Bootstrapper)."
    if requested_mode == MODE_OFFLINE:
        return MODE_OFFLINE, "Explicitly configured for Mode B (Full Offline Installer)."

    threshold_bytes = get_configured_threshold_bytes()
    thresh_mib = threshold_bytes / (1024 * 1024)
    pkg_mib = package_size_bytes / (1024 * 1024)

    if package_size_bytes >= threshold_bytes:
        return (
            MODE_ONLINE,
            f"Package size ({pkg_mib:.2f} MiB) meets/exceeds the configured threshold "
            f"({thresh_mib:.2f} MiB). Mode A (Lightweight Online Bootstrapper) selected."
        )
    else:
        return (
            MODE_OFFLINE,
            f"Package size ({pkg_mib:.2f} MiB) is below the configured threshold "
            f"({thresh_mib:.2f} MiB). Mode B (Full Offline Installer) selected."
        )


def get_asset_filenames(version: str = APP_VERSION, arch: str = TARGET_ARCH) -> Dict[str, str]:
    """Generates standard predictable asset filenames for a release."""
    return {
        "bootstrap_installer": f"Prubeth-Setup-{version}.exe",
        "setup_alias": "Setup.exe",
        "offline_installer": f"Prubeth-Offline-Setup-{version}.exe",
        "payload": f"Prubeth-Payload-{version}-{arch}.zip",
        "manifest": f"Prubeth-Manifest-{version}.json",
        "manifest_sig": f"Prubeth-Manifest-{version}.sig",
        "sha256sums": "Prubeth-SHA256SUMS.txt",
        "release_notes": f"Prubeth-Release-Notes-{version}.md",
        "sbom": f"Prubeth-SBOM-{version}.json"
    }


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 digest of a local file in streaming blocks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_manifest_signature(manifest_bytes: bytes, signing_key: str = TRUSTED_PUBLIC_VERIFICATION_KEY) -> str:
    """Generates a cryptographic HMAC-SHA256 signature for the manifest bytes."""
    return hmac.new(signing_key.encode("utf-8"), manifest_bytes, hashlib.sha256).hexdigest()


def verify_manifest_signature(manifest_bytes: bytes, signature_hex: str, verification_key: str = TRUSTED_PUBLIC_VERIFICATION_KEY) -> bool:
    """Cryptographically verifies that the manifest was issued by the trusted authority."""
    expected = compute_manifest_signature(manifest_bytes, verification_key)
    return hmac.compare_digest(expected.lower(), signature_hex.strip().lower())
