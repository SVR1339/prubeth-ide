"""Tests for PRUBETH IDE Model Laboratory & Offline Policy Guard (core/model_lab.py)
"""

import socket
import pytest
from core.model_lab import (
    OfflinePolicyMode,
    AirGapViolationError,
    OfflineEnforcementPolicy,
    ModelBenchmarkHarness,
    BenchmarkMetric,
)


def test_offline_enforcement_policy_strict_airgap():
    policy = OfflineEnforcementPolicy(mode=OfflinePolicyMode.STRICT_AIRGAP)

    # Allowed destinations
    assert policy.check_and_audit("127.0.0.1", 11434, "ollama_client")
    assert policy.check_and_audit("localhost", 8080, "llamacpp_client")
    assert policy.check_and_audit("::1", 1234, "lmstudio_client")

    # Blocked destinations
    with pytest.raises(AirGapViolationError):
        policy.check_and_audit("api.openai.com", 443, "cloud_client")

    with pytest.raises(AirGapViolationError):
        policy.check_and_audit("93.184.216.34", 80, "external_probe")

    audit_log = policy.get_audit_log()
    assert len(audit_log) == 5
    assert audit_log[0].allowed is True
    assert audit_log[3].allowed is False
    assert audit_log[3].target_host == "api.openai.com"


def test_offline_enforcement_policy_audit_mode():
    policy = OfflineEnforcementPolicy(mode=OfflinePolicyMode.AUDIT_ONLY)

    # In audit mode, external connection does not raise, but records allowed=True
    assert policy.check_and_audit("api.anthropic.com", 443, "test_caller") is True
    assert len(policy.get_audit_log()) == 1


def test_offline_guard_socket_interception():
    policy = OfflineEnforcementPolicy(mode=OfflinePolicyMode.STRICT_AIRGAP)

    with policy.strict_offline_guard():
        # Connecting to external host must trigger AirGapViolationError
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with pytest.raises(AirGapViolationError):
                s.connect(("8.8.8.8", 53))
        finally:
            s.close()


def test_model_benchmark_harness():
    harness = ModelBenchmarkHarness()

    def mock_stream():
        import time
        time.sleep(0.01)  # Simulate initial latency
        for word in ["The", "quick", "brown", "fox", "jumps"]:
            time.sleep(0.005)
            yield word

    metric = harness.benchmark_stream("test-qwen2.5:1.5b", mock_stream, prompt_token_count=100)

    assert metric.model_name == "test-qwen2.5:1.5b"
    assert metric.first_token_latency_ms > 0
    assert metric.tokens_per_second > 0
    assert metric.completion_tokens == 5
    assert metric.prompt_tokens == 100


def test_context_degradation_evaluation():
    harness = ModelBenchmarkHarness()

    def short_stream():
        import time
        for i in range(10):
            time.sleep(0.002)
            yield f"token_{i}"

    def long_stream():
        import time
        for i in range(10):
            time.sleep(0.003)
            yield f"token_{i}"

    short_res, long_res, score = harness.evaluate_context_degradation(
        "redsage-8b:latest", short_stream, long_stream
    )

    assert 0.0 < score <= 1.0
    assert long_res.context_degradation_score == score
