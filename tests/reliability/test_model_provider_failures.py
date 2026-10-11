"""PRUBETH IDE - Model & AI Provider Failure Chaos Tests
======================================================
Exercises provider timeout handling, socket drop during token streaming,
rate limits (429), server errors (500), malformed output, and air-gap enforcement.
"""

import pytest
from tests.reliability.helpers.crash_harness import (
    MockFaultyModelProvider,
    ModelFaultType,
    timed_operation,
)
from core.model_lab import (
    OfflinePolicyMode,
    AirGapViolationError,
    OfflineEnforcementPolicy,
    ModelBenchmarkHarness,
)


def test_provider_connection_refused_handling():
    """Provider failure when local Ollama is offline must raise ConnectionRefusedError cleanly."""
    provider = MockFaultyModelProvider(fault=ModelFaultType.CONNECTION_REFUSED)

    with pytest.raises(ConnectionRefusedError) as exc_info:
        provider.generate("Summarize codebase")

    assert "Failed to connect" in str(exc_info.value)
    assert provider.call_count == 1


def test_provider_timeout_handling():
    """Provider timeout must be caught within bounded deadline without freezing."""
    provider = MockFaultyModelProvider(fault=ModelFaultType.TIMEOUT)

    with timed_operation(1.0):
        with pytest.raises(TimeoutError) as exc_info:
            provider.generate("Explain complex architecture")

    assert "timed out" in str(exc_info.value)


def test_stream_interrupted_midway_handling():
    """Socket disconnect midway through streaming must fail gracefully and release resources."""
    provider = MockFaultyModelProvider(fault=ModelFaultType.STREAM_DROP_MIDWAY)
    collected = []

    with pytest.raises(ConnectionResetError) as exc_info:
        for token in provider.stream("Write code"):
            collected.append(token)

    # Partial tokens arrived before connection dropped
    assert len(collected) > 0
    assert "abruptly" in str(exc_info.value)


def test_rate_limit_and_server_error_responses():
    """HTTP 429 and 500 errors must be accurately classified."""
    rate_limited_provider = MockFaultyModelProvider(fault=ModelFaultType.RATE_LIMITED_429)
    with pytest.raises(RuntimeError) as exc_429:
        rate_limited_provider.generate("Test prompt")
    assert "429" in str(exc_429.value)

    err_500_provider = MockFaultyModelProvider(fault=ModelFaultType.INTERNAL_SERVER_ERROR_500)
    with pytest.raises(RuntimeError) as exc_500:
        err_500_provider.generate("Test prompt")
    assert "500" in str(exc_500.value)


def test_airgap_guard_interception_under_external_call():
    """AirGap policy must intercept and prevent external calls under STRICT_AIRGAP."""
    policy = OfflineEnforcementPolicy(mode=OfflinePolicyMode.STRICT_AIRGAP)

    with pytest.raises(AirGapViolationError):
        policy.check_and_audit("external-api.cloudprovider.org", 443, "unvetted_plugin")

    audit = policy.get_audit_log()
    assert len(audit) == 1
    assert audit[0].allowed is False
    assert audit[0].target_host == "external-api.cloudprovider.org"
