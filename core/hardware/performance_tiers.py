"""
PRUBETH IDE — Dynamic Performance Tier & Progressive Scaling Engine
Part of the Indefinite Hardware Upgradability & Progressive Performance Scaling Engine.

Continuously computes capability envelopes and progressive scaling parameters
(agent concurrency, indexing workers, cache sizes, local context limits, quantization)
based on real-time measured system capacity, battery topology, and multi-device compute.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, List, Optional

from core.hardware.capabilities import HardwareSnapshot, DeviceType, HardwareDevice


class PerformanceTierLevel(str, Enum):
    MINIMAL_ECO = "MINIMAL_ECO"
    STANDARD_BALANCED = "STANDARD_BALANCED"
    HIGH_PERFORMANCE = "HIGH_PERFORMANCE"
    WORKSTATION_PRO = "WORKSTATION_PRO"
    EXTREME_CLUSTER = "EXTREME_CLUSTER"


@dataclass
class ScalingProfile:
    """Dynamically synthesized execution parameters tailored to live host hardware capacity."""
    tier_level: PerformanceTierLevel
    tier_name: str
    max_parallel_agents: int
    max_task_steps: int
    background_workers: int
    indexing_workers: int
    indexing_batch_size: int
    cache_capacity_mb: int
    max_local_context_tokens: int
    recommended_quantization: str
    preferred_model_size_params: str
    simultaneous_provider_requests: int
    pause_indexing_on_battery: bool
    low_memory_mode: bool
    description: str
    scaling_multiplier: float = 1.0
    telemetry_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_settings_delta(self) -> Dict[str, Any]:
        """Translates scaling profile to settings dictionary updates."""
        return {
            "max_parallel_agents": self.max_parallel_agents,
            "max_task_steps": self.max_task_steps,
            "background_workers": self.background_workers,
            "indexing_workers": self.indexing_workers,
            "indexing_batch_size": self.indexing_batch_size,
            "cache_mb": self.cache_capacity_mb,
            "max_local_context_tokens": self.max_local_context_tokens,
            "recommended_quantization": self.recommended_quantization,
            "preferred_model_size_params": self.preferred_model_size_params,
            "simultaneous_provider_requests": self.simultaneous_provider_requests,
            "pause_indexing_on_battery": self.pause_indexing_on_battery,
            "low_memory_mode": self.low_memory_mode,
            "hardware_tier": self.tier_level.value
        }


class DynamicPerformanceTierEngine:
    """
    Evaluates hardware capabilities and synthesizes continuous, progressive performance
    configurations without artificial ceilings or vendor-locked limitations.
    """

    @classmethod
    def evaluate_hardware(cls, snapshot: HardwareSnapshot) -> ScalingProfile:
        """
        Synthesizes an optimal scaling profile from the hardware snapshot.
        Scales smoothly from 4GB laptops to 128GB+ multi-GPU computing nodes.
        """
        ram_mb = snapshot.memory.total_ram_mb
        cpu_threads = snapshot.cpu.logical_threads
        has_simd_fast = snapshot.cpu.supports_avx2 or snapshot.cpu.supports_avx512 or snapshot.cpu.supports_arm_neon
        is_battery = snapshot.power.is_on_battery
        is_power_saver = snapshot.power.is_power_saver_active

        # Sum total VRAM across all healthy accelerator devices
        gpu_devices = [d for d in snapshot.devices if d.device_type != DeviceType.CPU and d.is_healthy]
        total_vram_mb = sum(d.total_memory_mb for d in gpu_devices)
        gpu_count = len(gpu_devices)
        has_gpu = gpu_count > 0

        # Multi-factor score (0.0 to 100.0+)
        # RAM points: 1 pt per 1024MB RAM (e.g. 16GB -> 16 pts, 64GB -> 64 pts)
        ram_pts = ram_mb / 1024.0
        # CPU points: 2 pts per thread
        cpu_pts = cpu_threads * 2.0
        # GPU points: 3 pts per 1024MB VRAM + 10 pts bonus per discrete GPU
        gpu_pts = (total_vram_mb / 1024.0) * 3.0 + (gpu_count * 10.0 if has_gpu else 0.0)

        composite_score = ram_pts + cpu_pts + gpu_pts

        # Determine baseline tier level
        if ram_mb < 7500 or (not has_gpu and cpu_threads <= 4):
            level = PerformanceTierLevel.MINIMAL_ECO
            name = "Minimal Eco / Constrained"
        elif ram_mb < 15500 or (has_gpu and total_vram_mb <= 3500):
            level = PerformanceTierLevel.STANDARD_BALANCED
            name = "Standard Balanced"
        elif ram_mb < 32000 or (has_gpu and total_vram_mb <= 12000):
            level = PerformanceTierLevel.HIGH_PERFORMANCE
            name = "High Performance"
        elif ram_mb < 64000 or (has_gpu and total_vram_mb <= 24000):
            level = PerformanceTierLevel.WORKSTATION_PRO
            name = "Workstation Pro"
        else:
            level = PerformanceTierLevel.EXTREME_CLUSTER
            name = "Extreme Workstation / Cluster Fabric"

        # Apply battery conservation step-down if operating on battery
        if is_battery and level not in (PerformanceTierLevel.MINIMAL_ECO, PerformanceTierLevel.STANDARD_BALANCED):
            # Step down one tier to conserve battery thermals
            if level == PerformanceTierLevel.EXTREME_CLUSTER:
                level = PerformanceTierLevel.WORKSTATION_PRO
            elif level == PerformanceTierLevel.WORKSTATION_PRO:
                level = PerformanceTierLevel.HIGH_PERFORMANCE
            elif level == PerformanceTierLevel.HIGH_PERFORMANCE:
                level = PerformanceTierLevel.STANDARD_BALANCED
            name += " (Battery Saver Adjusted)"

        # Calculate progressive, continuous parameters
        # Concurrency scales with cores, constrained by RAM
        max_agents = max(1, min(int(cpu_threads // 2), int(ram_mb // 4096)))
        if level == PerformanceTierLevel.MINIMAL_ECO:
            max_agents = 1
        elif level == PerformanceTierLevel.EXTREME_CLUSTER:
            max_agents = max(8, min(cpu_threads, 32))

        # Background worker sizing
        bg_workers = max(1, min(cpu_threads // 2, 16))
        if is_battery:
            bg_workers = max(1, bg_workers // 2)

        # Indexing worker count and batch size
        idx_workers = max(1, min(cpu_threads // 4, 8))
        idx_batch = 25 if level == PerformanceTierLevel.MINIMAL_ECO else min(500, int(ram_mb / 128))

        # Dynamic cache capacity: ~5% of available RAM, clamped safely
        cache_mb = max(256, min(16384, int(ram_mb * 0.08)))

        # Context tokens calculation
        if level == PerformanceTierLevel.MINIMAL_ECO:
            max_context = 8192
            quant = "int4"
            model_params = "1B - 3B"
            max_steps = 25
            low_mem = True
        elif level == PerformanceTierLevel.STANDARD_BALANCED:
            max_context = 32768
            quant = "int4"
            model_params = "7B - 8B"
            max_steps = 40
            low_mem = False
        elif level == PerformanceTierLevel.HIGH_PERFORMANCE:
            max_context = 65536
            quant = "int8" if total_vram_mb >= 8000 else "int4"
            model_params = "8B - 14B"
            max_steps = 60
            low_mem = False
        elif level == PerformanceTierLevel.WORKSTATION_PRO:
            max_context = 131072
            quant = "fp16" if total_vram_mb >= 16000 else "int8"
            model_params = "14B - 32B"
            max_steps = 100
            low_mem = False
        else: # EXTREME_CLUSTER
            max_context = 262144
            quant = "fp16"
            model_params = "70B+ / Mixture of Experts"
            max_steps = 200
            low_mem = False

        simul_requests = max(2, min(32, int(ram_mb // 2048) + gpu_count * 2))

        desc = (
            f"Hardware Tier: {name} (Composite Score: {composite_score:.1f}). "
            f"Configured for {ram_mb}MB RAM, {cpu_threads} CPU threads, "
            f"{gpu_count} accelerator(s) ({total_vram_mb}MB VRAM). "
            f"Max agents: {max_agents}, Cache: {cache_mb}MB."
        )

        return ScalingProfile(
            tier_level=level,
            tier_name=name,
            max_parallel_agents=max_agents,
            max_task_steps=max_steps,
            background_workers=bg_workers,
            indexing_workers=idx_workers,
            indexing_batch_size=idx_batch,
            cache_capacity_mb=cache_mb,
            max_local_context_tokens=max_context,
            recommended_quantization=quant,
            preferred_model_size_params=model_params,
            simultaneous_provider_requests=simul_requests,
            pause_indexing_on_battery=is_battery,
            low_memory_mode=low_mem,
            description=desc,
            scaling_multiplier=round(composite_score / 25.0, 2),
            telemetry_metadata={
                "composite_score": composite_score,
                "ram_mb": ram_mb,
                "cpu_threads": cpu_threads,
                "gpu_count": gpu_count,
                "total_vram_mb": total_vram_mb,
                "is_on_battery": is_battery
            }
        )
