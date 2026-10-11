"""
PRUBETH IDE — Dynamic Model Capacity Evaluator & Hardware Expansion Engine
Part of the Indefinite Hardware Upgradability & Progressive Performance Scaling Engine.

Calculates accurate VRAM/RAM footprints (weights, KV cache, scratchpad activations)
for various quantization types (Q4_K_M, Q8_0, FP16, FP8). Reevaluates catalog feasibility
upon hardware upgrades and recommends optimal models without unpermitted model swaps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

from core.hardware.capabilities import HardwareSnapshot, DeviceType, HardwareDevice


class ModelFeasibilityStatus(str, Enum):
    FULLY_OFFLOADED_GPU = "fully_offloaded_gpu"        # 100% in GPU VRAM (fastest)
    PARTIALLY_OFFLOADED_HYBRID = "hybrid_gpu_cpu"       # Split layers between GPU and CPU RAM
    CPU_RAM_ONLY = "cpu_ram_only"                      # Fits in system RAM, runs on CPU
    EXCEEDS_CAPACITY = "exceeds_capacity"              # Insufficient RAM/VRAM


@dataclass
class ModelResourceEstimate:
    """Calculated memory requirements and runtime feasibility for a model."""
    model_id: str
    parameters_billion: float
    quantization: str
    context_tokens: int
    weights_memory_mb: int
    kv_cache_memory_mb: int
    total_memory_required_mb: int
    feasibility: ModelFeasibilityStatus
    recommended_device_id: str
    estimated_tokens_per_sec: float
    is_newly_feasible: bool = False
    diagnostic_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "parameters_billion": self.parameters_billion,
            "quantization": self.quantization,
            "context_tokens": self.context_tokens,
            "weights_memory_mb": self.weights_memory_mb,
            "kv_cache_memory_mb": self.kv_cache_memory_mb,
            "total_memory_required_mb": self.total_memory_required_mb,
            "feasibility": self.feasibility.value,
            "recommended_device_id": self.recommended_device_id,
            "estimated_tokens_per_sec": self.estimated_tokens_per_sec,
            "is_newly_feasible": self.is_newly_feasible,
            "diagnostic_notes": self.diagnostic_notes
        }


class DynamicModelCapacityEvaluator:
    """
    Computes precise memory bounds for local AI models and dynamically re-evaluates
    catalog capability whenever system hardware, drivers, or VRAM budgets expand.
    """

    # Bits per weight for standard quantizations
    BITS_PER_WEIGHT = {
        "fp32": 32.0,
        "fp16": 16.0,
        "bf16": 16.0,
        "int8": 8.5,    # 8-bit + scale metadata
        "q8_0": 8.5,
        "int4": 4.5,    # 4-bit + scale metadata
        "q4_k_m": 4.5,
        "q4_0": 4.5,
        "fp8": 8.2,
        "fp4": 4.3,
        "q5_k_m": 5.5,
        "q6_k": 6.5
    }

    @classmethod
    def calculate_model_memory(
        cls,
        parameters_billion: float,
        quantization: str = "q4_k_m",
        context_tokens: int = 4096,
        layers: int = 32,
        hidden_dim: int = 4096
    ) -> Tuple[int, int, int]:
        """
        Calculates (weights_mb, kv_cache_mb, total_mb) using physical transformer equations.
        
        Weights MB = (params_b * 10^9 * bits_per_weight) / (8 * 1024 * 1024)
        KV Cache MB = 2 * layers * hidden_dim * context_tokens * 2 bytes (FP16) / (1024 * 1024)
        """
        bits = cls.BITS_PER_WEIGHT.get(quantization.lower(), 4.5)
        # Weights in MB
        weights_bytes = (parameters_billion * 1e9 * bits) / 8.0
        weights_mb = int(math.ceil(weights_bytes / (1024.0 * 1024.0)))

        # Standard GQA / MHA KV cache calculation in FP16 (2 bytes per element)
        # 2 tensors (key, value) * layers * hidden_dim * tokens * 2 bytes
        kv_cache_bytes = 2 * layers * hidden_dim * context_tokens * 2
        kv_cache_mb = int(math.ceil(kv_cache_bytes / (1024.0 * 1024.0)))

        # Runtime scratchpad buffer (~10% of weights)
        scratchpad_mb = max(128, int(weights_mb * 0.10))

        total_mb = weights_mb + kv_cache_mb + scratchpad_mb
        return weights_mb, kv_cache_mb, total_mb

    @classmethod
    def evaluate_model_feasibility(
        cls,
        model_id: str,
        parameters_billion: float,
        quantization: str,
        context_tokens: int,
        hardware_snapshot: HardwareSnapshot,
        previous_feasibility: Optional[ModelFeasibilityStatus] = None
    ) -> ModelResourceEstimate:
        """
        Evaluates whether a model can be hosted on available GPU(s) or system RAM.
        """
        weights_mb, kv_mb, total_mb = cls.calculate_model_memory(
            parameters_billion=parameters_billion,
            quantization=quantization,
            context_tokens=context_tokens
        )

        gpus = [d for d in hardware_snapshot.devices if d.device_type != DeviceType.CPU and d.is_healthy]
        best_gpu = max(gpus, key=lambda d: d.available_memory_mb) if gpus else None

        avail_ram = hardware_snapshot.memory.available_ram_mb
        safe_ram_headroom = max(0, avail_ram - 2048)  # Leave 2GB for OS

        # 1. Full GPU Offload
        if best_gpu and (best_gpu.available_memory_mb - 512) >= total_mb:
            speed_toks = cls._estimate_tokens_per_sec(parameters_billion, "gpu", best_gpu.device_type)
            is_new = (previous_feasibility is not None and previous_feasibility != ModelFeasibilityStatus.FULLY_OFFLOADED_GPU)
            return ModelResourceEstimate(
                model_id=model_id,
                parameters_billion=parameters_billion,
                quantization=quantization,
                context_tokens=context_tokens,
                weights_memory_mb=weights_mb,
                kv_cache_memory_mb=kv_mb,
                total_memory_required_mb=total_mb,
                feasibility=ModelFeasibilityStatus.FULLY_OFFLOADED_GPU,
                recommended_device_id=best_gpu.device_id,
                estimated_tokens_per_sec=speed_toks,
                is_newly_feasible=is_new,
                diagnostic_notes=f"Fits fully in {best_gpu.name} VRAM ({total_mb}MB required, {best_gpu.available_memory_mb}MB available)."
            )

        # 2. Hybrid GPU + CPU Offload
        if best_gpu and best_gpu.available_memory_mb > 2048:
            gpu_usable = best_gpu.available_memory_mb - 512
            cpu_needed = total_mb - gpu_usable
            if safe_ram_headroom >= cpu_needed:
                speed_toks = cls._estimate_tokens_per_sec(parameters_billion, "hybrid", best_gpu.device_type)
                is_new = (previous_feasibility is not None and previous_feasibility == ModelFeasibilityStatus.EXCEEDS_CAPACITY)
                return ModelResourceEstimate(
                    model_id=model_id,
                    parameters_billion=parameters_billion,
                    quantization=quantization,
                    context_tokens=context_tokens,
                    weights_memory_mb=weights_mb,
                    kv_cache_memory_mb=kv_mb,
                    total_memory_required_mb=total_mb,
                    feasibility=ModelFeasibilityStatus.PARTIALLY_OFFLOADED_HYBRID,
                    recommended_device_id=best_gpu.device_id,
                    estimated_tokens_per_sec=speed_toks,
                    is_newly_feasible=is_new,
                    diagnostic_notes=f"Hybrid offload: {gpu_usable}MB on GPU, {cpu_needed}MB on host RAM."
                )

        # 3. CPU RAM Only
        if safe_ram_headroom >= total_mb:
            speed_toks = cls._estimate_tokens_per_sec(parameters_billion, "cpu", DeviceType.CPU)
            is_new = (previous_feasibility is not None and previous_feasibility == ModelFeasibilityStatus.EXCEEDS_CAPACITY)
            return ModelResourceEstimate(
                model_id=model_id,
                parameters_billion=parameters_billion,
                quantization=quantization,
                context_tokens=context_tokens,
                weights_memory_mb=weights_mb,
                kv_cache_memory_mb=kv_mb,
                total_memory_required_mb=total_mb,
                feasibility=ModelFeasibilityStatus.CPU_RAM_ONLY,
                recommended_device_id="cpu",
                estimated_tokens_per_sec=speed_toks,
                is_newly_feasible=is_new,
                diagnostic_notes=f"Host CPU RAM execution: {total_mb}MB in system memory ({safe_ram_headroom}MB available)."
            )

        # 4. Exceeds Capacity
        return ModelResourceEstimate(
            model_id=model_id,
            parameters_billion=parameters_billion,
            quantization=quantization,
            context_tokens=context_tokens,
            weights_memory_mb=weights_mb,
            kv_cache_memory_mb=kv_mb,
            total_memory_required_mb=total_mb,
            feasibility=ModelFeasibilityStatus.EXCEEDS_CAPACITY,
            recommended_device_id="none",
            estimated_tokens_per_sec=0.0,
            is_newly_feasible=False,
            diagnostic_notes=f"Exceeds host capacity: Requires {total_mb}MB, but system only has {safe_ram_headroom}MB RAM and {best_gpu.available_memory_mb if best_gpu else 0}MB VRAM."
        )

    @classmethod
    def reevaluate_catalogue(
        cls,
        catalogue: List[Dict[str, Any]],
        hardware_snapshot: HardwareSnapshot,
        previous_evaluations: Optional[Dict[str, ModelFeasibilityStatus]] = None
    ) -> Dict[str, ModelResourceEstimate]:
        """
        Reevaluates an entire model catalog. Flags models that transition from
        infeasible to feasible following a hardware upgrade.
        """
        results: Dict[str, ModelResourceEstimate] = {}
        prev = previous_evaluations or {}

        for item in catalogue:
            m_id = item.get("id") or item.get("model_id", "unknown")
            params = float(item.get("parameters_billion", 7.0))
            quant = item.get("quantization", "q4_k_m")
            ctx = int(item.get("context_window", 4096))
            prev_status = prev.get(m_id)

            est = cls.evaluate_model_feasibility(
                model_id=m_id,
                parameters_billion=params,
                quantization=quant,
                context_tokens=ctx,
                hardware_snapshot=hardware_snapshot,
                previous_feasibility=prev_status
            )
            results[m_id] = est

        return results

    @classmethod
    def recommend_optimal_model(
        cls,
        task_category: str,
        candidates: List[Dict[str, Any]],
        hardware_snapshot: HardwareSnapshot,
        active_user_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recommends highest-quality feasible model based on latency, resources, and privacy.
        Crucially respects active_user_preference and never overrides user choices automatically.
        """
        evaluations = cls.reevaluate_catalogue(candidates, hardware_snapshot)

        # Filter feasible models
        feasible = [
            (c, evaluations[c.get("id", c.get("model_id"))])
            for c in candidates
            if evaluations[c.get("id", c.get("model_id"))].feasibility != ModelFeasibilityStatus.EXCEEDS_CAPACITY
        ]

        if not feasible:
            return {
                "recommended_model_id": active_user_preference or "qwen2.5:1.5b",
                "reason": "Fallback to minimal instruction model; no larger models fit current hardware.",
                "requires_user_approval": True
            }

        # Score candidates based on speed and parameter capacity
        def score_fn(item_pair):
            c, est = item_pair
            # GPU preference score
            gpu_bonus = 50.0 if est.feasibility == ModelFeasibilityStatus.FULLY_OFFLOADED_GPU else 10.0
            speed_score = min(100.0, est.estimated_tokens_per_sec * 2.0)
            # Parameter depth score (prefer 7B-14B if fitting, but don't over-prioritize >32B unless extreme)
            param_score = min(50.0, est.parameters_billion * 3.0)
            return gpu_bonus + speed_score + param_score

        best_candidate, best_est = max(feasible, key=score_fn)
        best_id = best_candidate.get("id", best_candidate.get("model_id"))

        is_different = (active_user_preference is not None and best_id != active_user_preference)

        return {
            "recommended_model_id": best_id,
            "feasibility": best_est.feasibility.value,
            "estimated_speed_tokens_sec": best_est.estimated_tokens_per_sec,
            "recommended_device": best_est.recommended_device_id,
            "requires_user_approval": is_different,
            "reason": (
                f"Selected {best_id} ({best_est.parameters_billion}B params, {best_est.quantization}) "
                f"running at ~{best_est.estimated_tokens_per_sec:.1f} tok/s on {best_est.recommended_device_id}."
            )
        }

    @staticmethod
    def _estimate_tokens_per_sec(params_b: float, mode: str, dev_type: DeviceType) -> float:
        """Estimates generation throughput tokens per second."""
        if mode == "gpu":
            if dev_type == DeviceType.NVIDIA_CUDA:
                return max(15.0, min(180.0, 350.0 / math.sqrt(max(1.0, params_b))))
            elif dev_type == DeviceType.APPLE_SILICON:
                return max(12.0, min(140.0, 260.0 / math.sqrt(max(1.0, params_b))))
            return max(10.0, min(100.0, 200.0 / math.sqrt(max(1.0, params_b))))
        elif mode == "hybrid":
            return max(5.0, min(35.0, 60.0 / math.sqrt(max(1.0, params_b))))
        else: # cpu
            return max(2.0, min(25.0, 40.0 / math.sqrt(max(1.0, params_b))))
