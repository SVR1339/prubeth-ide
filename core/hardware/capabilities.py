"""
PRUBETH IDE — Hardware Capabilities & Telemetry Contracts
Part of the Indefinite Hardware Upgradability & Progressive Performance Scaling Engine.

Defines vendor-agnostic data models for physical and virtual hardware resources,
including multi-device accelerators, CPU SIMD topologies, memory hierarchies,
storage capabilities, and point-in-time hardware snapshots.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, List, Optional, Set


class DeviceType(str, Enum):
    CPU = "cpu"
    NVIDIA_CUDA = "nvidia_cuda"
    AMD_ROCM = "amd_rocm"
    DIRECTML = "directml"
    INTEL_ACCEL = "intel_accel"
    APPLE_SILICON = "apple_silicon"
    FUTURE_ACCELERATOR = "future_accelerator"


class QuantizationType(str, Enum):
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    INT4 = "int4"
    FP8 = "fp8"
    FP4 = "fp4"


@dataclass
class HardwareDevice:
    """Represents a specific compute device (GPU, NPU, DSP, or custom accelerator)."""
    device_id: str                      # e.g. "cuda:0", "cuda:1", "rocm:0", "cpu"
    name: str                           # e.g. "NVIDIA GeForce RTX 4090", "Apple M3 Max"
    device_type: DeviceType
    vendor: str                         # "NVIDIA", "AMD", "Intel", "Apple", "Generic"
    driver_version: str = "Unknown"
    runtime_version: str = "Unknown"
    total_memory_mb: int = 0
    available_memory_mb: int = 0
    compute_capability: str = ""        # e.g. "sm_89", "gfx1100"
    supported_quantizations: List[str] = field(default_factory=lambda: ["fp32", "fp16", "int8", "int4"])
    is_primary: bool = False
    is_healthy: bool = True
    active_workload_count: int = 0
    temperature_celsius: Optional[float] = None
    power_usage_watts: Optional[float] = None
    pcie_generation: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def used_memory_mb(self) -> int:
        return max(0, self.total_memory_mb - self.available_memory_mb)

    @property
    def memory_utilization_ratio(self) -> float:
        if self.total_memory_mb <= 0:
            return 0.0
        return self.used_memory_mb / self.total_memory_mb


@dataclass
class CPUCapability:
    """Detailed capability analysis of host CPU topology and vector instruction sets."""
    physical_cores: int = 4
    logical_threads: int = 8
    architecture: str = "x86_64"        # "x86_64", "arm64", "riscv64"
    model_name: str = "Generic CPU"
    base_frequency_ghz: float = 2.5
    simd_extensions: List[str] = field(default_factory=list) # "AVX2", "AVX512", "AMX", "NEON", "SSE4_2"
    supports_avx2: bool = False
    supports_avx512: bool = False
    supports_amx: bool = False
    supports_arm_neon: bool = False
    numa_nodes: int = 1


@dataclass
class MemoryCapability:
    """System memory (RAM) capacity, operating process footprint, and swap status."""
    total_ram_mb: int = 16384
    available_ram_mb: int = 8192
    process_rss_mb: int = 512
    swap_total_mb: int = 8192
    swap_free_mb: int = 6144
    is_unified_memory: bool = False     # True for Apple Silicon, APUs, Tegra
    memory_bus_bandwidth_gbps: Optional[float] = None

    @property
    def ram_utilization_ratio(self) -> float:
        if self.total_ram_mb <= 0:
            return 0.0
        return max(0, self.total_ram_mb - self.available_ram_mb) / self.total_ram_mb


@dataclass
class StorageCapability:
    """Storage health and high-throughput cache / model weight storage capacity."""
    workspace_free_mb: int = 50000
    models_cache_free_mb: int = 50000
    storage_type: str = "SSD"           # "SSD", "NVMe", "HDD", "Unknown"
    is_fast_storage: bool = True


@dataclass
class PowerCapability:
    """Host power topology and battery state."""
    is_on_battery: bool = False
    battery_life_percent: Optional[int] = None
    is_power_saver_active: bool = False


@dataclass
class HardwareSnapshot:
    """
    Immutable point-in-time snapshot of complete host hardware resources.
    Serialized and compared to detect dynamic upgrades and downgrades.
    """
    timestamp: float = field(default_factory=time.time)
    os_name: str = "Unknown"
    os_release: str = "Unknown"
    cpu: CPUCapability = field(default_factory=CPUCapability)
    memory: MemoryCapability = field(default_factory=MemoryCapability)
    devices: List[HardwareDevice] = field(default_factory=list)
    storage: StorageCapability = field(default_factory=StorageCapability)
    power: PowerCapability = field(default_factory=PowerCapability)
    environment_fingerprint: str = ""

    @property
    def total_gpu_vram_mb(self) -> int:
        return sum(d.total_memory_mb for d in self.devices if d.device_type != DeviceType.CPU)

    @property
    def available_gpu_vram_mb(self) -> int:
        return sum(d.available_memory_mb for d in self.devices if d.device_type != DeviceType.CPU)

    @property
    def primary_device(self) -> Optional[HardwareDevice]:
        for d in self.devices:
            if d.is_primary:
                return d
        non_cpus = [d for d in self.devices if d.device_type != DeviceType.CPU]
        if non_cpus:
            return non_cpus[0]
        for d in self.devices:
            if d.device_type == DeviceType.CPU:
                return d
        return None

    @property
    def has_hardware_acceleration(self) -> bool:
        return any(d.device_type != DeviceType.CPU and d.is_healthy for d in self.devices)

    def to_dict(self) -> Dict[str, Any]:
        """Converts snapshot to serializable dictionary without secrets."""
        return {
            "timestamp": self.timestamp,
            "os_name": self.os_name,
            "os_release": self.os_release,
            "cpu": asdict(self.cpu),
            "memory": asdict(self.memory),
            "devices": [asdict(d) for d in self.devices],
            "storage": asdict(self.storage),
            "power": asdict(self.power),
            "environment_fingerprint": self.environment_fingerprint,
            "total_gpu_vram_mb": self.total_gpu_vram_mb,
            "available_gpu_vram_mb": self.available_gpu_vram_mb,
            "has_hardware_acceleration": self.has_hardware_acceleration
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
