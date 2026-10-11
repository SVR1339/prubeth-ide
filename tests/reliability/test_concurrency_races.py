"""PRUBETH IDE - Concurrency, Race Condition & Deadlock Chaos Tests
================================================================
Exercises multi-threaded event bus publication, secret redaction under load,
command registry concurrency, and compatibility broker thread safety.
"""

import concurrent.futures
import time
import pytest
from tests.reliability.helpers.crash_harness import timed_operation
from core.event_bus import EventBus, EventChannel, EventSeverity
from core.command_registry import CommandRegistry, Command, CommandRiskLevel
from core.future_compat import CompatibilityBroker, IComputeProviderV1, SemanticContractVersion


def test_concurrent_event_bus_publishing_and_redaction():
    """EventBus must handle concurrent event streams with deterministic secret redaction."""
    bus = EventBus()
    received = []
    bus.subscribe(EventChannel.SECURITY, lambda ev: received.append(ev))

    def publish_worker(idx: int):
        # Event with sensitive token that must be redacted
        payload = {"token": f"sk-secretkey12345678901234567890_{idx}", "data": f"packet_{idx}"}
        bus.publish(
            channel=EventChannel.SECURITY,
            source=f"source_{idx}",
            payload=payload,
            severity=EventSeverity.INFO,
        )

    with timed_operation(4.0):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(publish_worker, i) for i in range(40)]
            for f in concurrent.futures.as_completed(futures):
                f.result()

    # Verify all 40 events received safely without lock contention
    assert len(received) == 40
    # Verify secret redaction was applied
    for ev in received:
        assert "[REDACTED" in ev.payload["token"]
        assert "packet_" in ev.payload["data"]


def test_concurrent_command_registry_execution():
    """CommandRegistry must execute and record audit entries safely across concurrent callers."""
    registry = CommandRegistry()
    registry.register(Command(
        command_id="test.compute_hash",
        title="Compute Hash",
        category="utility",
        handler=lambda text: f"hash_{len(text)}",
        risk_level=CommandRiskLevel.READ_ONLY,
    ))

    def exec_worker(idx: int):
        return registry.execute("test.compute_hash", f"payload_string_{idx}")

    with timed_operation(4.0):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(exec_worker, i) for i in range(30)]
            results = [f.result() for f in futures]

    assert len(results) == 30
    history = registry.get_history(limit=50)
    assert len(history) >= 30
    assert all(h.success for h in history)


def test_concurrent_future_compatibility_broker():
    """CompatibilityBroker must register and negotiate providers safely under concurrency."""
    broker = CompatibilityBroker()

    class DummyProvider(IComputeProviderV1):
        @property
        def contract_version(self) -> SemanticContractVersion:
            return SemanticContractVersion.V1_0

        def generate_completion(self, prompt: str, **kwargs) -> str:
            return f"Echo: {prompt}"

    def register_and_negotiate(idx: int):
        p_id = f"dummy_{idx}"
        broker.register_provider(p_id, "compute", DummyProvider())
        p = broker.negotiate_compute_provider(preferred_id=p_id)
        return p.generate_completion(f"call_{idx}")

    with timed_operation(4.0):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(register_and_negotiate, i) for i in range(20)]
            results = [f.result() for f in futures]

    assert len(results) == 20
    assert all(r.startswith("Echo: call_") for r in results)
