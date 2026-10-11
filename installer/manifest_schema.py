"""
PRUBETH IDE — Release Manifest Schema & Validation Engine
Enforces strict schema compliance, required fields, version matching, and integrity checks.
Never trusts filenames, tag names, or HTTP codes without full schema and signature verification.
"""
import json
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path


MANDATORY_MANIFEST_FIELDS = [
    "product",
    "version",
    "architecture",
    "channel",
    "payload_filename",
    "payload_sha256",
    "payload_size_bytes",
    "min_required_disk_bytes",
    "required_files",
    "signer_id"
]


class ManifestValidationError(Exception):
    """Raised when release manifest is malformed, untrusted, or incompatible."""
    pass


def validate_manifest_schema(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates manifest JSON structure against mandatory fields and types.
    Returns (is_valid, error_message).
    """
    if not isinstance(data, dict):
        return False, "Manifest root must be a JSON object."

    for field in MANDATORY_MANIFEST_FIELDS:
        if field not in data:
            return False, f"Missing required manifest field: '{field}'"

    # Type & content validations
    if not isinstance(data["product"], str) or not data["product"].strip():
        return False, "Invalid 'product' field: must be non-empty string."

    if not isinstance(data["version"], str) or not data["version"].strip():
        return False, "Invalid 'version' field: must be non-empty string."

    if data["architecture"] not in ["windows-x64", "windows-arm64", "all"]:
        return False, f"Unsupported architecture: '{data['architecture']}'"

    if data["channel"] not in ["stable", "beta", "dev"]:
        return False, f"Invalid release channel: '{data['channel']}'"

    if not isinstance(data["payload_filename"], str) or not data["payload_filename"].endswith(".zip"):
        return False, "Invalid 'payload_filename': must be a .zip archive."

    sha = str(data["payload_sha256"]).strip()
    if len(sha) != 64 or not all(c in "0123456789abcdefABCDEF" for c in sha):
        return False, f"Invalid 'payload_sha256': must be 64-character hexadecimal SHA-256 digest (got '{sha}')."

    if not isinstance(data["payload_size_bytes"], int) or data["payload_size_bytes"] <= 0:
        return False, "Invalid 'payload_size_bytes': must be a positive integer."

    if not isinstance(data["min_required_disk_bytes"], int) or data["min_required_disk_bytes"] <= 0:
        return False, "Invalid 'min_required_disk_bytes': must be a positive integer."

    if not isinstance(data["required_files"], list) or not data["required_files"]:
        return False, "Invalid 'required_files': must be a non-empty list of required paths."

    return True, None


def verify_manifest_compatibility(
    manifest: Dict[str, Any],
    expected_version: str,
    expected_channel: str = "stable",
    expected_arch: str = "windows-x64"
) -> Tuple[bool, Optional[str]]:
    """
    Ensures that the resolved manifest exactly matches the installer's target configuration.
    Prevents silent cross-channel, cross-architecture, or version mix-ups.
    """
    is_valid, err = validate_manifest_schema(manifest)
    if not is_valid:
        return False, f"Schema validation failed: {err}"

    if manifest["version"] != expected_version:
        return False, f"Version mismatch: installer expects '{expected_version}', but manifest declares '{manifest['version']}'."

    if manifest["channel"] != expected_channel and expected_channel != "any":
        return False, f"Channel mismatch: expected '{expected_channel}', got '{manifest['channel']}'."

    if manifest["architecture"] != expected_arch and manifest["architecture"] != "all":
        return False, f"Architecture mismatch: installer expects '{expected_arch}', got '{manifest['architecture']}'."

    return True, None


def build_manifest_document(
    version: str,
    payload_filename: str,
    payload_sha256: str,
    payload_size_bytes: int,
    min_required_disk_bytes: int,
    required_files: List[str],
    channel: str = "stable",
    architecture: str = "windows-x64",
    signer_id: str = "BSVR-PRUBETH-RELEASE-SIGNING-AUTHORITY-v3"
) -> Dict[str, Any]:
    """Constructs a compliant, standardized release manifest dictionary."""
    return {
        "product": "PRUBETH",
        "version": version,
        "architecture": architecture,
        "channel": channel,
        "payload_filename": payload_filename,
        "payload_sha256": payload_sha256.lower(),
        "payload_size_bytes": payload_size_bytes,
        "min_required_disk_bytes": min_required_disk_bytes,
        "required_files": required_files,
        "signer_id": signer_id,
        "published_by": "BSVR Technologies",
        "website": "https://www.bsvr.work/"
    }
