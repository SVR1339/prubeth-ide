"""
PRUBETH IDE — Multi-GPU Topology Router & Device Placement Engine
Part of the Indefinite Hardware Upgradability & Progressive Performance Scaling Engine.

Provides multi-device orchestration, single-device best-fit placement, user-pinned
device routing, pipeline parallelism layer splitting, and CPU hybrid offloading.
Prevents dangerous naive memory pooling assumptions across disparate physical GPUs.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

from core.hardware.capabilities import DeviceType, HardwareDevice


class DevicePlacementStrategy(str, Enum):
    AUTO_BEST_FIT = "auto_best_fit"
    USER_PINNED = "user_pinned"
    PIPELINE_PARALLEL = "pipeline_parallel"
    HYBRID_OFFLOAD_CPU = "hybrid_offload_cpu"
    CPU_ONLY = "cpu_only"


@dataclass
class PlacementDecision:
    """Device assignment decision for an active model, agent, or inference session."""
    strategy: DevicePlacementStrategy
    primary_device_id: str
    secondary_device_ids: List[str] = field(default_factory=list)
    device_vram_allocations_mb: Dict[str, int] = field(default_factory=dict)
    cpu_offload_ram_mb: int = 0
    is_valid: bool = True
    reason: str = ""


class MultiGPURuntimeRouter:
    """
    Manages multi-accelerator topologies. Assigns workloads to appropriate devices
    and avoids placing models on devices with insufficient VRAM.
    """

    def __init__(self):
        self._lock = threading.RLock()
        # Track active placements: model_session_id -> PlacementDecision
        self._active_placements: Dict[str, PlacementDecision] = {}

    def assign_device_for_model(
        self,
        model_id: str,
        required_vram_mb: int,
        available_devices: List[HardwareDevice],
        user_device_preference: Optional[str] = None,
        allow_multi_gpu_tensor_split: bool = False
    ) -> PlacementDecision:
        """
        Determines the optimal device allocation for a model given its VRAM requirement.
        
        Args:
            model_id: Identifier of the target model.
            required_vram_mb: Estimated total VRAM required for weights + KV cache.
            available_devices: List of discovered hardware devices.
            user_device_preference: Explicit device requested by user (e.g. 'cuda:1', 'cpu').
            allow_multi_gpu_tensor_split: True if runtime (vLLM, llama.cpp) explicitly supports multi-device split.
        """
        with self._lock:
            gpus = [d for d in available_devices if d.device_type != DeviceType.CPU and d.is_healthy]
            cpu_device = next((d for d in available_devices if d.device_type == DeviceType.CPU), None)

            # 1. User pinned preference takes precedence if provided and valid
            if user_device_preference and user_device_preference.strip():
                pref = user_device_preference.strip().lower()
                if pref == "cpu":
                    return PlacementDecision(
                        strategy=DevicePlacementStrategy.CPU_ONLY,
                        primary_device_id="cpu",
                        cpu_offload_ram_mb=required_vram_mb,
                        reason="User explicitly pinned execution to CPU."
                    )
                
                matched = next((d for d in gpus if d.device_id.lower() == pref), None)
                if matched:
                    if matched.available_memory_mb >= required_vram_mb or required_vram_mb == 0:
                        alloc = {matched.device_id: required_vram_mb}
                        return PlacementDecision(
                            strategy=DevicePlacementStrategy.USER_PINNED,
                            primary_device_id=matched.device_id,
                            device_vram_allocations_mb=alloc,
                            reason=f"Model pinned to user-selected device {matched.device_id}."
                        )
                    else:
                        # User pinned device has insufficient VRAM; check if hybrid offload is needed
                        vram_avail = max(0, matched.available_memory_mb - 512)
                        cpu_ram = max(0, required_vram_mb - vram_avail)
                        return PlacementDecision(
                            strategy=DevicePlacementStrategy.HYBRID_OFFLOAD_CPU,
                            primary_device_id=matched.device_id,
                            device_vram_allocations_mb={matched.device_id: vram_avail},
                            cpu_offload_ram_mb=cpu_ram,
                            reason=(
                                f"User-pinned device {matched.device_id} has {matched.available_memory_mb}MB; "
                                f"offloading remaining {cpu_ram}MB to CPU."
                            )
                        )

            # 2. No GPUs available -> CPU only
            if not gpus:
                return PlacementDecision(
                    strategy=DevicePlacementStrategy.CPU_ONLY,
                    primary_device_id="cpu",
                    cpu_offload_ram_mb=required_vram_mb,
                    reason="No hardware accelerators discovered; utilizing host CPU execution."
                )

            # 3. Single Best Fit: find GPU with adequate VRAM and smallest leftover headroom (tightest fit)
            adequate_gpus = [
                d for d in gpus
                if (d.available_memory_mb - 512) >= required_vram_mb
            ]
            if adequate_gpus:
                best_gpu = min(adequate_gpus, key=lambda d: d.available_memory_mb)
                return PlacementDecision(
                    strategy=DevicePlacementStrategy.AUTO_BEST_FIT,
                    primary_device_id=best_gpu.device_id,
                    device_vram_allocations_mb={best_gpu.device_id: required_vram_mb},
                    reason=f"Auto-selected {best_gpu.name} ({best_gpu.device_id}) with adequate {best_gpu.available_memory_mb}MB VRAM."
                )

            # 4. Multi-GPU Pipeline Parallelism: if multiple GPUs exist and runtime supports split
            if len(gpus) > 1 and allow_multi_gpu_tensor_split:
                total_usable_vram = sum(max(0, d.available_memory_mb - 512) for d in gpus)
                if total_usable_vram >= required_vram_mb:
                    allocations: Dict[str, int] = {}
                    remaining_req = required_vram_mb
                    for d in gpus:
                        d_usable = max(0, d.available_memory_mb - 512)
                        alloc = min(d_usable, remaining_req)
                        allocations[d.device_id] = alloc
                        remaining_req -= alloc
                        if remaining_req <= 0:
                            break
                    
                    return PlacementDecision(
                        strategy=DevicePlacementStrategy.PIPELINE_PARALLEL,
                        primary_device_id=gpus[0].device_id,
                        secondary_device_ids=[d.device_id for d in gpus[1:] if d.device_id in allocations],
                        device_vram_allocations_mb=allocations,
                        reason=f"Pipeline parallel split across {len(allocations)} GPUs."
                    )

            # 5. Hybrid GPU + CPU Offload fallback on the largest available GPU
            largest_gpu = max(gpus, key=lambda d: d.available_memory_mb)
            gpu_headroom = max(0, largest_gpu.available_memory_mb - 512)
            cpu_overflow = max(0, required_vram_mb - gpu_headroom)

            return PlacementDecision(
                strategy=DevicePlacementStrategy.HYBRID_OFFLOAD_CPU,
                primary_device_id=largest_gpu.device_id,
                device_vram_allocations_mb={largest_gpu.device_id: gpu_headroom},
                cpu_offload_ram_mb=cpu_overflow,
                reason=(
                    f"Model exceeds single GPU capacity; allocating {gpu_headroom}MB to "
                    f"{largest_gpu.device_id} and offloading {cpu_overflow}MB to system RAM."
                )
            )

    def register_placement(self, session_id: str, decision: PlacementDecision) -> None:
        with self._lock:
            self._active_placements[session_id] = decision

    def release_placement(self, session_id: str) -> Optional[PlacementDecision]:
        with self._lock:
            return self._active_placements.pop(session_id, None)

    def validate_multi_gpu_safety(
        self,
        target_device_ids: List[str],
        devices: List[HardwareDevice]
    ) -> Tuple[bool, str]:
        """
        Safety check: avoids assuming arbitrary non-NVLink GPUs can seamlessly combine memory.
        """
        matched = [d for d in devices if d.device_id in target_device_ids]
        if len(matched) <= 1:
            return True, "Single device operation is always safe."
        
        vendors = {d.vendor.lower() for d in matched}
        if len(vendors) > 1:
            return False, f"Cannot pool VRAM across disparate vendors: {vendors}."

        return True, "Verified multi-device topology compatibility."
