"""PRUBETH IDE - Personal Model Laboratory & Offline-First Policy Guard
====================================================================
Benchmarking harness for local LLMs, quantization and context-length profiling,
and strict air-gapped / offline-only policy enforcement preventing unauthorized
network egress during model inference and local research.
"""

from __future__ import annotations

import contextlib
import enum
import logging
import socket
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Models
# ============================================================================

class OfflinePolicyMode(str, enum.Enum):
    STRICT_AIRGAP = "STRICT_AIRGAP"        # Rejects all non-loopback connections instantly
    LOCAL_ONLY_HOST = "LOCAL_ONLY_HOST"    # Allows localhost (127.0.0.1) and LAN subnet
    AUDIT_ONLY = "AUDIT_ONLY"              # Logs egress attempts without blocking


class AirGapViolationError(RuntimeError):
    """Raised when an unauthorized outbound network connection is attempted."""
    pass


@dataclass
class BenchmarkMetric:
    model_name: str
    first_token_latency_ms: float
    tokens_per_second: float
    total_duration_ms: float
    prompt_tokens: int
    completion_tokens: int
    vram_allocated_mb: float = 0.0
    context_degradation_score: float = 1.0  # 1.0 = zero slowdown with large context

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AirGapAuditEntry:
    timestamp: float
    target_host: str
    target_port: int
    allowed: bool
    policy_mode: OfflinePolicyMode
    caller: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["policy_mode"] = self.policy_mode.value
        return d


# ============================================================================
# Offline-First Policy Enforcement Guard
# ============================================================================

class OfflineEnforcementPolicy:
    """Enforces zero remote egress for sensitive development and air-gapped research."""

    ALLOWED_LOCAL_HOSTS = {
        "127.0.0.1", "localhost", "::1"
    }

    def __init__(self, mode: OfflinePolicyMode = OfflinePolicyMode.STRICT_AIRGAP) -> None:
        self._mode = mode
        self._audit_log: List[AirGapAuditEntry] = []

    @property
    def mode(self) -> OfflinePolicyMode:
        return self._mode

    def set_mode(self, mode: OfflinePolicyMode) -> None:
        logger.info(f"Offline Enforcement Policy mode transitioned to {mode.value}")
        self._mode = mode

    def is_destination_allowed(self, host: str, port: int = 0) -> bool:
        """Evaluates whether destination host conforms to offline policy."""
        clean_host = host.lower().strip()
        is_local = clean_host in self.ALLOWED_LOCAL_HOSTS or clean_host.startswith("127.")

        if self._mode == OfflinePolicyMode.STRICT_AIRGAP:
            return is_local
        elif self._mode == OfflinePolicyMode.LOCAL_ONLY_HOST:
            # Allow local subnet (192.168.x.x, 10.x.x.x)
            return is_local or clean_host.startswith("192.168.") or clean_host.startswith("10.")
        return True

    def check_and_audit(self, host: str, port: int = 0, caller: str = "unknown") -> bool:
        """Audits connection attempt and enforces policy."""
        allowed = self.is_destination_allowed(host, port)
        entry = AirGapAuditEntry(
            timestamp=time.time(),
            target_host=host,
            target_port=port,
            allowed=allowed,
            policy_mode=self._mode,
            caller=caller,
        )
        self._audit_log.append(entry)

        if not allowed and self._mode == OfflinePolicyMode.STRICT_AIRGAP:
            err_msg = (
                f"AIR-GAP POLICY VIOLATION: Blocked unauthorized external connection to "
                f"'{host}:{port}' initiated by {caller}."
            )
            logger.error(err_msg)
            raise AirGapViolationError(err_msg)

        return allowed

    def get_audit_log(self) -> List[AirGapAuditEntry]:
        return list(self._audit_log)

    def clear_audit_log(self) -> None:
        self._audit_log.clear()

    @contextlib.contextmanager
    def strict_offline_guard(self) -> Iterator[None]:
        """Context manager patching socket.socket.connect to intercept external calls."""
        orig_connect = socket.socket.connect

        def guarded_connect(sock_self: socket.socket, address: Any) -> Any:
            host = ""
            port = 0
            if isinstance(address, tuple) and len(address) >= 2:
                host, port = address[0], address[1]
            elif isinstance(address, str):
                host = address

            self.check_and_audit(host, port, caller="socket.connect")
            return orig_connect(sock_self, address)

        socket.socket.connect = guarded_connect  # type: ignore
        try:
            yield
        finally:
            socket.socket.connect = orig_connect  # type: ignore


