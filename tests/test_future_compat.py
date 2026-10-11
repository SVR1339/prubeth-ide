"""Tests for PRUBETH IDE Future Compatibility Layer (core/future_compat.py)
"""

import pytest
from core.future_compat import (
    SemanticContractVersion,
    ComputeCapability,
    StorageCapability,
    IComputeProviderV1,
    IComputeProviderV2,
    IStorageEngineV1,
    IStorageEngineV2,
    V1ToV2ComputeAdapter,
    V1ToV2StorageAdapter,
    CompatibilityBroker,
    get_compatibility_broker,
)


class MockV1ComputeProvider(IComputeProviderV1):
    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V1_0

    def generate_completion(self, prompt: str, **kwargs) -> str:
        return f"Echo V1: {prompt}"


class MockV2ComputeProvider(IComputeProviderV2):
    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V2_0

    def generate_completion(self, prompt: str, **kwargs) -> str:
        return f"Echo V2: {prompt}"

    def stream_completion(self, prompt: str, **kwargs):
        for token in ["Echo", " ", "V2:", " ", prompt]:
            yield token

    def embed_text(self, text: str, **kwargs):
        return [0.1, 0.2, 0.3, 0.4]


class MockV1StorageEngine(IStorageEngineV1):
    def __init__(self):
        self._store = {}

    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V1_0

    def get_item(self, key: str):
        return self._store.get(key)

    def set_item(self, key: str, value):
        self._store[key] = value

    def delete_item(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def list_keys(self, prefix: str = ""):
        return [k for k in self._store if k.startswith(prefix)]


def test_semantic_version_compatibility():
    v1 = SemanticContractVersion.V1_0
    v2 = SemanticContractVersion.V2_0
    v3 = SemanticContractVersion.V3_0

    assert v1.is_compatible_with(v1)
    assert v2.is_compatible_with(v1)
    assert v3.is_compatible_with(v2)
    assert not v1.is_compatible_with(v2)


def test_v1_to_v2_compute_adapter():
    v1_prov = MockV1ComputeProvider()
    adapter = V1ToV2ComputeAdapter(v1_prov, chunk_size=5)

    assert adapter.contract_version == SemanticContractVersion.V2_0
    assert adapter.generate_completion("hello") == "Echo V1: hello"

    # Streaming test
    tokens = list(adapter.stream_completion("test"))
    assert "".join(tokens) == "Echo V1: test"

    # Embedding fallback
    embed = adapter.embed_text("test")
    assert isinstance(embed, list)
    assert len(embed) == 16


def test_v1_to_v2_storage_adapter():
    v1_store = MockV1StorageEngine()
    v1_store.set_item("doc1", {"type": "report", "val": 10})
    v1_store.set_item("doc2", {"type": "log", "val": 20})

    adapter = V1ToV2StorageAdapter(v1_store)
    assert adapter.contract_version == SemanticContractVersion.V2_0

    # Query capability
    res = adapter.query({"type": "report"})
    assert len(res) == 1
    assert res[0]["_key"] == "doc1"

    # Batch write
    adapter.batch_write({"doc3": {"type": "report", "val": 30}})
    assert adapter.get_item("doc3")["val"] == 30

    # Snapshot and restore
    assert adapter.create_snapshot("snap1")
    adapter.set_item("doc1", {"type": "modified"})
    assert adapter.get_item("doc1")["type"] == "modified"

    assert adapter.restore_snapshot("snap1")
    assert adapter.get_item("doc1")["type"] == "report"


def test_compatibility_broker_registration_and_negotiation():
    broker = CompatibilityBroker()
    v1_compute = MockV1ComputeProvider()
    v2_compute = MockV2ComputeProvider()

    broker.register_provider("mock_v1", "compute", v1_compute, ComputeCapability.TEXT_COMPLETION.value)
    broker.register_provider("mock_v2", "compute", v2_compute, (ComputeCapability.TEXT_COMPLETION | ComputeCapability.TOKEN_STREAMING).value)

    # Negotiate preferred
    p = broker.negotiate_compute_provider(preferred_id="mock_v2")
    assert isinstance(p, MockV2ComputeProvider)

    # Negotiate elevation of V1
    p_elevated = broker.negotiate_compute_provider(preferred_id="mock_v1", required_version=SemanticContractVersion.V2_0)
    assert isinstance(p_elevated, V1ToV2ComputeAdapter)

    # Compatibility matrix inspection
    matrix = broker.get_compatibility_matrix()
    assert matrix["total_registered"] == 2
    assert "compute" in matrix["categories"]
