"""
PRUBETH IDE — Pluggable Hardware Acceleration Adapters
Part of the Indefinite Hardware Upgradability & Progressive Performance Scaling Engine.

Provides modular, replaceable acceleration adapters for NVIDIA CUDA, AMD ROCm/DirectML,
Intel OpenVINO/oneAPI, Apple Silicon Metal, and optimized CPU SIMD execution engines.
Includes transparent fallback chains with diagnostic logging.
"""

from __future__ import annotations

import os
import sys
import abc
import shutil
import platform
import subprocess
from typing import Dict, Any, List, Optional, Tuple

from core.hardware.capabilities import DeviceType, HardwareDevice


class HardwareAccelerationAdapter(abc.ABC):
    """Abstract contract for hardware inference and execution acceleration backends."""

    @property
    @abc.abstractmethod
    def backend_name(self) -> str:
        """Unique identifier of the acceleration backend (e.g. 'cuda', 'rocm', 'cpu')."""
        pass

    @property
    @abc.abstractmethod
    def device_type(self) -> DeviceType:
        """Underlying compute device classification."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Determines whether drivers, libraries, and hardware for this backend are functional."""
        pass

    @abc.abstractmethod
    def probe_devices(self) -> List[HardwareDevice]:
        """Discovers devices managed by this acceleration adapter."""
        pass

    @abc.abstractmethod
    def verify_compatibility(
        self,
        model_format: str,
        required_vram_mb: int,
        quantization: str = "fp16"
    ) -> Tuple[bool, str]:
        """
        Validates whether this adapter can execute a model with specified parameters.
        Returns (is_compatible, diagnostic_reason).
        """
        pass

    @abc.abstractmethod
    def allocate_context(self, device_id: str, memory_mb: int) -> bool:
        """Attempts to reserve memory budget on the target device."""
        pass

    @abc.abstractmethod
    def release_context(self, device_id: str, memory_mb: int) -> None:
        """Releases reserved memory budget on the target device."""
        pass

    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns runtime diagnostic metrics for telemetry and user inspection."""
        return {
            "backend": self.backend_name,
            "device_type": self.device_type.value,
            "available": self.is_available()
        }


# =====================================================================
# 1. CPU Acceleration Adapter (AVX2, AVX-512, AMX, ARM NEON)
# =====================================================================
class CPUAccelerationAdapter(HardwareAccelerationAdapter):
    """Universal fallback CPU execution adapter with SIMD vector optimization."""

    def __init__(self):
        self._allocated_mb: Dict[str, int] = {"cpu": 0}

    @property
    def backend_name(self) -> str:
        return "cpu"

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.CPU

    def is_available(self) -> bool:
        return True  # Host CPU is always available

    def probe_devices(self) -> List[HardwareDevice]:
        threads = os.cpu_count() or 4
        return [
            HardwareDevice(
                device_id="cpu",
                name=f"Host CPU SIMD Vector Engine ({threads} Threads)",
                device_type=DeviceType.CPU,
                vendor="Host System",
                driver_version="Native OS",
                is_primary=True,
                is_healthy=True,
                supported_quantizations=["fp32", "fp16", "int8", "int4"]
            )
        ]

    def verify_compatibility(
        self,
        model_format: str,
        required_vram_mb: int,
        quantization: str = "fp16"
    ) -> Tuple[bool, str]:
        # CPU can run GGUF, ONNX, and PyTorch CPU models; very large models may be slow but compatible
        fmt = model_format.lower()
        if fmt in ("gguf", "onnx", "safetensors", "torch", "bin"):
            return True, "Compatible with CPU execution engine (utilizes system RAM)."
        return True, "Compatible with CPU universal fallback."

    def allocate_context(self, device_id: str, memory_mb: int) -> bool:
        self._allocated_mb["cpu"] = self._allocated_mb.get("cpu", 0) + memory_mb
        return True

    def release_context(self, device_id: str, memory_mb: int) -> None:
        self._allocated_mb["cpu"] = max(0, self._allocated_mb.get("cpu", 0) - memory_mb)


# =====================================================================
# 2. NVIDIA CUDA Acceleration Adapter
# =====================================================================
class NvidiaCudaAdapter(HardwareAccelerationAdapter):
    """High-performance NVIDIA CUDA & Tensor Core acceleration adapter."""

    def __init__(self):
        self._allocated_mb: Dict[str, int] = {}

    @property
    def backend_name(self) -> str:
        return "cuda"

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.NVIDIA_CUDA

    def is_available(self) -> bool:
        if shutil.which("nvidia-smi") is not None:
            return True
        try:
            import torch
            return bool(torch.cuda.is_available())
        except Exception:
            return False

    def probe_devices(self) -> List[HardwareDevice]:
        devices: List[HardwareDevice] = []
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            try:
                cmd = [
                    nvidia_smi,
                    "--query-gpu=index,name,memory.total,memory.free,driver_version,compute_cap",
                    "--format=csv,noheader,nounits"
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if proc.returncode == 0 and proc.stdout.strip():
                    for line in proc.stdout.strip().split("\n"):
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 5:
                            idx = parts[0]
                            name = parts[1]
                            total_mb = int(float(parts[2]))
                            free_mb = int(float(parts[3]))
                            driver_ver = parts[4]
                            comp_cap = parts[5] if len(parts) > 5 else "7.5"
                            devices.append(HardwareDevice(
                                device_id=f"cuda:{idx}",
                                name=name,
                                device_type=DeviceType.NVIDIA_CUDA,
                                vendor="NVIDIA",
                                driver_version=driver_ver,
                                runtime_version=comp_cap,
                                total_memory_mb=total_mb,
                                available_memory_mb=free_mb,
                                compute_capability=comp_cap,
                                supported_quantizations=["fp32", "fp16", "bf16", "int8", "int4", "fp8"],
                                is_healthy=True
                            ))
            except Exception:
                pass
        return devices

    def verify_compatibility(
        self,
        model_format: str,
        required_vram_mb: int,
        quantization: str = "fp16"
    ) -> Tuple[bool, str]:
        if not self.is_available():
            return False, "NVIDIA CUDA runtime or driver not found."
        
        devices = self.probe_devices()
        if not devices:
            return False, "No active NVIDIA CUDA devices discovered."

        # Check if at least one device can accommodate the required VRAM
        max_free_vram = max((d.available_memory_mb for d in devices), default=0)
        # Leave 512MB margin for OS window manager
        safe_headroom = max(0, max_free_vram - 512)
        if required_vram_mb > safe_headroom and required_vram_mb > 0:
            return False, (
                f"Insufficient VRAM on CUDA devices: required {required_vram_mb}MB, "
                f"usable headroom is {safe_headroom}MB (Total free: {max_free_vram}MB)."
            )

        return True, f"Fully compatible with NVIDIA CUDA ({len(devices)} device(s) ready)."

    def allocate_context(self, device_id: str, memory_mb: int) -> bool:
        self._allocated_mb[device_id] = self._allocated_mb.get(device_id, 0) + memory_mb
        return True

    def release_context(self, device_id: str, memory_mb: int) -> None:
        self._allocated_mb[device_id] = max(0, self._allocated_mb.get(device_id, 0) - memory_mb)


# =====================================================================
# 3. AMD ROCm & Microsoft DirectML Adapter
# =====================================================================
class AmdRocmDirectMLAdapter(HardwareAccelerationAdapter):
    """AMD ROCm HIP and Windows DirectML cross-vendor GPU acceleration adapter."""

    def __init__(self):
        self._allocated_mb: Dict[str, int] = {}

    @property
    def backend_name(self) -> str:
        return "directml"

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.DIRECTML

    def is_available(self) -> bool:
        # Check DirectML on Windows or ROCm on Linux
        if sys.platform == "win32":
            return True  # DirectML is supported on modern Windows 10/11
        return shutil.which("rocm-smi") is not None

    def probe_devices(self) -> List[HardwareDevice]:
        devices: List[HardwareDevice] = []
        if sys.platform == "win32":
            devices.append(HardwareDevice(
                device_id="directml:0",
                name="DirectX 12 / DirectML Hardware Accelerator",
                device_type=DeviceType.DIRECTML,
                vendor="DirectML",
                is_healthy=True,
                supported_quantizations=["fp32", "fp16", "int8"]
            ))
        elif shutil.which("rocm-smi"):
            devices.append(HardwareDevice(
                device_id="rocm:0",
                name="AMD ROCm Radeon Accelerator",
                device_type=DeviceType.AMD_ROCM,
                vendor="AMD",
                is_healthy=True,
                supported_quantizations=["fp32", "fp16", "int8", "int4"]
            ))
        return devices

    def verify_compatibility(
        self,
        model_format: str,
        required_vram_mb: int,
        quantization: str = "fp16"
    ) -> Tuple[bool, str]:
        if not self.is_available():
            return False, "Neither AMD ROCm nor DirectML runtime available."
        fmt = model_format.lower()
        if fmt in ("onnx", "gguf", "safetensors", "torch"):
            return True, "Compatible with DirectML/ROCm GPU acceleration."
        return True, "DirectML runtime available."

    def allocate_context(self, device_id: str, memory_mb: int) -> bool:
        self._allocated_mb[device_id] = self._allocated_mb.get(device_id, 0) + memory_mb
        return True

    def release_context(self, device_id: str, memory_mb: int) -> None:
        self._allocated_mb[device_id] = max(0, self._allocated_mb.get(device_id, 0) - memory_mb)


# =====================================================================
# 4. Intel OpenVINO & oneAPI Adapter
# =====================================================================
class IntelAcceleratorAdapter(HardwareAccelerationAdapter):
    """Intel OpenVINO & Arc Graphics / NPU acceleration adapter."""

    def __init__(self):
        self._allocated_mb: Dict[str, int] = {}

    @property
    def backend_name(self) -> str:
        return "openvino"

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.INTEL_ACCEL

    def is_available(self) -> bool:
        try:
            import openvino
            return True
        except ImportError:
            return False

    def probe_devices(self) -> List[HardwareDevice]:
        devices: List[HardwareDevice] = []
        try:
            import openvino as ov
            core = ov.Core()
            for dev_str in core.available_devices:
                dev_name = core.get_property(dev_str, "FULL_DEVICE_NAME")
                devices.append(HardwareDevice(
                    device_id=f"intel:{dev_str.lower()}",
                    name=str(dev_name),
                    device_type=DeviceType.INTEL_ACCEL,
                    vendor="Intel",
                    is_healthy=True,
                    supported_quantizations=["fp32", "fp16", "int8", "int4"]
                ))
        except Exception:
            pass
        return devices

    def verify_compatibility(
        self,
        model_format: str,
        required_vram_mb: int,
        quantization: str = "fp16"
    ) -> Tuple[bool, str]:
        if not self.is_available():
            return False, "Intel OpenVINO runtime not installed in active environment."
        return True, "Compatible with Intel OpenVINO runtime."

    def allocate_context(self, device_id: str, memory_mb: int) -> bool:
        self._allocated_mb[device_id] = self._allocated_mb.get(device_id, 0) + memory_mb
        return True

    def release_context(self, device_id: str, memory_mb: int) -> None:
        self._allocated_mb[device_id] = max(0, self._allocated_mb.get(device_id, 0) - memory_mb)


# =====================================================================
# 5. Apple Silicon Metal Performance Shaders (MPS) Adapter
# =====================================================================
class AppleSiliconAdapter(HardwareAccelerationAdapter):
    """Apple Silicon Unified Memory & Metal GPU / Neural Engine acceleration adapter."""

    def __init__(self):
        self._allocated_mb: Dict[str, int] = {}

    @property
    def backend_name(self) -> str:
        return "metal"

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.APPLE_SILICON

    def is_available(self) -> bool:
        return sys.platform == "darwin" and ("arm" in platform.machine().lower())

    def probe_devices(self) -> List[HardwareDevice]:
        if not self.is_available():
            return []
        return [
            HardwareDevice(
                device_id="metal:0",
                name="Apple Silicon Metal Performance Engine",
                device_type=DeviceType.APPLE_SILICON,
                vendor="Apple",
                is_primary=True,
                is_healthy=True,
                supported_quantizations=["fp32", "fp16", "int8", "int4", "fp8"]
            )
        ]

    def verify_compatibility(
        self,
        model_format: str,
        required_vram_mb: int,
        quantization: str = "fp16"
    ) -> Tuple[bool, str]:
        if not self.is_available():
            return False, "Not running on Apple Silicon macOS platform."
        return True, "Compatible with Apple Silicon Metal unified memory engine."

    def allocate_context(self, device_id: str, memory_mb: int) -> bool:
        self._allocated_mb[device_id] = self._allocated_mb.get(device_id, 0) + memory_mb
        return True

    def release_context(self, device_id: str, memory_mb: int) -> None:
        self._allocated_mb[device_id] = max(0, self._allocated_mb.get(device_id, 0) - memory_mb)


# =====================================================================
# 6. Acceleration Registry & Transparent Fallback Chain
# =====================================================================
class AccelerationRegistry:
    """
    Central registry of acceleration adapters with automatic verification
    and transparent fallback routing (Preferred -> Secondary -> CPU).
    """

    def __init__(self):
        self._adapters: Dict[str, HardwareAccelerationAdapter] = {}
        self._register_default_adapters()

    def register_adapter(self, adapter: HardwareAccelerationAdapter) -> None:
        self._adapters[adapter.backend_name.lower()] = adapter

    def get_adapter(self, name: str) -> Optional[HardwareAccelerationAdapter]:
        return self._adapters.get(name.lower())

    def list_available_adapters(self) -> List[HardwareAccelerationAdapter]:
        return [a for a in self._adapters.values() if a.is_available()]

    def select_best_adapter(
        self,
        model_format: str,
        required_vram_mb: int = 0,
        quantization: str = "fp16",
        preferred_backend: Optional[str] = None
    ) -> Tuple[HardwareAccelerationAdapter, HardwareDevice, List[str]]:
        """
        Selects optimal execution backend using preference, hardware availability,
        and VRAM headroom. Falls back safely if the preferred accelerator fails validation.
        
        Returns:
            (selected_adapter, target_device, fallback_audit_log)
        """
        audit_log: List[str] = []

        # Determine evaluation order
        order: List[str] = []
        if preferred_backend and preferred_backend.lower() in self._adapters:
            order.append(preferred_backend.lower())

        # Standard priority ranking
        for candidate in ["cuda", "metal", "directml", "openvino", "cpu"]:
            if candidate not in order and candidate in self._adapters:
                order.append(candidate)

        for backend_name in order:
            adapter = self._adapters[backend_name]
            if not adapter.is_available():
                audit_log.append(f"Skipped {backend_name.upper()}: runtime or hardware not available.")
                continue

            is_compat, reason = adapter.verify_compatibility(
                model_format=model_format,
                required_vram_mb=required_vram_mb,
                quantization=quantization
            )

            if not is_compat:
                audit_log.append(f"Incompatible {backend_name.upper()}: {reason}")
                continue

            # Compatible backend found
            devices = adapter.probe_devices()
            target_device = devices[0] if devices else HardwareDevice(
                device_id="cpu",
                name="Fallback CPU",
                device_type=DeviceType.CPU,
                vendor="Host System"
            )

            audit_log.append(f"Selected {backend_name.upper()} on device {target_device.device_id} ({reason})")
            return adapter, target_device, audit_log

        # Ultimate fallback
        cpu_adapter = self._adapters["cpu"]
        audit_log.append("Fell back to universal CPU SIMD adapter.")
        return cpu_adapter, cpu_adapter.probe_devices()[0], audit_log

    def _register_default_adapters(self) -> None:
        self.register_adapter(CPUAccelerationAdapter())
        self.register_adapter(NvidiaCudaAdapter())
        self.register_adapter(AmdRocmDirectMLAdapter())
        self.register_adapter(IntelAcceleratorAdapter())
        self.register_adapter(AppleSiliconAdapter())
