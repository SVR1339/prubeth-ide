"""
PRUBETH IDE — Universal Hardware Auto-Tuning Engine
Pillar 6 & Pillar 7: Quality Engineering & Operations Governance

Automatically profiles host hardware (CPU, RAM, GPU, Battery, OS) across any PC,
laptop, or workstation, and synthesizes optimal runtime configurations (VRAM offloading,
thread concurrency, cache budgets, and model size tiers) for peak IDE performance.
"""

from __future__ import annotations

import os
import sys
import platform
import subprocess
import shutil
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class HardwareProfile:
    """Detected hardware capabilities of the host machine."""
    os_name: str
    os_release: str
    architecture: str
    cpu_cores: int
    cpu_threads: int
    cpu_model: str
    ram_total_mb: int
    ram_available_mb: int
    is_on_battery: bool
    has_nvidia_gpu: bool
    gpu_name: str
    vram_total_mb: int
    vram_free_mb: int
    tier_name: str  # ULTRA_LOW, BALANCED_LAPTOP, HIGH_PERFORMANCE, WORKSTATION_PRO
    devices_count: int = 1
    has_hardware_acceleration: bool = False
    snapshot: Optional[Any] = None
    scaling_profile: Optional[Any] = None


@dataclass
class TuningResult:
    """Recommended performance settings synthesized by the autotuner."""
    profile: HardwareProfile
    suggested_tier: str
    settings_delta: Dict[str, Any]
    diagnostic_summary: str
    scaling_profile: Optional[Any] = None


