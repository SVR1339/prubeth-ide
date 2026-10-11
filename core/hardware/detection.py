"""
PRUBETH IDE — Dynamic Hardware Discovery & Telemetry Engine
Part of the Indefinite Hardware Upgradability & Progressive Performance Scaling Engine.

Probes multi-device topologies (Multi-GPU NVIDIA, AMD ROCm, DirectML, Intel Arc/OpenVINO,
Apple Silicon, CPU SIMD extensions) without hardcoded vendor limits or rigid ceilings.
Distinguishes physical hardware from process-usable compute capacity.
"""

from __future__ import annotations

import os
import sys
import shutil
import platform
import subprocess
import hashlib
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

from core.hardware.capabilities import (
    DeviceType,
    HardwareDevice,
    CPUCapability,
    MemoryCapability,
    StorageCapability,
    PowerCapability,
    HardwareSnapshot
)


class HardwareCapabilityManager:
    """
    Central discovery and telemetry engine for host computing resources.
    Discovers multi-GPU configurations, vector extensions, and memory headroom.
    Supports on-demand, scheduled, and pre-workload refresh hooks.
    """

    _instance: Optional[HardwareCapabilityManager] = None
    _lock = threading.Lock()

    def __init__(self, cache_ttl_seconds: float = 10.0):
        self._cache_ttl = cache_ttl_seconds
        self._last_snapshot: Optional[HardwareSnapshot] = None
        self._last_refresh_time: float = 0.0
        self._change_listeners: List[Callable[[HardwareSnapshot, HardwareSnapshot], None]] = []
        self._internal_lock = threading.RLock()
        
        # Initial discovery
        self.refresh_inventory(force=True)

    @classmethod
    def get_instance(cls) -> HardwareCapabilityManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = HardwareCapabilityManager()
            return cls._instance

    def register_change_listener(self, callback: Callable[[HardwareSnapshot, HardwareSnapshot], None]) -> None:
        """Registers a callback invoked whenever a hardware configuration or capacity shift is detected."""
        with self._internal_lock:
            if callback not in self._change_listeners:
                self._change_listeners.append(callback)

    def unregister_change_listener(self, callback: Callable[[HardwareSnapshot, HardwareSnapshot], None]) -> None:
        with self._internal_lock:
            if callback in self._change_listeners:
                self._change_listeners.remove(callback)

    def get_current_snapshot(self) -> HardwareSnapshot:
        """Returns the active hardware snapshot, refreshing if cache TTL has expired."""
        with self._internal_lock:
            now = time.time()
            if self._last_snapshot is None or (now - self._last_refresh_time) > self._cache_ttl:
                return self.refresh_inventory(force=False)
            return self._last_snapshot

    def refresh_inventory(self, force: bool = False) -> HardwareSnapshot:
        """
        Actively probes the operating system, device drivers, and runtime libraries.
        Triggers change listeners if the hardware configuration or tier changes.
        """
        with self._internal_lock:
            now = time.time()
            if not force and self._last_snapshot is not None and (now - self._last_refresh_time) < self._cache_ttl:
                return self._last_snapshot

            old_snapshot = self._last_snapshot

            os_name = platform.system()
            os_release = platform.release()

            # Probe components safely
            cpu = self._probe_cpu()
            memory = self._probe_memory()
            devices = self._probe_accelerator_devices(memory.is_unified_memory)
            storage = self._probe_storage()
            power = self._probe_power()

            # Generate environment fingerprint for change detection
            fingerprint = self._calculate_fingerprint(cpu, memory, devices)

            new_snapshot = HardwareSnapshot(
                timestamp=now,
                os_name=os_name,
                os_release=os_release,
                cpu=cpu,
                memory=memory,
                devices=devices,
                storage=storage,
                power=power,
                environment_fingerprint=fingerprint
            )

            self._last_snapshot = new_snapshot
            self._last_refresh_time = now

            # Detect hardware change and dispatch to listeners
            if old_snapshot is not None and old_snapshot.environment_fingerprint != fingerprint:
                self._notify_listeners(old_snapshot, new_snapshot)

            return new_snapshot

    def _notify_listeners(self, old: HardwareSnapshot, new: HardwareSnapshot) -> None:
        listeners = list(self._change_listeners)
        for listener in listeners:
            try:
                listener(old, new)
            except Exception:
                pass

    def _calculate_fingerprint(self, cpu: CPUCapability, mem: MemoryCapability, devices: List[HardwareDevice]) -> str:
        dev_sig = ",".join(f"{d.device_id}:{d.name}:{d.total_memory_mb}" for d in devices)
        raw = f"{cpu.model_name}:{cpu.logical_threads}:{mem.total_ram_mb}:{dev_sig}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    # ------------------------------------------------------------------
    # CPU Discovery
    # ------------------------------------------------------------------
    def _probe_cpu(self) -> CPUCapability:
        logical_threads = os.cpu_count() or 4
        physical_cores = max(1, logical_threads // 2) if logical_threads > 1 else 1
        arch = platform.machine().lower()
        model_name = platform.processor() or "Generic CPU"

        simd_extensions: List[str] = []
        supports_avx2 = False
        supports_avx512 = False
        supports_amx = False
        supports_neon = False

        if "arm" in arch or "aarch64" in arch:
            simd_extensions.append("NEON")
            supports_neon = True
        else:
            # x86 vector detection
            simd_extensions.append("SSE4_2")
            # Probe Windows registry or Linux /proc/cpuinfo or macOS sysctl
            simd_detected = self._detect_x86_simd()
            simd_extensions.extend(simd_detected)
            supports_avx2 = "AVX2" in simd_extensions
            supports_avx512 = any("AVX512" in s for s in simd_extensions)
            supports_amx = any("AMX" in s for s in simd_extensions)

        return CPUCapability(
            physical_cores=physical_cores,
            logical_threads=logical_threads,
            architecture=arch,
            model_name=model_name,
            simd_extensions=list(set(simd_extensions)),
            supports_avx2=supports_avx2,
            supports_avx512=supports_avx512,
            supports_amx=supports_amx,
            supports_arm_neon=supports_neon
        )

    def _detect_x86_simd(self) -> List[str]:
        found: List[str] = []
        if sys.platform == "win32":
            # On Windows, try IsProcessorFeaturePresent or assume AVX2 on modern 64-bit systems
            try:
                import ctypes
                # PF_AVX2_INSTRUCTIONS_AVAILABLE = 40
                if ctypes.windll.kernel32.IsProcessorFeaturePresent(40):
                    found.append("AVX2")
                # PF_AVX512F_INSTRUCTIONS_AVAILABLE = 49
                if ctypes.windll.kernel32.IsProcessorFeaturePresent(49):
                    found.append("AVX512F")
            except Exception:
                found.append("AVX2")
        elif sys.platform == "linux":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    content = f.read().lower()
                    if "avx2" in content:
                        found.append("AVX2")
                    if "avx512" in content:
                        found.append("AVX512F")
                    if "amx" in content:
                        found.append("AMX")
            except Exception:
                pass
        elif sys.platform == "darwin":
            try:
                out = subprocess.check_output(["sysctl", "-n", "machdep.cpu.features"], text=True).lower()
                if "avx2" in out:
                    found.append("AVX2")
            except Exception:
                pass
        return found

    # ------------------------------------------------------------------
    # Memory Discovery
    # ------------------------------------------------------------------
    def _probe_memory(self) -> MemoryCapability:
        total_ram = 16384
        avail_ram = 8192
        swap_total = 8192
        swap_free = 6144
        is_unified = False

        # Check Apple Silicon unified memory
        if sys.platform == "darwin" and ("arm" in platform.machine().lower()):
            is_unified = True

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
                    total_ram = int(stat.ullTotalPhys / (1024 * 1024))
                    avail_ram = int(stat.ullAvailPhys / (1024 * 1024))
                    swap_total = int(stat.ullTotalPageFile / (1024 * 1024))
                    swap_free = int(stat.ullAvailPageFile / (1024 * 1024))
            except Exception:
                pass
        elif sys.platform == "linux":
            try:
                with open("/proc/meminfo", "r") as f:
                    info = {}
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip().split()[0]
                            info[key] = int(val) // 1024
                    total_ram = info.get("MemTotal", total_ram)
                    avail_ram = info.get("MemAvailable", info.get("MemFree", avail_ram))
                    swap_total = info.get("SwapTotal", swap_total)
                    swap_free = info.get("SwapFree", swap_free)
            except Exception:
                pass

        # Estimate process RSS
        process_rss = 256
        try:
            import psutil
            process_rss = int(psutil.Process().memory_info().rss / (1024 * 1024))
        except Exception:
            pass

        return MemoryCapability(
            total_ram_mb=total_ram,
            available_ram_mb=avail_ram,
            process_rss_mb=process_rss,
            swap_total_mb=swap_total,
            swap_free_mb=swap_free,
            is_unified_memory=is_unified
        )

    # ------------------------------------------------------------------
    # Accelerator & Multi-GPU Discovery
    # ------------------------------------------------------------------
    def _probe_accelerator_devices(self, is_unified_memory: bool = False) -> List[HardwareDevice]:
        devices: List[HardwareDevice] = []

        # 1. Primary CPU pseudo-device
        cpu_threads = os.cpu_count() or 4
        devices.append(HardwareDevice(
            device_id="cpu",
            name=f"Host CPU Execution Engine ({cpu_threads} Threads)",
            device_type=DeviceType.CPU,
            vendor="Host System",
            is_primary=False,
            is_healthy=True,
            supported_quantizations=["fp32", "fp16", "int8", "int4"]
        ))

        # 2. Multi-GPU Discovery via nvidia-smi (captures all GPUs independently)
        nvidia_devices = self._probe_nvidia_smi()
        if nvidia_devices:
            devices.extend(nvidia_devices)

        # 3. DirectML / AMD ROCm / PyTorch fallback if nvidia-smi wasn't available
        if not nvidia_devices:
            torch_devices = self._probe_torch_devices()
            if torch_devices:
                devices.extend(torch_devices)

        # 4. Apple Silicon Metal Accelerator (if on Darwin ARM)
        if sys.platform == "darwin" and is_unified_memory:
            devices.append(HardwareDevice(
                device_id="metal:0",
                name="Apple Silicon Metal Performance Engine",
                device_type=DeviceType.APPLE_SILICON,
                vendor="Apple",
                is_primary=True,
                is_healthy=True,
                supported_quantizations=["fp32", "fp16", "int8", "int4", "fp8"]
            ))

        # 5. Generic Windows Video Controller fallback if no other GPU discovered
        if len(devices) == 1 and sys.platform == "win32":
            wmi_device = self._probe_windows_display_adapter()
            if wmi_device:
                devices.append(wmi_device)

        # Mark first GPU as primary if available
        first_gpu = next((d for d in devices if d.device_type != DeviceType.CPU), None)
        if first_gpu:
            first_gpu.is_primary = True
        else:
            devices[0].is_primary = True

        return devices

    def _probe_nvidia_smi(self) -> List[HardwareDevice]:
        """Probes all installed NVIDIA GPUs independently via nvidia-smi query."""
        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            return []

        devices: List[HardwareDevice] = []
        try:
            cmd = [
                nvidia_smi,
                "--query-gpu=index,name,memory.total,memory.free,driver_version,compute_cap",
                "--format=csv,noheader,nounits"
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if proc.returncode == 0 and proc.stdout.strip():
                lines = proc.stdout.strip().split("\n")
                for line in lines:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 5:
                        idx = parts[0]
                        name = parts[1]
                        total_mb = int(float(parts[2]))
                        free_mb = int(float(parts[3]))
                        driver_ver = parts[4]
                        compute_cap = parts[5] if len(parts) > 5 else "Unknown"

                        # Determine quantizations based on compute capability (e.g. sm_89 supports FP8)
                        quants = ["fp32", "fp16", "int8", "int4"]
                        try:
                            cap_val = float(compute_cap)
                            if cap_val >= 8.9:
                                quants.extend(["fp8", "fp4"])
                            elif cap_val >= 8.0:
                                quants.append("bf16")
                        except Exception:
                            pass

                        devices.append(HardwareDevice(
                            device_id=f"cuda:{idx}",
                            name=name,
                            device_type=DeviceType.NVIDIA_CUDA,
                            vendor="NVIDIA",
                            driver_version=driver_ver,
                            runtime_version=compute_cap,
                            total_memory_mb=total_mb,
                            available_memory_mb=free_mb,
                            compute_capability=compute_cap,
                            supported_quantizations=quants,
                            is_healthy=True
                        ))
        except Exception:
            pass

        return devices

    def _probe_torch_devices(self) -> List[HardwareDevice]:
        """Checks PyTorch for CUDA, ROCm, or MPS devices."""
        devices: List[HardwareDevice] = []
        try:
            import torch
            if torch.cuda.is_available():
                count = torch.cuda.device_count()
                for i in range(count):
                    props = torch.cuda.get_device_properties(i)
                    total_mb = int(props.total_memory / (1024 * 1024))
                    # Available estimate
                    free_mb = total_mb
                    try:
                        free_bytes, total_bytes = torch.cuda.mem_get_info(i)
                        free_mb = int(free_bytes / (1024 * 1024))
                    except Exception:
                        free_mb = total_mb // 2

                    is_rocm = hasattr(torch.version, "hip") and torch.version.hip is not None
                    dev_type = DeviceType.AMD_ROCM if is_rocm else DeviceType.NVIDIA_CUDA
                    vendor = "AMD" if is_rocm else "NVIDIA"

                    devices.append(HardwareDevice(
                        device_id=f"cuda:{i}" if not is_rocm else f"rocm:{i}",
                        name=props.name,
                        device_type=dev_type,
                        vendor=vendor,
                        total_memory_mb=total_mb,
                        available_memory_mb=free_mb,
                        compute_capability=f"{props.major}.{props.minor}",
                        supported_quantizations=["fp32", "fp16", "int8", "int4"],
                        is_healthy=True
                    ))
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                devices.append(HardwareDevice(
                    device_id="mps:0",
                    name="Apple Silicon Metal Shaders (MPS)",
                    device_type=DeviceType.APPLE_SILICON,
                    vendor="Apple",
                    is_healthy=True,
                    supported_quantizations=["fp32", "fp16", "int8", "int4"]
                ))
        except Exception:
            pass

        return devices

    def _probe_windows_display_adapter(self) -> Optional[HardwareDevice]:
        """Queries Windows WMI / CIM for installed display adapters (DirectML / Integrated)."""
        try:
            cmd = ["powershell", "-NoProfile", "-Command",
                   "Get-CimInstance Win32_VideoController | Select-Object -First 1 Name, AdapterRAM | ConvertTo-Json"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if proc.returncode == 0 and proc.stdout.strip():
                import json
                data = json.loads(proc.stdout.strip())
                name = data.get("Name", "Generic Display Adapter")
                raw_ram = data.get("AdapterRAM", 0)
                ram_mb = int(raw_ram / (1024 * 1024)) if raw_ram and raw_ram > 0 else 1024

                return HardwareDevice(
                    device_id="directml:0",
                    name=name,
                    device_type=DeviceType.DIRECTML,
                    vendor="Microsoft DirectML",
                    total_memory_mb=ram_mb,
                    available_memory_mb=max(512, ram_mb - 256),
                    supported_quantizations=["fp32", "fp16", "int8"],
                    is_healthy=True
                )
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Storage & Power Discovery
    # ------------------------------------------------------------------
    def _probe_storage(self) -> StorageCapability:
        ws_free_mb = 50000
        models_free_mb = 50000
        try:
            ws_path = Path.cwd()
            stat = shutil.disk_usage(ws_path)
            ws_free_mb = int(stat.free / (1024 * 1024))

            home_stat = shutil.disk_usage(Path.home())
            models_free_mb = int(home_stat.free / (1024 * 1024))
        except Exception:
            pass

        return StorageCapability(
            workspace_free_mb=ws_free_mb,
            models_cache_free_mb=models_free_mb,
            storage_type="SSD",
            is_fast_storage=True
        )

    def _probe_power(self) -> PowerCapability:
        is_battery = False
        percent = None
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
                    is_battery = (status.ACLineStatus == 0)
                    if 0 <= status.BatteryLifePercent <= 100:
                        percent = int(status.BatteryLifePercent)
            except Exception:
                pass

        return PowerCapability(
            is_on_battery=is_battery,
            battery_life_percent=percent,
            is_power_saver_active=is_battery and (percent is not None and percent < 25)
        )
