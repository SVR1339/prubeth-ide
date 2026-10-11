"""PRUBETH IDE - Future Compatibility Layer (Century-Scale Extensible Architecture)
================================================================================
Implements versioned interface contracts, capability negotiation, and adaptive
wrappers ensuring compute, storage, indexing, and scheduling engines can be
evolved, replaced, or migrated across decades without modifying IDE UI layers.

Principles:
1. Stable interfaces, replaceable implementations.
2. Explicit semantic versioning for all component contracts.
3. Backward-compatible automatic adapter synthesis.
4. Capability-based discovery rather than hardcoded vendor assumptions.
"""

from __future__ import annotations

import abc
import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, Iterator, List, Optional, Sequence, Tuple, Type, Union

logger = logging.getLogger(__name__)


# ============================================================================
# Version & Capability Definitions
# ============================================================================

class SemanticContractVersion(enum.Enum):
    V1_0 = "1.0.0"
    V2_0 = "2.0.0"
    V3_0 = "3.0.0"

    def is_compatible_with(self, target: SemanticContractVersion) -> bool:
        """Determines major-version compatibility."""
        my_major = self.value.split(".")[0]
        target_major = target.value.split(".")[0]
        return my_major == target_major or (int(my_major) >= int(target_major))


class ComputeCapability(enum.Flag):
    NONE = 0
    TEXT_COMPLETION = 1 << 0
    TOKEN_STREAMING = 1 << 1
    EMBEDDINGS = 1 << 2
    LAYER_OFFLOAD = 1 << 3
    QUANTIZATION = 1 << 4
    STRUCTURED_OUTPUT = 1 << 5
    HARDWARE_TELEMETRY = 1 << 6


class StorageCapability(enum.Flag):
    NONE = 0
    KEY_VALUE = 1 << 0
    TRANSACTIONAL = 1 << 1
    STRUCTURED_QUERY = 1 << 2
    ATOMIC_SNAPSHOT = 1 << 3
    VECTOR_SEARCH = 1 << 4
    TIME_SERIES = 1 << 5


# ============================================================================
# Compute Provider Contracts (V1, V2, V3)
# ============================================================================

class IComputeProviderV1(abc.ABC):
    """V1 Compute Provider: Synchronous text completion."""

    @property
    @abc.abstractmethod
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V1_0

    @abc.abstractmethod
    def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        """Generates complete text response for a given prompt."""
        pass