# ============================================================================
# Model Benchmark Harness
# ============================================================================

class ModelBenchmarkHarness:
    """Profiles token latency, throughput, and context degradation for local models."""

    def __init__(self, offline_policy: Optional[OfflineEnforcementPolicy] = None) -> None:
        self._offline_policy = offline_policy or OfflineEnforcementPolicy()

    def benchmark_stream(
        self,
        model_name: str,
        stream_generator_fn: Callable[[], Iterator[str]],
        prompt_token_count: int = 50,
        simulated_vram_mb: float = 3584.0,
    ) -> BenchmarkMetric:
        """Executes streaming benchmark measuring FTL and tokens/sec."""
        first_token_time: Optional[float] = None
        token_count = 0
        start_time = time.perf_counter()

        # Iterate tokens and measure latency
        for _ in stream_generator_fn():
            if first_token_time is None:
                first_token_time = time.perf_counter()
            token_count += 1

        end_time = time.perf_counter()
        total_duration_sec = end_time - start_time
        ftl_ms = ((first_token_time - start_time) * 1000.0) if first_token_time else 0.0
        generation_duration_sec = (end_time - first_token_time) if first_token_time else total_duration_sec
        tps = (token_count / generation_duration_sec) if generation_duration_sec > 0 else 0.0

        return BenchmarkMetric(
            model_name=model_name,
            first_token_latency_ms=round(ftl_ms, 2),
            tokens_per_second=round(tps, 2),
            total_duration_ms=round(total_duration_sec * 1000.0, 2),
            prompt_tokens=prompt_token_count,
            completion_tokens=token_count,
            vram_allocated_mb=simulated_vram_mb,
            context_degradation_score=1.0,
        )

    def evaluate_context_degradation(
        self,
        model_name: str,
        short_prompt_fn: Callable[[], Iterator[str]],
        long_prompt_fn: Callable[[], Iterator[str]],
    ) -> Tuple[BenchmarkMetric, BenchmarkMetric, float]:
        """Compares throughput between 512 and 4096 tokens, returning degradation factor."""
        short_res = self.benchmark_stream(model_name, short_prompt_fn, prompt_token_count=512)
        long_res = self.benchmark_stream(model_name, long_prompt_fn, prompt_token_count=4096)

        # Degradation factor: long_tps / short_tps (1.0 = identical speed)
        ratio = (long_res.tokens_per_second / short_res.tokens_per_second) if short_res.tokens_per_second > 0 else 1.0
        score = round(min(ratio, 1.0), 3)

        long_res.context_degradation_score = score
        return short_res, long_res, score


# Global singletons
_GLOBAL_OFFLINE_POLICY: Optional[OfflineEnforcementPolicy] = None
_GLOBAL_MODEL_HARNESS: Optional[ModelBenchmarkHarness] = None

def get_offline_policy() -> OfflineEnforcementPolicy:
    global _GLOBAL_OFFLINE_POLICY
    if _GLOBAL_OFFLINE_POLICY is None:
        _GLOBAL_OFFLINE_POLICY = OfflineEnforcementPolicy()
    return _GLOBAL_OFFLINE_POLICY

def get_model_benchmark_harness() -> ModelBenchmarkHarness:
    global _GLOBAL_MODEL_HARNESS
    if _GLOBAL_MODEL_HARNESS is None:
        _GLOBAL_MODEL_HARNESS = ModelBenchmarkHarness(get_offline_policy())
    return _GLOBAL_MODEL_HARNESS
