"""
PRUBETH IDE — Indefinite Hardware Upgradability & Progressive Performance Scaling Test Suite
Validates dynamic capability expansion, multi-device topology routing, resource budgeting,
admission control, pluggable acceleration fallback, model re-evaluation, and upgrade-safe persistence.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

from core.hardware.capabilities import (
    DeviceType,
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
from core.capability_registry import CapabilityRegistry
from horizon_engine.hardware_autotuner import HardwareAutoTuner


# =====================================================================
# 1. Tests for Hardware Ceilings Removal & Progressive Scaling
# =====================================================================
def test_no_artificial_hardware_ceilings_on_extreme_workstation():
    """Verify system expands to large worker pools and contexts on 128GB multi-GPU hardware."""
    extreme_snapshot = HardwareSnapshot(
        os_name="Windows",
        os_release="11",
        cpu=CPUCapability(
            physical_cores=32,
            logical_threads=64,
            model_name="AMD Ryzen Threadripper PRO 7995WX",
            supports_avx2=True,
            supports_avx512=True
        ),
        memory=MemoryCapability(
            total_ram_mb=131072,  # 128GB
            available_ram_mb=110000
        ),
        devices=[
            HardwareDevice(
                device_id="cuda:0",
                name="NVIDIA RTX 4090",
                device_type=DeviceType.NVIDIA_CUDA,
                vendor="NVIDIA",
                total_memory_mb=24576,
                available_memory_mb=22000,
                is_primary=True,
                is_healthy=True
            ),
            HardwareDevice(
                device_id="cuda:1",
                name="NVIDIA RTX 4090",
                device_type=DeviceType.NVIDIA_CUDA,
                vendor="NVIDIA",
                total_memory_mb=24576,
                available_memory_mb=22000,
                is_primary=False,
                is_healthy=True
            )
        ],
        storage=StorageCapability(workspace_free_mb=500000, models_cache_free_mb=500000),
        power=PowerCapability(is_on_battery=False)
    )

    profile = DynamicPerformanceTierEngine.evaluate_hardware(extreme_snapshot)
    
    assert profile.tier_level == PerformanceTierLevel.EXTREME_CLUSTER
    assert profile.max_parallel_agents >= 16
    assert profile.background_workers >= 8
    assert profile.cache_capacity_mb >= 8192
    assert profile.max_local_context_tokens >= 131072
    assert profile.simultaneous_provider_requests >= 16


def test_minimal_eco_scaling_on_constrained_device():
    """Verify system contracts gracefully to 1 agent and low memory mode on 4GB device."""
    constrained_snapshot = HardwareSnapshot(
        os_name="Linux",
        os_release="6.1",
        cpu=CPUCapability(physical_cores=2, logical_threads=2, model_name="Intel Celeron"),
        memory=MemoryCapability(total_ram_mb=4096, available_ram_mb=2048),
        devices=[
            HardwareDevice(device_id="cpu", name="Host CPU", device_type=DeviceType.CPU, vendor="Host")
        ],
        power=PowerCapability(is_on_battery=True)
    )

    profile = DynamicPerformanceTierEngine.evaluate_hardware(constrained_snapshot)
    assert profile.tier_level == PerformanceTierLevel.MINIMAL_ECO
    assert profile.max_parallel_agents == 1
    assert profile.low_memory_mode is True
    assert profile.cache_capacity_mb <= 512
    assert profile.pause_indexing_on_battery is True


# =====================================================================
# 2. Tests for Dynamic Hardware Discovery & Telemetry Change Listeners
# =====================================================================
def test_hardware_capability_manager_live_discovery():
    """Verify live hardware discovery accurately detects host CPU, memory, and devices."""
    mgr = HardwareCapabilityManager.get_instance()
    snapshot = mgr.get_current_snapshot()
    
    assert snapshot.os_name != "Unknown"
    assert snapshot.cpu.logical_threads >= 1
    assert snapshot.memory.total_ram_mb > 1000
    assert len(snapshot.devices) >= 1
    assert snapshot.environment_fingerprint != ""


def test_hardware_change_event_listener_notification():
    """Verify change listeners are notified when hardware snapshot changes."""
    mgr = HardwareCapabilityManager(cache_ttl_seconds=0.0)
    events_received = []

    def on_change(old_snap, new_snap):
        events_received.append((old_snap, new_snap))

    mgr.register_change_listener(on_change)

    old_snap = mgr.get_current_snapshot()
    # Create artificial updated snapshot with upgraded RAM
    upgraded_snap = HardwareSnapshot(
        timestamp=old_snap.timestamp + 10,
        os_name=old_snap.os_name,
        os_release=old_snap.os_release,
        cpu=old_snap.cpu,
        memory=MemoryCapability(total_ram_mb=old_snap.memory.total_ram_mb + 16384, available_ram_mb=20000),
        devices=old_snap.devices,
        environment_fingerprint="upgraded_fingerprint_hash"
    )

    # Trigger listener notification
    mgr._notify_listeners(old_snap, upgraded_snap)
    assert len(events_received) == 1
    assert events_received[0][1].memory.total_ram_mb == old_snap.memory.total_ram_mb + 16384

    mgr.unregister_change_listener(on_change)


# =====================================================================
# 3. Tests for Resource Budget Manager & Workload Admission Control
# =====================================================================
def test_admission_controller_admits_within_safe_budget():
    """Verify interactive task within safe RAM budget is immediately admitted."""
    snapshot = HardwareSnapshot(
        memory=MemoryCapability(total_ram_mb=16384, available_ram_mb=12000),
        devices=[HardwareDevice(device_id="cpu", name="CPU", device_type=DeviceType.CPU, vendor="Host")]
    )
    budget = ResourceBudgetManager()

    spec = WorkloadSpec(
        workload_id="task_editor_completion",
        name="Inline Code Completion",
        priority=WorkloadPriority.INTERACTIVE,
        estimated_ram_mb=512,
        estimated_vram_mb=0
    )

    decision = budget.admit_workload(spec, snapshot)
    assert decision.status == AdmissionStatus.ADMITTED
    assert decision.allocated_ram_mb == 512
    assert decision.degradation_ratio == 1.0


def test_admission_controller_degrades_when_headroom_is_tight():
    """Verify heavy workload degrades to 50% budget when headroom is constrained."""
    snapshot = HardwareSnapshot(
        memory=MemoryCapability(total_ram_mb=8192, available_ram_mb=3500),  # 3500MB available - 2048MB OS headroom = 1452MB usable
        devices=[HardwareDevice(device_id="cpu", name="CPU", device_type=DeviceType.CPU, vendor="Host")]
    )
    budget = ResourceBudgetManager()

    spec = WorkloadSpec(
        workload_id="large_batch_index",
        name="Large AST Codebase Indexing",
        priority=WorkloadPriority.BACKGROUND_INDEXING,
        estimated_ram_mb=2000,  # Exceeds 1452MB, but 50% (1000MB) fits
        can_degrade=True
    )

    decision = budget.admit_workload(spec, snapshot)
    assert decision.status == AdmissionStatus.DEGRADED_ADMITTED
    assert decision.allocated_ram_mb == 1000
    assert decision.degradation_ratio == 0.5


def test_admission_controller_evicts_background_for_interactive():
    """Verify low-priority speculative workload is evicted to admit critical interactive task."""
    snapshot = HardwareSnapshot(
        memory=MemoryCapability(total_ram_mb=8192, available_ram_mb=3500),  # 1452MB usable headroom
        devices=[HardwareDevice(device_id="cpu", name="CPU", device_type=DeviceType.CPU, vendor="Host")]
    )
    budget = ResourceBudgetManager()

    # Pre-allocate speculative workload consuming 1000MB
    speculative_spec = WorkloadSpec(
        workload_id="spec_eval_run",
        name="Speculative Benchmark Evaluation",
        priority=WorkloadPriority.SPECULATIVE,
        estimated_ram_mb=1000
    )
    dec1 = budget.admit_workload(speculative_spec, snapshot)
    assert dec1.status == AdmissionStatus.ADMITTED

    # Now interactive prompt requires 1000MB (only ~452MB remains without eviction)
    interactive_spec = WorkloadSpec(
        workload_id="interactive_chat_prompt",
        name="User Code Generation Request",
        priority=WorkloadPriority.INTERACTIVE,
        estimated_ram_mb=1000
    )
    dec2 = budget.admit_workload(interactive_spec, snapshot)
    assert dec2.status == AdmissionStatus.ADMITTED
    # Speculative task was preempted and evicted
    accounting = budget.get_resource_accounting()
    active_ids = [a["workload_id"] for a in accounting["allocations"]]
    assert "interactive_chat_prompt" in active_ids
    assert "spec_eval_run" not in active_ids


# =====================================================================
# 4. Tests for Pluggable Acceleration Adapters & Fallback Chain
# =====================================================================
def test_cpu_acceleration_adapter_always_available():
    """Verify CPU acceleration adapter operates on all platforms."""
    adapter = CPUAccelerationAdapter()
    assert adapter.is_available() is True
    assert adapter.backend_name == "cpu"
    compat, reason = adapter.verify_compatibility("gguf", 4096)
    assert compat is True


def test_nvidia_cuda_adapter_vram_rejection_and_fallback():
    """Verify CUDA adapter rejects models that exceed device VRAM, falling back to CPU."""
    registry = AccelerationRegistry()

    # Test request for 120,000MB (120GB) VRAM model (exceeds any single desktop GPU)
    adapter, device, audit_log = registry.select_best_adapter(
        model_format="gguf",
        required_vram_mb=120000,
        preferred_backend="cuda"
    )

    # Must fall back safely to CPU or DirectML without raising unhandled exceptions
    assert adapter is not None
    assert len(audit_log) >= 1
    assert any("Fell back" in log or "Incompatible" in log or "Selected" in log for log in audit_log)


# =====================================================================
# 5. Tests for Multi-GPU Topology Router & Device Placement
# =====================================================================
def test_multi_gpu_router_selects_best_fit_device():
    """Verify router selects the GPU that best fits required VRAM."""
    devices = [
        HardwareDevice(
            device_id="cuda:0",
            name="RTX 3060",
            device_type=DeviceType.NVIDIA_CUDA,
            vendor="NVIDIA",
            total_memory_mb=12288,
            available_memory_mb=8000
        ),
        HardwareDevice(
            device_id="cuda:1",
            name="RTX 4090",
            device_type=DeviceType.NVIDIA_CUDA,
            vendor="NVIDIA",
            total_memory_mb=24576,
            available_memory_mb=20000
        ),
        HardwareDevice(
            device_id="cpu",
            name="Host CPU",
            device_type=DeviceType.CPU,
            vendor="Host"
        )
    ]
    router = MultiGPURuntimeRouter()

    # Model requiring 6000MB fits in cuda:0 (tightest fit) without unnecessarily consuming cuda:1
    decision = router.assign_device_for_model(
        model_id="qwen2.5-coder:7b",
        required_vram_mb=6000,
        available_devices=devices
    )
    assert decision.strategy == DevicePlacementStrategy.AUTO_BEST_FIT
    assert decision.primary_device_id == "cuda:0"

    # Model requiring 15000MB exceeds cuda:0 and lands on cuda:1
    decision2 = router.assign_device_for_model(
        model_id="deepseek-coder:33b",
        required_vram_mb=15000,
        available_devices=devices
    )
    assert decision2.primary_device_id == "cuda:1"


def test_multi_gpu_router_respects_user_pinning():
    """Verify router respects explicit user device preference."""
    devices = [
        HardwareDevice(device_id="cuda:0", name="GPU 0", device_type=DeviceType.NVIDIA_CUDA, vendor="NVIDIA", total_memory_mb=12000, available_memory_mb=10000),
        HardwareDevice(device_id="cuda:1", name="GPU 1", device_type=DeviceType.NVIDIA_CUDA, vendor="NVIDIA", total_memory_mb=12000, available_memory_mb=10000)
    ]
    router = MultiGPURuntimeRouter()

    decision = router.assign_device_for_model(
        model_id="qwen2.5:7b",
        required_vram_mb=5000,
        available_devices=devices,
        user_device_preference="cuda:1"
    )
    assert decision.strategy == DevicePlacementStrategy.USER_PINNED
    assert decision.primary_device_id == "cuda:1"


def test_multi_gpu_router_cross_vendor_safety():
    """Verify safety check rejects unsafe memory pooling across different vendors."""
    router = MultiGPURuntimeRouter()
    devices = [
        HardwareDevice(device_id="cuda:0", name="NVIDIA RTX 4080", device_type=DeviceType.NVIDIA_CUDA, vendor="NVIDIA"),
        HardwareDevice(device_id="rocm:0", name="AMD Radeon RX 7900", device_type=DeviceType.AMD_ROCM, vendor="AMD")
    ]
    is_safe, reason = router.validate_multi_gpu_safety(["cuda:0", "rocm:0"], devices)
    assert is_safe is False
    assert "Cannot pool VRAM across disparate vendors" in reason


# =====================================================================
# 6. Tests for Dynamic Model Capacity Evaluator & Upgrade Re-evaluation
# =====================================================================
def test_physics_model_memory_calculation():
    """Verify model memory calculator generates correct physics-based transformer footprints."""
    # 7B model in 4-bit quantization with 4096 context tokens
    weights_mb, kv_mb, total_mb = DynamicModelCapacityEvaluator.calculate_model_memory(
        parameters_billion=7.0,
        quantization="q4_k_m",
        context_tokens=4096
    )
    # 7B * 4.5 bits / 8 = ~3.9GB weights
    assert 3500 <= weights_mb <= 4500
    assert kv_mb > 0
    assert total_mb > weights_mb


def test_model_upgrade_reevaluation_flags_newly_feasible_models():
    """Verify previously infeasible model is flagged as newly feasible when GPU upgraded."""
    catalogue = [
        {"id": "deepseek-coder:14b", "parameters_billion": 14.0, "quantization": "q4_k_m", "context_window": 8192}
    ]

    # Old baseline: 4GB GPU
    old_snap = HardwareSnapshot(
        memory=MemoryCapability(total_ram_mb=16384, available_ram_mb=8000),
        devices=[HardwareDevice(device_id="cuda:0", name="GTX 1050 Ti", device_type=DeviceType.NVIDIA_CUDA, vendor="NVIDIA", total_memory_mb=4096, available_memory_mb=3500)]
    )
    eval_old = DynamicModelCapacityEvaluator.reevaluate_catalogue(catalogue, old_snap)
    old_status = eval_old["deepseek-coder:14b"].feasibility

    # New upgraded machine: 16GB RTX 4080
    new_snap = HardwareSnapshot(
        memory=MemoryCapability(total_ram_mb=32768, available_ram_mb=24000),
        devices=[HardwareDevice(device_id="cuda:0", name="RTX 4080", device_type=DeviceType.NVIDIA_CUDA, vendor="NVIDIA", total_memory_mb=16384, available_memory_mb=15000)]
    )
    eval_new = DynamicModelCapacityEvaluator.reevaluate_catalogue(
        catalogue,
        new_snap,
        previous_evaluations={"deepseek-coder:14b": old_status}
    )

    est_new = eval_new["deepseek-coder:14b"]
    assert est_new.feasibility == ModelFeasibilityStatus.FULLY_OFFLOADED_GPU
    assert est_new.is_newly_feasible is True


def test_model_recommendation_never_overrides_user_preference_without_approval():
    """Verify recommendation engine flags user approval required when proposing a different model."""
    snap = HardwareSnapshot(
        memory=MemoryCapability(total_ram_mb=32768, available_ram_mb=24000),
        devices=[HardwareDevice(device_id="cuda:0", name="RTX 4080", device_type=DeviceType.NVIDIA_CUDA, vendor="NVIDIA", total_memory_mb=16384, available_memory_mb=15000)]
    )
    candidates = [
        {"id": "qwen2.5:1.5b", "parameters_billion": 1.5, "quantization": "q4_k_m"},
        {"id": "qwen2.5-coder:7b", "parameters_billion": 7.0, "quantization": "q4_k_m"}
    ]

    rec = DynamicModelCapacityEvaluator.recommend_optimal_model(
        task_category="coding",
        candidates=candidates,
        hardware_snapshot=snap,
        active_user_preference="qwen2.5:1.5b"
    )
    # Proposes 7B, but flags requires_user_approval = True because user preferred 1.5B
    assert rec["recommended_model_id"] == "qwen2.5-coder:7b"
    assert rec["requires_user_approval"] is True


# =====================================================================
# 7. Tests for Upgrade-Safe Persistence & Journaling
# =====================================================================
def test_hardware_persistence_records_upgrade_events_and_preserves_user_settings():
    """Verify hardware upgrade is journaled and user manual overrides are strictly preserved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        mgr = HardwarePersistenceManager(storage_dir=storage_dir)

        # Baseline: 16GB RAM laptop
        base_snap = HardwareSnapshot(
            memory=MemoryCapability(total_ram_mb=16384, available_ram_mb=12000),
            devices=[HardwareDevice(device_id="cpu", name="Host CPU", device_type=DeviceType.CPU, vendor="Host")],
            environment_fingerprint="fp_baseline_16gb"
        )
        user_settings = {
            "custom_theme": "Cyberpunk Neon",
            "api_key_custom": "sk-secret123",
            "local_model": "my-pinned-model",
            "performance": {"background_workers": 2, "cache_mb": 512}
        }

        # Initial sync
        has_changed, updated_settings, audit = mgr.synchronize_hardware_upgrade(base_snap, user_settings)
        assert has_changed is True
        assert updated_settings["custom_theme"] == "Cyberpunk Neon"

        # Upgraded machine: 64GB RAM with RTX 4090 GPU
        upgraded_snap = HardwareSnapshot(
            memory=MemoryCapability(total_ram_mb=65536, available_ram_mb=50000),
            devices=[HardwareDevice(device_id="cuda:0", name="RTX 4090", device_type=DeviceType.NVIDIA_CUDA, vendor="NVIDIA", total_memory_mb=24576, available_memory_mb=22000)],
            environment_fingerprint="fp_upgraded_64gb_rtx4090"
        )

        has_changed2, updated_settings2, audit2 = mgr.synchronize_hardware_upgrade(upgraded_snap, updated_settings)
        assert has_changed2 is True
        assert len(audit2) >= 1

        # Check audit log file exists and contains entry
        assert mgr.audit_log_path.exists()
        with open(mgr.audit_log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            assert "System RAM changed: 16384MB -> 65536MB" in log_content

        # Verify user manual overrides were untouched
        assert updated_settings2["custom_theme"] == "Cyberpunk Neon"
        assert updated_settings2["api_key_custom"] == "sk-secret123"
        assert updated_settings2["local_model"] == "my-pinned-model"

        # Verify performance parameters expanded dynamically
        assert updated_settings2["cache_mb"] >= 2048


# =====================================================================
# 8. Tests for Universal Capability Registry Integration
# =====================================================================
def test_capability_registry_hardware_components_registered():
    """Verify hardware scaling components are queryable via central CapabilityRegistry."""
    registry = CapabilityRegistry.get_instance()
    
    cap_mgr = registry.get("hw.capability_manager")
    assert cap_mgr is not None
    assert cap_mgr.status == "implemented"

    cap_budget = registry.get("hw.resource_budget")
    assert cap_budget is not None
    assert "Admission" in cap_budget.name

    cap_tiers = registry.get("hw.performance_tiers")
    assert cap_tiers is not None

    cap_adapters = registry.get("hw.acceleration_adapters")
    assert cap_adapters is not None

    cap_multi = registry.get("hw.multi_gpu")
    assert cap_multi is not None

    cap_models = registry.get("hw.model_expansion")
    assert cap_models is not None