class HardwareAutoTuner:
    """Cross-platform hardware discovery and autonomous performance tuning engine."""

    @classmethod
    def get_capability_manager(cls):
        from core.hardware.detection import HardwareCapabilityManager
        return HardwareCapabilityManager.get_instance()

    @classmethod
    def get_scaling_engine(cls):
        from core.hardware.performance_tiers import DynamicPerformanceTierEngine
        return DynamicPerformanceTierEngine

    @classmethod
    def get_budget_manager(cls):
        from core.hardware.resource_budget import ResourceBudgetManager
        return ResourceBudgetManager()

    @classmethod
    def get_acceleration_registry(cls):
        from core.hardware.acceleration_adapters import AccelerationRegistry
        return AccelerationRegistry()

    @classmethod
    def get_multi_gpu_router(cls):
        from core.hardware.multi_gpu import MultiGPURuntimeRouter
        return MultiGPURuntimeRouter()

    @classmethod
    def get_model_capacity_evaluator(cls):
        from core.hardware.model_expansion import DynamicModelCapacityEvaluator
        return DynamicModelCapacityEvaluator

    @classmethod
    def get_persistence_manager(cls):
        from core.hardware.persistence import HardwarePersistenceManager
        return HardwarePersistenceManager()

    @classmethod
    def detect_hardware(cls) -> HardwareProfile:
        """Inspects host machine resources using native OS APIs without external dependencies."""
        os_name = platform.system()
        os_release = platform.release()
        arch = platform.machine()
        
        cpu_cores = os.cpu_count() or 4
        cpu_threads = cpu_cores
        cpu_model = platform.processor() or "Generic CPU"
        
        ram_total_mb, ram_avail_mb = cls._get_ram_info()
        is_on_battery = cls._get_battery_status()
        has_nvidia, gpu_name, vram_total_mb, vram_free_mb = cls._get_gpu_info()

        # Determine Tier
        if ram_total_mb < 7500 or (not has_nvidia and cpu_threads <= 4):
            tier = "ULTRA_LOW"
        elif ram_total_mb < 15500 or is_on_battery or (has_nvidia and vram_total_mb <= 3000):
            tier = "BALANCED_LAPTOP"
        elif ram_total_mb < 32000 or (has_nvidia and vram_total_mb <= 12000):
            tier = "HIGH_PERFORMANCE"
        else:
            tier = "WORKSTATION_PRO"

        snapshot = None
        scaling_prof = None
        dev_count = 1
        try:
            from core.hardware.detection import HardwareCapabilityManager
            from core.hardware.performance_tiers import DynamicPerformanceTierEngine
            snapshot = HardwareCapabilityManager.get_instance().get_current_snapshot()
            scaling_prof = DynamicPerformanceTierEngine.evaluate_hardware(snapshot)
            dev_count = len(snapshot.devices)
        except Exception:
            pass

        return HardwareProfile(
            os_name=os_name,
            os_release=os_release,
            architecture=arch,
            cpu_cores=max(1, cpu_cores // 2) if cpu_cores > 1 else 1,
            cpu_threads=cpu_threads,
            cpu_model=cpu_model,
            ram_total_mb=ram_total_mb,
            ram_available_mb=ram_avail_mb,
            is_on_battery=is_on_battery,
            has_nvidia_gpu=has_nvidia,
            gpu_name=gpu_name,
            vram_total_mb=vram_total_mb,
            vram_free_mb=vram_free_mb,
            tier_name=tier,
            devices_count=dev_count,
            has_hardware_acceleration=has_nvidia or (snapshot is not None and snapshot.has_hardware_acceleration),
            snapshot=snapshot,
            scaling_profile=scaling_prof
        )


    @classmethod
    def synthesize_tuning(cls, target_model: str = "qwen2.5:1.5b") -> TuningResult:
        """Generates exact settings delta and performance parameters tailored for the host machine."""
        hw = cls.detect_hardware()
        delta: Dict[str, Any] = {}

        if hw.tier_name == "ULTRA_LOW":
            delta["max_parallel_agents"] = 1
            delta["max_task_steps"] = 25
            delta["background_workers"] = 1
            delta["cache_mb"] = 256
            delta["index_max_file_mb"] = 1
            delta["max_indexed_files"] = 15000
            delta["low_memory_mode"] = True
            delta["gpu_policy"] = "CPU only"
            delta["gguf_gpu_layers"] = 0
            delta["cuda_vram_limit_mb"] = 0
            delta["recommended_model"] = "qwen2.5:1.5b"
            desc = "Optimized for constrained devices / 4-8GB RAM. Low memory mode active, 1 agent worker."

        elif hw.tier_name == "BALANCED_LAPTOP":
            delta["max_parallel_agents"] = 2
            delta["max_task_steps"] = 35
            delta["background_workers"] = 2
            delta["cache_mb"] = 512
            delta["index_max_file_mb"] = 2
            delta["max_indexed_files"] = 40000
            delta["low_memory_mode"] = False
            delta["pause_indexing_on_battery"] = True
            if hw.has_nvidia_gpu and hw.vram_total_mb >= 3000:
                delta["gpu_policy"] = "Prefer GPU"
                delta["cuda_vram_limit_mb"] = max(2048, hw.vram_total_mb - 512)
                delta["gguf_gpu_layers"] = 24
            else:
                delta["gpu_policy"] = "Automatic"
                delta["gguf_gpu_layers"] = 0
                delta["cuda_vram_limit_mb"] = 0
            delta["recommended_model"] = "qwen2.5:1.5b" if hw.is_on_battery else "qwen2.5:7b"
            desc = "Balanced profile for mobile laptops / 8-16GB RAM. Battery-aware indexing enabled."

        elif hw.tier_name == "HIGH_PERFORMANCE":
            delta["max_parallel_agents"] = 4
            delta["max_task_steps"] = 50
            delta["background_workers"] = max(2, min(hw.cpu_threads // 2, 6))
            delta["cache_mb"] = 2048
            delta["index_max_file_mb"] = 5
            delta["max_indexed_files"] = 100000
            delta["low_memory_mode"] = False
            delta["pause_indexing_on_battery"] = False
            delta["gpu_policy"] = "Prefer GPU"
            
            # NVIDIA VRAM Layer Tuning (e.g., GTX 1050 Ti 4GB or RTX 6-8GB)
            usable_vram = max(2048, hw.vram_total_mb - 512)
            delta["cuda_vram_limit_mb"] = usable_vram
            if hw.vram_total_mb <= 4500:
                # 4GB GDDR5 (e.g. GTX 1050 Ti)
                delta["gguf_gpu_layers"] = 33
                delta["recommended_model"] = "redsage-8b:latest"
            elif hw.vram_total_mb <= 8500:
                # 6GB - 8GB GPU
                delta["gguf_gpu_layers"] = 42
                delta["recommended_model"] = "qwen2.5-coder:7b"
            else:
                delta["gguf_gpu_layers"] = 60
                delta["recommended_model"] = "deepseek-coder:14b"
            desc = f"High performance profile tuned for {hw.gpu_name} ({hw.vram_total_mb}MB VRAM). Offloading {delta['gguf_gpu_layers']} layers."

        else:  # WORKSTATION_PRO
            delta["max_parallel_agents"] = 8
            delta["max_task_steps"] = 100
            delta["background_workers"] = max(4, min(hw.cpu_threads, 12))
            delta["cache_mb"] = 8192
            delta["index_max_file_mb"] = 10
            delta["max_indexed_files"] = 250000
            delta["low_memory_mode"] = False
            delta["gpu_policy"] = "GPU required"
            delta["cuda_vram_limit_mb"] = max(8192, hw.vram_total_mb - 1024)
            delta["gguf_gpu_layers"] = 99
            delta["recommended_model"] = "qwen2.5-coder:32b"
            desc = f"Workstation Pro tier with {hw.ram_total_mb}MB RAM and high-end compute."

        return TuningResult(
            profile=hw,
            suggested_tier=hw.tier_name,
            settings_delta=delta,
            diagnostic_summary=desc,
            scaling_profile=hw.scaling_profile
        )

    @classmethod
    def apply_to_settings(cls, target_settings: Dict[str, Any], result: TuningResult) -> Dict[str, Any]:
        """Applies tuning results seamlessly to both flat and nested settings structures."""
        d = result.settings_delta

        # If settings is nested prubeth_settings style
        if "performance" in target_settings and isinstance(target_settings["performance"], dict):
            p = target_settings["performance"]
            p["background_workers"] = d.get("background_workers", p.get("background_workers", 2))
            p["cache_mb"] = d.get("cache_mb", p.get("cache_mb", 512))
            p["gpu_policy"] = d.get("gpu_policy", p.get("gpu_policy", "Automatic"))
            p["low_memory_mode"] = d.get("low_memory_mode", False)
            p["cuda_vram_limit_mb"] = d.get("cuda_vram_limit_mb", 0)
            p["gguf_gpu_layers"] = d.get("gguf_gpu_layers", 0)

        if "agents" in target_settings and isinstance(target_settings["agents"], dict):
            a = target_settings["agents"]
            a["max_parallel_agents"] = d.get("max_parallel_agents", a.get("max_parallel_agents", 2))
            a["max_task_steps"] = d.get("max_task_steps", a.get("max_task_steps", 30))

        # Also populate flat keys for backward compatibility with local_ai_studio_pro.py
        target_settings["cuda_vram_limit_mb"] = d.get("cuda_vram_limit_mb", 0)
        target_settings["gguf_gpu_layers"] = d.get("gguf_gpu_layers", 0)
        target_settings["max_agent_steps"] = d.get("max_task_steps", 30)
        target_settings["background_workers"] = d.get("background_workers", 2)
        target_settings["cache_mb"] = d.get("cache_mb", 512)
        target_settings["low_memory_mode"] = d.get("low_memory_mode", False)
        if "recommended_model" in d and not target_settings.get("local_model"):
            target_settings["local_model"] = d["recommended_model"]

        target_settings["hardware_tier"] = result.suggested_tier
        return target_settings

    @classmethod
    def _get_ram_info(cls) -> tuple[int, int]:
        """Returns (total_mb, available_mb) using Windows ctypes kernel32 or fallback."""
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", wintypes.DWORD),
                        ("dwMemoryLoad", wintypes.DWORD),
                        ("ullTotalPhys", ctypes.c_uint64),
                        ("ullAvailPhys", ctypes.c_uint64),
                        ("ullTotalPageFile", ctypes.c_uint64),
                        ("ullAvailPageFile", ctypes.c_uint64),
                        ("ullTotalVirtual", ctypes.c_uint64),
                        ("ullAvailVirtual", ctypes.c_uint64),
                        ("sullAvailExtendedVirtual", ctypes.c_uint64),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    total_mb = int(stat.ullTotalPhys / (1024 * 1024))
                    avail_mb = int(stat.ullAvailPhys / (1024 * 1024))
                    return total_mb, avail_mb
            except Exception:
                pass
        return 16384, 8192  # Safe fallback 16GB total / 8GB free

    @classmethod
    def _get_battery_status(cls) -> bool:
        """Returns True if running on battery power on a portable laptop."""
        if sys.platform == "win32":
            try:
                import ctypes
                class SYSTEM_POWER_STATUS(ctypes.Structure):
                    _fields_ = [
                        ("ACLineStatus", ctypes.c_byte),
                        ("BatteryFlag", ctypes.c_byte),
                        ("BatteryLifePercent", ctypes.c_byte),
                        ("SystemStatusFlag", ctypes.c_byte),
                        ("BatteryLifeTime", ctypes.c_ulong),
                        ("BatteryFullLifeTime", ctypes.c_ulong),
                    ]
                status = SYSTEM_POWER_STATUS()
                if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                    # ACLineStatus == 0 means battery (offline)
                    return status.ACLineStatus == 0
            except Exception:
                pass
        return False

    @classmethod
    def _get_gpu_info(cls) -> tuple[bool, str, int, int]:
        """Probes for NVIDIA CUDA or generic GPU, returns (has_nvidia, name, total_mb, free_mb)."""
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            try:
                cmd = [
                    nvidia_smi,
                    "--query-gpu=name,memory.total,memory.free",
                    "--format=csv,noheader,nounits"
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if proc.returncode == 0 and proc.stdout.strip():
                    line = proc.stdout.strip().split("\n")[0]
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        name = parts[0]
                        total_mb = int(float(parts[1]))
                        free_mb = int(float(parts[2]))
                        return True, name, total_mb, free_mb
            except Exception:
                pass

        # Check torch/cuda if installed
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                total_mb = int(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024))
                return True, name, total_mb, total_mb // 2
        except Exception:
            pass

        return False, "Integrated Graphics / Standard CPU", 0, 0
