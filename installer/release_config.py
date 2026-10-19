"""
PRUBETH IDE — Release Configuration, Delivery Modes & Cryptographic Trust Anchors
Defines official repository coordinates, release asset layouts, 70 MiB size threshold,
delivery modes (Mode A Online vs Mode B Offline), and release signature verification.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# --- Product Metadata ---
APP_NAME = "PRUBETH"
APP_DISPLAY_NAME = "PRUBETH IDE — Horizon Edition"
APP_TAGLINE = "Bloom, ideas unfolding"
APP_VERSION = "1.91.0"
APP_TAG = "v1.91"
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

# --- Cryptographic Trust Anchor (Asymmetric Ed25519) ---
# In accordance with external security audit directive (Finding 3), asymmetric Ed25519 is used.
# The private signing key is strictly kept OUTSIDE the repository and binaries.
# Only the public verification key (32 bytes = 64 hex characters) is embedded in the installer.
# Any prior symmetric HMAC signing key is revoked and invalidated.
TRUSTED_RELEASE_SIGNER_ID = "BSVR-PRUBETH-RELEASE-AUTHORITY-ED25519-v1"
TRUSTED_PUBLIC_VERIFICATION_KEY = (
    "4290a6bf8ef8045d53657eddfcc7839bbf08b3ee2ecc83eedc64d32f54d63129"
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


def compute_manifest_signature(
    manifest_bytes: bytes,
    private_key_hex_or_bytes: Optional[Any] = None
) -> str:
    """
    Generates an asymmetric Ed25519 digital signature for release manifest bytes.
    The private key is strictly kept OUTSIDE released binaries.
    Resolves private key from explicit argument, PRUBETH_RELEASE_SIGNING_PRIVATE_KEY env,
    or local release_signing.key file.
    Returns 128-hex-character (64-byte) Ed25519 signature.
    """
    from cryptography.hazmat.primitives.asymmetric import ed25519

    priv_raw: Optional[bytes] = None
    if private_key_hex_or_bytes:
        if isinstance(private_key_hex_or_bytes, bytes):
            priv_raw = private_key_hex_or_bytes
        elif isinstance(private_key_hex_or_bytes, str):
            priv_raw = bytes.fromhex(private_key_hex_or_bytes.strip())
    else:
        env_key = os.environ.get("PRUBETH_RELEASE_SIGNING_PRIVATE_KEY")
        if env_key:
            priv_raw = bytes.fromhex(env_key.strip())
        else:
            key_file = Path(__file__).resolve().parent.parent / "release_signing.key"
            if key_file.exists():
                priv_raw = bytes.fromhex(key_file.read_text(encoding="utf-8").strip())

    if not priv_raw:
        raise ValueError(
            "Private release signing key not found. Set PRUBETH_RELEASE_SIGNING_PRIVATE_KEY "
            "or provide a valid release_signing.key outside git."
        )

    priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_raw)
    sig_bytes = priv_key.sign(manifest_bytes)
    return sig_bytes.hex()


def verify_manifest_signature(
    manifest_bytes: bytes,
    signature_hex: str,
    verification_key: str = TRUSTED_PUBLIC_VERIFICATION_KEY
) -> bool:
    """
    Cryptographically verifies an asymmetric Ed25519 signature against the trusted public key.
    Fails closed: returns True only if the signature is authentic and unaltered;
    returns False on any error, tampering, or key mismatch.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.exceptions import InvalidSignature

        pub_bytes = bytes.fromhex(verification_key.strip())
        sig_bytes = bytes.fromhex(signature_hex.strip())
        if len(pub_bytes) != 32 or len(sig_bytes) != 64:
            return False

        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        pub_key.verify(sig_bytes, manifest_bytes)
        return True
    except Exception:
        return False
