"""
PRUBETH IDE — Indefinite Hardware Upgradability & Progressive Performance Scaling Engine
Public package interface.
"""

from core.hardware.capabilities import (
    DeviceType,
    QuantizationType,
    HardwareDevice,
    CPUCapability,
    MemoryCapability,
    StorageCapability,
    PowerCapability,
    HardwareSnapshot,
)
from core.hardware.detection import HardwareCapabilityManager
from core.hardware.acceleration_adapters import (
    HardwareAccelerationAdapter,
    CPUAccelerationAdapter,
    NvidiaCudaAdapter,
    AmdRocmDirectMLAdapter,
    IntelAcceleratorAdapter,
    AppleSiliconAdapter,
    AccelerationRegistry,
)
from core.hardware.resource_budget import (
    WorkloadPriority,
    AdmissionStatus,
    WorkloadSpec,
    AdmissionDecision,
    ResourceBudgetConfig,
    ResourceBudgetManager,
)
from core.hardware.performance_tiers import (
    PerformanceTierLevel,
    ScalingProfile,
    DynamicPerformanceTierEngine,
)
from core.hardware.multi_gpu import (
    DevicePlacementStrategy,
    PlacementDecision,
    MultiGPURuntimeRouter,
)
from core.hardware.model_expansion import (
    ModelFeasibilityStatus,
    ModelResourceEstimate,
    DynamicModelCapacityEvaluator,
)
from core.hardware.persistence import HardwarePersistenceManager

__all__ = [
    "DeviceType",
    "QuantizationType",
    "HardwareDevice",
    "CPUCapability",
    "MemoryCapability",
    "StorageCapability",
    "PowerCapability",
    "HardwareSnapshot",
    "HardwareCapabilityManager",
    "HardwareAccelerationAdapter",
    "CPUAccelerationAdapter",
    "NvidiaCudaAdapter",
    "AmdRocmDirectMLAdapter",
    "IntelAcceleratorAdapter",
    "AppleSiliconAdapter",
    "AccelerationRegistry",
    "WorkloadPriority",
    "AdmissionStatus",
    "WorkloadSpec",
    "AdmissionDecision",
    "ResourceBudgetConfig",
    "ResourceBudgetManager",
    "PerformanceTierLevel",
    "ScalingProfile",
    "DynamicPerformanceTierEngine",
    "DevicePlacementStrategy",
    "PlacementDecision",
    "MultiGPURuntimeRouter",
    "ModelFeasibilityStatus",
    "ModelResourceEstimate",
    "DynamicModelCapacityEvaluator",
    "HardwarePersistenceManager",
]