class IComputeProviderV2(IComputeProviderV1):
    """V2 Compute Provider: Adds token streaming and vector embeddings."""

    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V2_0

    @abc.abstractmethod
    def stream_completion(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Streams completion tokens lazily."""
        pass

    @abc.abstractmethod
    def embed_text(self, text: str, **kwargs: Any) -> List[float]:
        """Generates embedding vector for input text."""
        pass


class IComputeProviderV3(IComputeProviderV2):
    """V3 Compute Provider: Heterogeneous compute, quantization & layer offloading."""

    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V3_0

    @abc.abstractmethod
    def get_hardware_telemetry(self) -> Dict[str, Any]:
        """Returns compute unit, VRAM, RAM, and temperature telemetry."""
        pass

    @abc.abstractmethod
    def configure_offload(self, gpu_device_id: int, num_layers: int) -> bool:
        """Configures GPU layer offload count."""
        pass

    @abc.abstractmethod
    def quantize_weights(self, source_model: str, target_quant: str) -> Dict[str, Any]:
        """Profiles or executes weight quantization (e.g., Q4_K_M)."""
        pass


# ============================================================================
# Storage Engine Contracts (V1, V2)
# ============================================================================

class IStorageEngineV1(abc.ABC):
    """V1 Storage Engine: Basic key-value persistence."""

    @property
    @abc.abstractmethod
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V1_0

    @abc.abstractmethod
    def get_item(self, key: str) -> Optional[Any]:
        pass

    @abc.abstractmethod
    def set_item(self, key: str, value: Any) -> None:
        pass

    @abc.abstractmethod
    def delete_item(self, key: str) -> bool:
        pass

    @abc.abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        pass


class IStorageEngineV2(IStorageEngineV1):
    """V2 Storage Engine: Filter queries, batch operations & snapshots."""

    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V2_0

    @abc.abstractmethod
    def query(self, filter_spec: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def batch_write(self, items: Dict[str, Any]) -> int:
        pass

    @abc.abstractmethod
    def create_snapshot(self, snapshot_id: str) -> bool:
        pass

    @abc.abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> bool:
        pass


# ============================================================================
# Scheduler Engine Contracts (V1, V2)
# ============================================================================

class ISchedulerEngineV1(abc.ABC):
    """V1 Scheduler: Simple task queuing and execution."""

    @property
    @abc.abstractmethod
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V1_0

    @abc.abstractmethod
    def submit(self, task_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """Submits task, returns task_id."""
        pass

    @abc.abstractmethod
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """Returns task execution status dict."""
        pass


class ISchedulerEngineV2(ISchedulerEngineV1):
    """V2 Scheduler: Bounded concurrency, priority queuing & cancellation."""

    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V2_0

    @abc.abstractmethod
    def submit_priority(self, task_name: str, priority: int, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        pass

    @abc.abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        pass

    @abc.abstractmethod
    def get_worker_utilization(self) -> Dict[str, Any]:
        pass


# ============================================================================
# Indexer Engine Contract (V1)
# ============================================================================

class IIndexerEngineV1(abc.ABC):
    """V1 Codebase Indexer: Lexical and structural symbol indexing."""

    @property
    @abc.abstractmethod
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V1_0

    @abc.abstractmethod
    def index_document(self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        pass

    @abc.abstractmethod
    def search_symbols(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def clear_index(self) -> None:
        pass


# ============================================================================
# Backward Compatibility Adapters (Synthesizers)
# ============================================================================

class V1ToV2ComputeAdapter(IComputeProviderV2):
    """Wraps a legacy V1 provider to satisfy V2 requests gracefully."""

    def __init__(self, v1_provider: IComputeProviderV1, chunk_size: int = 40):
        self._provider = v1_provider
        self._chunk_size = chunk_size

    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V2_0

    def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        return self._provider.generate_completion(prompt, **kwargs)

    def stream_completion(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        full_text = self.generate_completion(prompt, **kwargs)
        for i in range(0, len(full_text), self._chunk_size):
            yield full_text[i:i + self._chunk_size]

    def embed_text(self, text: str, **kwargs: Any) -> List[float]:
        # Fallback deterministic pseudo-embedding based on hash buckets
        # for air-gapped/offline systems lacking native vector models
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return [(b / 255.0) * 2.0 - 1.0 for b in h[:16]]


class V1ToV2StorageAdapter(IStorageEngineV2):
    """Wraps a V1 Key-Value store to satisfy V2 query & snapshot requests."""

    def __init__(self, v1_storage: IStorageEngineV1):
        self._storage = v1_storage
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    @property
    def contract_version(self) -> SemanticContractVersion:
        return SemanticContractVersion.V2_0

    def get_item(self, key: str) -> Optional[Any]:
        return self._storage.get_item(key)

    def set_item(self, key: str, value: Any) -> None:
        self._storage.set_item(key, value)

    def delete_item(self, key: str) -> bool:
        return self._storage.delete_item(key)

    def list_keys(self, prefix: str = "") -> List[str]:
        return self._storage.list_keys(prefix)

    def query(self, filter_spec: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for k in self.list_keys():
            val = self.get_item(k)
            if isinstance(val, dict):
                matches = True
                for fk, fv in filter_spec.items():
                    if val.get(fk) != fv:
                        matches = False
                        break
                if matches:
                    results.append({"_key": k, **val})
                    if len(results) >= limit:
                        break
        return results

    def batch_write(self, items: Dict[str, Any]) -> int:
        count = 0
        for k, v in items.items():
            self.set_item(k, v)
            count += 1
        return count

    def create_snapshot(self, snapshot_id: str) -> bool:
        dump = {}
        for k in self.list_keys():
            dump[k] = self.get_item(k)
        self._snapshots[snapshot_id] = dump
        return True

    def restore_snapshot(self, snapshot_id: str) -> bool:
        if snapshot_id not in self._snapshots:
            return False
        for k, v in self._snapshots[snapshot_id].items():
            self.set_item(k, v)
        return True


# ============================================================================
# Compatibility Broker
# ============================================================================

@dataclass
class ProviderDescriptor:
    provider_id: str
    category: str  # "compute", "storage", "scheduler", "indexer"
    contract_version: SemanticContractVersion
    capabilities: int
    instance: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


class CompatibilityBroker:
    """Universal registry and contract negotiation broker.
    
    Permits registering components of any contract version and negotiating
    the best matching adapter for callers without coupling to concrete classes.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, ProviderDescriptor] = {}

    def register_provider(
        self,
        provider_id: str,
        category: str,
        instance: Any,
        capabilities: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        version = getattr(instance, "contract_version", SemanticContractVersion.V1_0)
        self._registry[provider_id] = ProviderDescriptor(
            provider_id=provider_id,
            category=category,
            contract_version=version,
            capabilities=capabilities,
            instance=instance,
            metadata=metadata or {},
        )
        logger.info(f"Registered future-compatible provider '{provider_id}' ({category} {version.value})")

    def unregister_provider(self, provider_id: str) -> bool:
        return self._registry.pop(provider_id, None) is not None

    def get_descriptor(self, provider_id: str) -> Optional[ProviderDescriptor]:
        return self._registry.get(provider_id)

    def list_providers(self, category: Optional[str] = None) -> List[ProviderDescriptor]:
        if category:
            return [d for d in self._registry.values() if d.category == category]
        return list(self._registry.values())

    def negotiate_compute_provider(
        self,
        preferred_id: Optional[str] = None,
        required_version: SemanticContractVersion = SemanticContractVersion.V1_0,
    ) -> Optional[IComputeProviderV1]:
        """Negotiates compute provider, elevating V1 -> V2 via adapter if needed."""
        descriptors = self.list_providers("compute")
        if not descriptors:
            return None

        # Try preferred ID first
        target_desc = None
        if preferred_id and preferred_id in self._registry:
            cand = self._registry[preferred_id]
            if cand.category == "compute":
                target_desc = cand

        if not target_desc:
            # Pick highest version available
            descriptors.sort(key=lambda d: d.contract_version.value, reverse=True)
            target_desc = descriptors[0]

        inst = target_desc.instance

        # Check version match or elevation
        if required_version == SemanticContractVersion.V2_0 and isinstance(inst, IComputeProviderV2):
            return inst
        elif required_version == SemanticContractVersion.V2_0 and isinstance(inst, IComputeProviderV1):
            logger.info(f"Elevating compute provider '{target_desc.provider_id}' V1 -> V2 via adapter")
            return V1ToV2ComputeAdapter(inst)
        elif required_version == SemanticContractVersion.V1_0 and isinstance(inst, IComputeProviderV1):
            return inst

        return inst

    def negotiate_storage_engine(
        self,
        preferred_id: Optional[str] = None,
        required_version: SemanticContractVersion = SemanticContractVersion.V1_0,
    ) -> Optional[IStorageEngineV1]:
        """Negotiates storage engine, elevating V1 -> V2 via adapter if needed."""
        descriptors = self.list_providers("storage")
        if not descriptors:
            return None

        target_desc = None
        if preferred_id and preferred_id in self._registry:
            cand = self._registry[preferred_id]
            if cand.category == "storage":
                target_desc = cand

        if not target_desc:
            descriptors.sort(key=lambda d: d.contract_version.value, reverse=True)
            target_desc = descriptors[0]

        inst = target_desc.instance

        if required_version == SemanticContractVersion.V2_0 and isinstance(inst, IStorageEngineV2):
            return inst
        elif required_version == SemanticContractVersion.V2_0 and isinstance(inst, IStorageEngineV1):
            logger.info(f"Elevating storage engine '{target_desc.provider_id}' V1 -> V2 via adapter")
            return V1ToV2StorageAdapter(inst)
        elif required_version == SemanticContractVersion.V1_0 and isinstance(inst, IStorageEngineV1):
            return inst

        return inst

    def get_compatibility_matrix(self) -> Dict[str, Any]:
        """Generates comprehensive diagnostic compatibility report."""
        categories: Dict[str, List[Dict[str, Any]]] = {}
        for desc in self._registry.values():
            categories.setdefault(desc.category, []).append({
                "provider_id": desc.provider_id,
                "version": desc.contract_version.value,
                "capabilities": desc.capabilities,
                "metadata": desc.metadata,
            })
        return {
            "total_registered": len(self._registry),
            "categories": categories,
        }


# Global broker singleton
_GLOBAL_BROKER: Optional[CompatibilityBroker] = None

def get_compatibility_broker() -> CompatibilityBroker:
    global _GLOBAL_BROKER
    if _GLOBAL_BROKER is None:
        _GLOBAL_BROKER = CompatibilityBroker()
    return _GLOBAL_BROKER
