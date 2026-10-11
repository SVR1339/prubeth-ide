"""
PRUBETH IDE — Upgrade-Safe Hardware Persistence & Migration Manager
Part of the Indefinite Hardware Upgradability & Progressive Performance Scaling Engine.

Separates user manual preferences from dynamic machine telemetry profiles.
Detects hardware upgrades and driver changes safely without invalidating user projects,
checkpoints, agent history, or manual configurations.
"""

from __future__ import annotations

import os
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from core.hardware.capabilities import HardwareSnapshot
from core.hardware.performance_tiers import DynamicPerformanceTierEngine, ScalingProfile


class HardwarePersistenceManager:
    """
    Manages isolated, upgrade-safe persistence for detected hardware topologies,
    scaling profiles, and historical hardware upgrade audit journals.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            self.storage_dir = Path.home() / ".local_ai_studio_pro" / "hardware"
        else:
            self.storage_dir = Path(storage_dir)

        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        self.profile_path = self.storage_dir / "detected_profile.json"
        self.audit_log_path = self.storage_dir / "hardware_audit.log"

    def load_cached_profile(self) -> Optional[Dict[str, Any]]:
        """Loads previously detected hardware profile if available."""
        if not self.profile_path.exists():
            return None
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save_detected_profile(
        self,
        snapshot: HardwareSnapshot,
        scaling_profile: ScalingProfile
    ) -> None:
        """Atomically persists the current hardware snapshot and scaling profile."""
        data = {
            "saved_at": time.time(),
            "snapshot": snapshot.to_dict(),
            "scaling_profile": {
                "tier_level": scaling_profile.tier_level.value,
                "tier_name": scaling_profile.tier_name,
                "max_parallel_agents": scaling_profile.max_parallel_agents,
                "background_workers": scaling_profile.background_workers,
                "cache_mb": scaling_profile.cache_capacity_mb,
                "indexing_workers": scaling_profile.indexing_workers,
                "recommended_quantization": scaling_profile.recommended_quantization,
                "description": scaling_profile.description
            }
        }

        try:
            tmp_fd, tmp_file = tempfile.mkstemp(dir=str(self.storage_dir), prefix="hw_prof_", suffix=".tmp")
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_file, str(self.profile_path))
        except Exception:
            pass

    def record_hardware_event(self, event_description: str) -> None:
        """Appends a timestamped hardware change event to the audit log."""
        try:
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            line = f"[{timestamp_str}] {event_description}\n"
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def synchronize_hardware_upgrade(
        self,
        new_snapshot: HardwareSnapshot,
        user_settings: Dict[str, Any],
        auto_scale_enabled: bool = True
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Compares new snapshot against cached profile. If hardware has upgraded or changed:
        1. Logs the diff to hardware_audit.log.
        2. Safely updates auto-detected performance parameters in settings.
        3. Strictly preserves user manual overrides and project metadata.
        
        Returns:
            (has_hardware_changed, updated_settings, audit_changes)
        """
        cached = self.load_cached_profile()
        scaling_profile = DynamicPerformanceTierEngine.evaluate_hardware(new_snapshot)
        audit_changes: List[str] = []

        if cached is None:
            # First initialization
            self.save_detected_profile(new_snapshot, scaling_profile)
            self.record_hardware_event(f"Initial hardware profile established: {scaling_profile.tier_name}")
            audit_changes.append(f"Initial hardware profile detected: {scaling_profile.tier_name}")
            
            if auto_scale_enabled:
                user_settings = self._merge_scaling_safely(user_settings, scaling_profile)
            return True, user_settings, audit_changes

        cached_snap = cached.get("snapshot", {})
        old_fingerprint = cached_snap.get("environment_fingerprint", "")
        new_fingerprint = new_snapshot.environment_fingerprint

        if old_fingerprint == new_fingerprint:
            # Hardware is identical
            return False, user_settings, []

        # Hardware change detected!
        old_ram = cached_snap.get("memory", {}).get("total_ram_mb", 0)
        new_ram = new_snapshot.memory.total_ram_mb
        old_vram = cached_snap.get("total_gpu_vram_mb", 0)
        new_vram = new_snapshot.total_gpu_vram_mb
        old_tier = cached.get("scaling_profile", {}).get("tier_name", "Unknown")
        new_tier = scaling_profile.tier_name

        if new_ram != old_ram:
            diff_msg = f"System RAM changed: {old_ram}MB -> {new_ram}MB"
            audit_changes.append(diff_msg)
            self.record_hardware_event(diff_msg)

        if new_vram != old_vram:
            diff_msg = f"GPU VRAM changed: {old_vram}MB -> {new_vram}MB"
            audit_changes.append(diff_msg)
            self.record_hardware_event(diff_msg)

        if old_tier != new_tier:
            tier_msg = f"Performance tier scaled: {old_tier} -> {new_tier}"
            audit_changes.append(tier_msg)
            self.record_hardware_event(tier_msg)

        # Update cached profile
        self.save_detected_profile(new_snapshot, scaling_profile)

        # Apply safe performance delta if auto-scaling is active
        if auto_scale_enabled:
            user_settings = self._merge_scaling_safely(user_settings, scaling_profile)

        return True, user_settings, audit_changes

    def _merge_scaling_safely(
        self,
        settings: Dict[str, Any],
        profile: ScalingProfile
    ) -> Dict[str, Any]:
        """
        Merges new hardware scaling parameters into user settings without
        overwriting explicitly user-pinned models, API keys, or custom directories.
        """
        delta = profile.to_settings_delta()

        # Update nested performance block if present
        if "performance" in settings and isinstance(settings["performance"], dict):
            p = settings["performance"]
            p["background_workers"] = delta["background_workers"]
            p["cache_mb"] = delta["cache_mb"]
            p["low_memory_mode"] = delta["low_memory_mode"]

        # Update nested agents block if present
        if "agents" in settings and isinstance(settings["agents"], dict):
            a = settings["agents"]
            a["max_parallel_agents"] = delta["max_parallel_agents"]
            a["max_task_steps"] = delta["max_task_steps"]

        # Flat bridge keys
        settings["background_workers"] = delta["background_workers"]
        settings["cache_mb"] = delta["cache_mb"]
        settings["low_memory_mode"] = delta["low_memory_mode"]
        settings["max_parallel_agents"] = delta["max_parallel_agents"]
        settings["hardware_tier"] = delta["hardware_tier"]

        return settings
