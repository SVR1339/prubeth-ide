"""
PRUBETH IDE — Disk Space Management & Multi-Volume Validation Engine
Calculates space requirements for compressed payload, staging, extraction, and upgrade backups.
Independently verifies target installation volume and staging/temp volume headroom.
Never deletes user files automatically.
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


class DiskSpaceCheckResult:
    def __init__(
        self,
        is_sufficient: bool,
        target_required_bytes: int,
        target_available_bytes: int,
        target_volume: str,
        staging_required_bytes: int,
        staging_available_bytes: int,
        staging_volume: str,
        insufficient_reason: Optional[str] = None
    ):
        self.is_sufficient = is_sufficient
        self.target_required_bytes = target_required_bytes
        self.target_available_bytes = target_available_bytes
        self.target_volume = target_volume
        self.staging_required_bytes = staging_required_bytes
        self.staging_available_bytes = staging_available_bytes
        self.staging_volume = staging_volume
        self.insufficient_reason = insufficient_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_sufficient": self.is_sufficient,
            "target_required_mb": self.target_required_bytes / (1024 * 1024),
            "target_available_mb": self.target_available_bytes / (1024 * 1024),
            "target_volume": self.target_volume,
            "staging_required_mb": self.staging_required_bytes / (1024 * 1024),
            "staging_available_mb": self.staging_available_bytes / (1024 * 1024),
            "staging_volume": self.staging_volume,
            "insufficient_reason": self.insufficient_reason
        }


def get_path_volume(path: Path) -> Path:
    """Returns the root mount/drive path for a given filesystem path."""
    p = path.resolve()
    while p.parent != p:
        if p.exists():
            return p
        p = p.parent
    return p


def get_available_bytes(path: Path) -> int:
    """Returns available free disk space in bytes for the volume hosting the given path."""
    try:
        # Resolve to an existing parent if path does not exist yet
        check_p = path.resolve()
        while not check_p.exists() and check_p.parent != check_p:
            check_p = check_p.parent
        usage = shutil.disk_usage(str(check_p))
        return usage.free
    except Exception:
        return 0


def calculate_directory_size(path: Path) -> int:
    """Calculates total size of existing directory in bytes."""
    if not path.exists() or not path.is_dir():
        return 0
    total = 0
    try:
        for p in path.rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except OSError:
                    pass
    except Exception:
        pass
    return total


def estimate_space_requirements(
    payload_size_bytes: int,
    is_upgrade: bool = False,
    existing_dir: Optional[Path] = None,
    safety_margin_bytes: int = 50 * 1024 * 1024  # 50 MB buffer
) -> Dict[str, int]:
    """
    Estimates space requirements across lifecycle:
    - compressed payload download
    - extraction staging area
    - final target installation files
    - upgrade backup of existing directory (if upgrading)
    """
    # Compressed payload downloaded to temp
    download_bytes = payload_size_bytes
    # Extracted application files estimate (~3x compressed size if unknown)
    extracted_app_bytes = int(payload_size_bytes * 3.0)
    # Staging workspace during safe extraction
    staging_bytes = extracted_app_bytes + (10 * 1024 * 1024)

    # Upgrade backup if existing directory has files
    backup_bytes = 0
    if is_upgrade and existing_dir and existing_dir.exists():
        backup_bytes = calculate_directory_size(existing_dir)

    return {
        "download_bytes": download_bytes,
        "staging_bytes": staging_bytes,
        "extracted_app_bytes": extracted_app_bytes,
        "backup_bytes": backup_bytes,
        "safety_margin_bytes": safety_margin_bytes,
        "total_staging_volume_bytes": download_bytes + staging_bytes + safety_margin_bytes,
        "total_target_volume_bytes": extracted_app_bytes + backup_bytes + safety_margin_bytes
    }


def verify_disk_space(
    target_dir: Path,
    payload_size_bytes: int,
    staging_dir: Optional[Path] = None,
    is_upgrade: bool = False
) -> DiskSpaceCheckResult:
    """
    Performs complete multi-volume disk space validation.
    Checks target drive and staging/temp drive independently.
    """
    if staging_dir is None:
        staging_dir = Path(tempfile.gettempdir())

    target_vol = str(get_path_volume(target_dir))
    staging_vol = str(get_path_volume(staging_dir))

    reqs = estimate_space_requirements(payload_size_bytes, is_upgrade, target_dir)

    target_avail = get_available_bytes(target_dir)
    staging_avail = get_available_bytes(staging_dir)

    # Same volume check vs separate volume check
    if target_vol.lower() == staging_vol.lower():
        # Both on same volume: need sum of staging and target requirements simultaneously
        combined_req = reqs["total_staging_volume_bytes"] + reqs["total_target_volume_bytes"]
        if target_avail < combined_req:
            shortage_mb = (combined_req - target_avail) / (1024 * 1024)
            req_mb = combined_req / (1024 * 1024)
            avail_mb = target_avail / (1024 * 1024)
            reason = (
                f"Insufficient disk space on volume '{target_vol}'. "
                f"Required: {req_mb:.1f} MB, Available: {avail_mb:.1f} MB (Shortage: {shortage_mb:.1f} MB). "
                f"Please choose a different drive or free space before continuing."
            )
            return DiskSpaceCheckResult(
                is_sufficient=False,
                target_required_bytes=combined_req,
                target_available_bytes=target_avail,
                target_volume=target_vol,
                staging_required_bytes=combined_req,
                staging_available_bytes=staging_avail,
                staging_volume=staging_vol,
                insufficient_reason=reason
            )
    else:
        # Separate volumes: check each volume independently
        if target_avail < reqs["total_target_volume_bytes"]:
            shortage_mb = (reqs["total_target_volume_bytes"] - target_avail) / (1024 * 1024)
            req_mb = reqs["total_target_volume_bytes"] / (1024 * 1024)
            avail_mb = target_avail / (1024 * 1024)
            reason = (
                f"Insufficient space on installation volume '{target_vol}'. "
                f"Required: {req_mb:.1f} MB, Available: {avail_mb:.1f} MB (Shortage: {shortage_mb:.1f} MB)."
            )
            return DiskSpaceCheckResult(
                is_sufficient=False,
                target_required_bytes=reqs["total_target_volume_bytes"],
                target_available_bytes=target_avail,
                target_volume=target_vol,
                staging_required_bytes=reqs["total_staging_volume_bytes"],
                staging_available_bytes=staging_avail,
                staging_volume=staging_vol,
                insufficient_reason=reason
            )

        if staging_avail < reqs["total_staging_volume_bytes"]:
            shortage_mb = (reqs["total_staging_volume_bytes"] - staging_avail) / (1024 * 1024)
            req_mb = reqs["total_staging_volume_bytes"] / (1024 * 1024)
            avail_mb = staging_avail / (1024 * 1024)
            reason = (
                f"Insufficient space on staging/temporary volume '{staging_vol}'. "
                f"Required: {req_mb:.1f} MB, Available: {avail_mb:.1f} MB (Shortage: {shortage_mb:.1f} MB)."
            )
            return DiskSpaceCheckResult(
                is_sufficient=False,
                target_required_bytes=reqs["total_target_volume_bytes"],
                target_available_bytes=target_avail,
                target_volume=target_vol,
                staging_required_bytes=reqs["total_staging_volume_bytes"],
                staging_available_bytes=staging_avail,
                staging_volume=staging_vol,
                insufficient_reason=reason
            )

    return DiskSpaceCheckResult(
        is_sufficient=True,
        target_required_bytes=reqs["total_target_volume_bytes"],
        target_available_bytes=target_avail,
        target_volume=target_vol,
        staging_required_bytes=reqs["total_staging_volume_bytes"],
        staging_available_bytes=staging_avail,
        staging_volume=staging_vol,
        insufficient_reason=None
    )
