"""
PRUBETH IDE — Resource Budget Manager & Workload Admission Controller
Part of the Indefinite Hardware Upgradability & Progressive Performance Scaling Engine.

Enforces configurable budgets for CPU %, RAM, GPU VRAM, active worker concurrency,
and background activity. Features admission control, hysteresis smoothing to prevent
rapid tier oscillation, priority queues, backpressure, and safe memory pressure degradation.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import Dict, Any, List, Optional, Tuple, Callable

from core.hardware.capabilities import HardwareSnapshot, DeviceType, HardwareDevice


class WorkloadPriority(IntEnum):
    """Execution priority levels for workload admission and preemptive eviction."""
    INTERACTIVE = 1         # Highest: User prompt responses, visual editing, UI chat
    CODE_INTELLIGENCE = 2   # High: LSP diagnostics, inline completion, typechecking
    BACKGROUND_INDEXING = 3 # Medium: RAG embedding, AST codebase indexing, git scanning
    SPECULATIVE = 4         # Low: Speculative pre-computations, automated eval runs


class AdmissionStatus(str, Enum):
    ADMITTED = "admitted"
    DEGRADED_ADMITTED = "degraded_admitted"
    QUEUED = "queued"
    REJECTED = "rejected"


@dataclass
class WorkloadSpec:
    """Resource requirement contract for an incoming task, agent, or model invocation."""
    workload_id: str
    name: str
    priority: WorkloadPriority
    estimated_ram_mb: int = 512
    estimated_vram_mb: int = 0
    estimated_cpu_threads: int = 1
    target_device_id: Optional[str] = None
    can_degrade: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class AdmissionDecision:
    """Formal admission decision emitted by the ResourceBudgetManager."""
    status: AdmissionStatus
    workload_spec: WorkloadSpec
    allocated_ram_mb: int = 0
    allocated_vram_mb: int = 0
    allocated_threads: int = 0
    assigned_device_id: str = "cpu"
    degradation_ratio: float = 1.0  # 1.0 = full capability, 0.5 = 50% context / batch
    reason: str = ""


@dataclass
class ResourceBudgetConfig:
    """Configurable resource boundary limits and safety margins."""
    max_cpu_percent: float = 80.0
    os_headroom_ram_percent: float = 18.0     # Reserve 18% RAM for OS and GUI responsiveness
    min_os_headroom_ram_mb: int = 2048        # At least 2GB reserved for OS
    max_vram_utilization_ratio: float = 0.85  # Max 85% VRAM used per GPU
    max_active_workers_per_core: float = 1.5
    memory_pressure_high_threshold: float = 0.88  # Trigger degradation
    memory_pressure_low_threshold: float = 0.70   # Relieve degradation
    hysteresis_window_seconds: float = 5.0


class ResourceBudgetManager:
    """
    Guarantees stable IDE performance and system responsiveness by admitting
    or throttling workloads based on live measured resource availability.
    """

    def __init__(self, config: Optional[ResourceBudgetConfig] = None):
        self.config = config or ResourceBudgetConfig()
        self._lock = threading.RLock()
        
        # Active allocations: workload_id -> AdmissionDecision
        self._active_allocations: Dict[str, AdmissionDecision] = {}
        
        # Backpressure queue of pending workloads: List[WorkloadSpec] sorted by priority
        self._queued_workloads: List[WorkloadSpec] = []
        
        # Hysteresis state tracking
        self._last_pressure_change_time: float = 0.0
        self._is_under_pressure: bool = False

    def admit_workload(
        self,
        spec: WorkloadSpec,
        hardware_snapshot: HardwareSnapshot
    ) -> AdmissionDecision:
        """
        Evaluates incoming workload resource requirements against available headroom.
        Returns ADMITTED, DEGRADED_ADMITTED, QUEUED, or REJECTED.
        """
        with self._lock:
            # 1. Calculate safe RAM headroom
            total_ram = hardware_snapshot.memory.total_ram_mb
            avail_ram = hardware_snapshot.memory.available_ram_mb
            os_headroom = max(
                self.config.min_os_headroom_ram_mb,
                int(total_ram * (self.config.os_headroom_ram_percent / 100.0))
            )
            safe_usable_ram = max(0, avail_ram - os_headroom)

            # Subtract currently admitted active workloads
            current_active_ram = sum(d.allocated_ram_mb for d in self._active_allocations.values())
            remaining_ram_budget = max(0, safe_usable_ram - current_active_ram)

            # 2. Calculate device VRAM headroom if targeting a GPU
            target_device = None
            assigned_device_id = "cpu"
            req_vram = spec.estimated_vram_mb

            if req_vram > 0 and spec.target_device_id and spec.target_device_id != "cpu":
                target_device = next(
                    (d for d in hardware_snapshot.devices if d.device_id == spec.target_device_id),
                    None
                )
            elif req_vram > 0:
                # Find device with most free VRAM
                candidate_gpus = [d for d in hardware_snapshot.devices if d.device_type != DeviceType.CPU and d.is_healthy]
                if candidate_gpus:
                    target_device = max(candidate_gpus, key=lambda d: d.available_memory_mb)

            vram_budget_ok = True
            safe_vram_headroom = 0
            if target_device and target_device.device_type != DeviceType.CPU:
                assigned_device_id = target_device.device_id
                active_dev_vram = sum(
                    d.allocated_vram_mb for d in self._active_allocations.values()
                    if d.assigned_device_id == assigned_device_id
                )
                max_dev_budget = int(target_device.total_memory_mb * self.config.max_vram_utilization_ratio)
                safe_vram_headroom = max(0, min(target_device.available_memory_mb, max_dev_budget) - active_dev_vram)
                if req_vram > safe_vram_headroom:
                    vram_budget_ok = False

            # 3. Admission Logic
            if remaining_ram_budget >= spec.estimated_ram_mb and (req_vram == 0 or vram_budget_ok):
                decision = AdmissionDecision(
                    status=AdmissionStatus.ADMITTED,
                    workload_spec=spec,
                    allocated_ram_mb=spec.estimated_ram_mb,
                    allocated_vram_mb=req_vram,
                    allocated_threads=spec.estimated_cpu_threads,
                    assigned_device_id=assigned_device_id,
                    degradation_ratio=1.0,
                    reason=f"Admitted with full resource allocation on {assigned_device_id}."
                )
                self._active_allocations[spec.workload_id] = decision
                return decision

            # 4. Attempt graceful degradation if workload supports it
            if spec.can_degrade:
                degraded_ram = max(128, spec.estimated_ram_mb // 2)
                degraded_vram = req_vram // 2
                degraded_threads = max(1, spec.estimated_cpu_threads // 2)

                can_admit_degraded = (remaining_ram_budget >= degraded_ram) and (
                    degraded_vram == 0 or safe_vram_headroom >= degraded_vram
                )

                if can_admit_degraded:
                    decision = AdmissionDecision(
                        status=AdmissionStatus.DEGRADED_ADMITTED,
                        workload_spec=spec,
                        allocated_ram_mb=degraded_ram,
                        allocated_vram_mb=degraded_vram,
                        allocated_threads=degraded_threads,
                        assigned_device_id=assigned_device_id,
                        degradation_ratio=0.5,
                        reason="Admitted in degraded mode (50% context / batch) to respect headroom."
                    )
                    self._active_allocations[spec.workload_id] = decision
                    return decision

            # 5. Check if we should evict lower-priority workloads for an INTERACTIVE request
            if spec.priority == WorkloadPriority.INTERACTIVE:
                evicted = self._evict_lower_priority(spec.estimated_ram_mb, req_vram)
                if evicted:
                    # Retry admission recursively
                    return self.admit_workload(spec, hardware_snapshot)

            # 6. Queue or reject
            if spec.priority in (WorkloadPriority.INTERACTIVE, WorkloadPriority.CODE_INTELLIGENCE):
                self._queued_workloads.append(spec)
                self._queued_workloads.sort(key=lambda s: s.priority.value)
                return AdmissionDecision(
                    status=AdmissionStatus.QUEUED,
                    workload_spec=spec,
                    reason="Insufficient instant headroom; queued in backpressure priority buffer."
                )

            # Low priority background or speculative task is rejected under load
            return AdmissionDecision(
                status=AdmissionStatus.REJECTED,
                workload_spec=spec,
                reason="Workload deferred: system capacity allocated to higher-priority interactive tasks."
            )

    def complete_workload(self, workload_id: str) -> Optional[AdmissionDecision]:
        """Releases the allocated budget for a finished or canceled workload."""
        with self._lock:
            decision = self._active_allocations.pop(workload_id, None)
            return decision

    def _evict_lower_priority(self, needed_ram: int, needed_vram: int) -> List[str]:
        """Preempts speculative and background workloads to clear capacity for interactive requests."""
        evicted_ids: List[str] = []
        # Sort active allocations descending by priority number (highest enum value = lowest priority)
        candidates = sorted(
            self._active_allocations.values(),
            key=lambda d: d.workload_spec.priority.value,
            reverse=True
        )

        for candidate in candidates:
            if candidate.workload_spec.priority > WorkloadPriority.CODE_INTELLIGENCE:
                # Evict background or speculative task
                self._active_allocations.pop(candidate.workload_spec.workload_id, None)
                evicted_ids.append(candidate.workload_spec.workload_id)
                # Check if we freed enough
                needed_ram -= candidate.allocated_ram_mb
                needed_vram -= candidate.allocated_vram_mb
                if needed_ram <= 0 and needed_vram <= 0:
                    break

        return evicted_ids

    def update_memory_pressure_state(self, hardware_snapshot: HardwareSnapshot) -> bool:
        """
        Calculates memory pressure with hysteresis smoothing to prevent rapid toggling.
        Returns True if system is under high memory pressure.
        """
        with self._lock:
            now = time.time()
            utilization = hardware_snapshot.memory.ram_utilization_ratio

            # Check if threshold crossed
            if not self._is_under_pressure and utilization >= self.config.memory_pressure_high_threshold:
                # Enter pressure state
                self._is_under_pressure = True
                self._last_pressure_change_time = now
            elif self._is_under_pressure and utilization <= self.config.memory_pressure_low_threshold:
                # Check hysteresis window before exiting pressure state
                if (now - self._last_pressure_change_time) >= self.config.hysteresis_window_seconds:
                    self._is_under_pressure = False
                    self._last_pressure_change_time = now

            return self._is_under_pressure

    def get_resource_accounting(self) -> Dict[str, Any]:
        """Returns diagnostic telemetry of current allocations and queue depth."""
        with self._lock:
            return {
                "active_workload_count": len(self._active_allocations),
                "queued_workload_count": len(self._queued_workloads),
                "total_allocated_ram_mb": sum(d.allocated_ram_mb for d in self._active_allocations.values()),
                "total_allocated_vram_mb": sum(d.allocated_vram_mb for d in self._active_allocations.values()),
                "is_under_memory_pressure": self._is_under_pressure,
                "allocations": [
                    {
                        "workload_id": d.workload_spec.workload_id,
                        "name": d.workload_spec.name,
                        "priority": d.workload_spec.priority.name,
                        "status": d.status.value,
                        "ram_mb": d.allocated_ram_mb,
                        "vram_mb": d.allocated_vram_mb,
                        "device": d.assigned_device_id
                    }
                    for d in self._active_allocations.values()
                ]
            }
