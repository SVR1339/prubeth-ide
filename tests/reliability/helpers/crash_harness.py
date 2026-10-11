"""PRUBETH IDE - Reliability & Chaos Engineering Test Harness
===========================================================
Provides disposable isolated sandboxes, fault injectors, mock error-prone
inference endpoints, leak detectors, and strict operation timeouts.
"""

from __future__ import annotations

import contextlib
import enum
import json
import logging
import os
import shutil
import stat
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterator, List, Optional, Sequence, Tuple, Union

logger = logging.getLogger(__name__)


# ============================================================================
# Fault Types for Model Inferences & Network
# ============================================================================

class ModelFaultType(str, enum.Enum):
    NONE = "NONE"
    TIMEOUT = "TIMEOUT"
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    RATE_LIMITED_429 = "RATE_LIMITED_429"
    AUTH_ERROR_401 = "AUTH_ERROR_401"
    INTERNAL_SERVER_ERROR_500 = "INTERNAL_SERVER_ERROR_500"
    STREAM_DROP_MIDWAY = "STREAM_DROP_MIDWAY"
    MALFORMED_JSON = "MALFORMED_JSON"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    SLOW_FIRST_TOKEN = "SLOW_FIRST_TOKEN"


class MockFaultyModelProvider:
    """Mock model provider capable of injecting controllable failure modes."""

    def __init__(self, fault: ModelFaultType = ModelFaultType.NONE, delay_seconds: float = 0.0) -> None:
        self.fault = fault
        self.delay_seconds = delay_seconds
        self.call_count = 0

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self.call_count += 1
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)

        if self.fault == ModelFaultType.TIMEOUT:
            raise TimeoutError("Inference request timed out after 30.0s")
        elif self.fault == ModelFaultType.CONNECTION_REFUSED:
            raise ConnectionRefusedError("Failed to connect to local Ollama server at 127.0.0.1:11434")
        elif self.fault == ModelFaultType.RATE_LIMITED_429:
            raise RuntimeError("HTTP 429: Too Many Requests - rate limit exceeded")
        elif self.fault == ModelFaultType.AUTH_ERROR_401:
            raise PermissionError("HTTP 401: Unauthorized - invalid or expired API key")
        elif self.fault == ModelFaultType.INTERNAL_SERVER_ERROR_500:
            raise RuntimeError("HTTP 500: Internal Server Error in backend runner")
        elif self.fault == ModelFaultType.MALFORMED_JSON:
            return '{"status": "partial", "payload": [1, 2, '  # Incomplete JSON
        elif self.fault == ModelFaultType.EMPTY_RESPONSE:
            return ""

        return f"Deterministic Mock Response for: {prompt[:30]}"

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        self.call_count += 1
        if self.fault == ModelFaultType.SLOW_FIRST_TOKEN:
            time.sleep(0.08)

        tokens = ["Thought: ", "Analyzing ", "user ", "query... ", "Response: ", "Done."]
        for idx, tok in enumerate(tokens):
            if self.fault == ModelFaultType.STREAM_DROP_MIDWAY and idx == 3:
                raise ConnectionResetError("Connection closed abruptly by remote inference peer midway through stream")
            yield tok


# ============================================================================
# Disposable Workspace
# ============================================================================

class DisposableWorkspace:
    """Context manager for isolated sandboxed test workspaces."""

    def __init__(self, populate_files: bool = True) -> None:
        self._temp_dir: Optional[str] = None
        self._populate = populate_files
        self.path: Path = Path(".")

    def __enter__(self) -> Path:
        self._temp_dir = tempfile.mkdtemp(prefix="prubeth_chaos_ws_")
        self.path = Path(self._temp_dir).resolve()

        if self._populate:
            (self.path / "src").mkdir(parents=True, exist_ok=True)
            (self.path / "tests").mkdir(parents=True, exist_ok=True)
            (self.path / "main.py").write_text("def main():\n    print('Hello PRUBETH')\n\nif __name__ == '__main__':\n    main()\n", encoding="utf-8")
            (self.path / "src" / "utils.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            (self.path / "requirements.txt").write_text("requests==2.31.0\nurllib3==2.0.7\n", encoding="utf-8")
            (self.path / "package.json").write_text('{"name": "test-pkg", "version": "1.0.0"}', encoding="utf-8")

        return self.path

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                # Clear read-only flags in case tests set them
                for root, dirs, files in os.walk(self._temp_dir):
                    for fname in files:
                        p = Path(root) / fname
                        try:
                            os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
                        except Exception:
                            pass
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed removing disposable workspace {self._temp_dir}: {e}")


# ============================================================================
# Isolated Configuration Harness
# ============================================================================

class IsolatedConfigHarness:
    """Isolates settings and credential stores to temporary directories."""

    def __init__(self) -> None:
        self._temp_dir: Optional[str] = None
        self.config_dir: Path = Path(".")
        self.settings_file: Path = Path(".")

    def __enter__(self) -> IsolatedConfigHarness:
        self._temp_dir = tempfile.mkdtemp(prefix="prubeth_chaos_cfg_")
        self.config_dir = Path(self._temp_dir).resolve()
        self.settings_file = self.config_dir / "settings.json"

        # Default clean config
        initial = {
            "schema_version": 1,
            "provider": "Ollama",
            "model": "qwen2.5:1.5b",
            "ollama_url": "http://127.0.0.1:11434",
            "unrestricted_mode": True,
            "theme": "Obsidian Slate",
        }
        self.settings_file.write_text(json.dumps(initial, indent=2), encoding="utf-8")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)


# ============================================================================
# Fault Injector
# ============================================================================

class FaultInjector:
    """Injects low-level filesystem, data corruption, and permission faults."""

    @staticmethod
    def corrupt_json_file(file_path: Union[str, Path]) -> None:
        """Truncates file to create invalid, unparseable JSON."""
        p = Path(file_path)
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            # Truncate at half length to break braces
            corrupted = text[: max(1, len(text) // 2)]
            p.write_text(corrupted, encoding="utf-8")

    @staticmethod
    def inject_invalid_bytes(file_path: Union[str, Path]) -> None:
        """Overwrites file with raw invalid binary bytes."""
        p = Path(file_path)
        p.write_bytes(b"\x00\xFF\xFE\xFD\x80\x81\xFF\xFF\x00")

    @staticmethod
    def make_read_only(file_path: Union[str, Path]) -> None:
        """Removes write permissions on file."""
        p = Path(file_path)
        os.chmod(p, stat.S_IREAD)

    @staticmethod
    def restore_writable(file_path: Union[str, Path]) -> None:
        """Restores read and write permissions."""
        p = Path(file_path)
        os.chmod(p, stat.S_IWRITE | stat.S_IREAD)


# ============================================================================
# Resource Leak Detector
# ============================================================================

class ResourceLeakDetector:
    """Tracks thread and process counts to ensure zero zombie leaks."""

    def __init__(self) -> None:
        self.initial_threads: List[str] = []

    def snapshot(self) -> None:
        self.initial_threads = [t.name for t in threading.enumerate() if t.is_alive()]

    def verify_no_thread_leaks(self, allowed_new_prefixes: Sequence[str] = ("Dummy-",)) -> bool:
        current_threads = [t.name for t in threading.enumerate() if t.is_alive()]
        leaked = []
        for name in current_threads:
            if name not in self.initial_threads:
                if not any(name.startswith(p) for p in allowed_new_prefixes):
                    leaked.append(name)
        if leaked:
            logger.warning(f"Detected uncollected leaked background threads: {leaked}")
            return False
        return True


# ============================================================================
# Bounded Operation Timer
# ============================================================================

@contextlib.contextmanager
def timed_operation(max_allowed_seconds: float = 5.0) -> Iterator[None]:
    """Guarantees an operation completes within a safe wall-clock threshold."""
    start = time.perf_counter()
    yield
    duration = time.perf_counter() - start
    if duration > max_allowed_seconds:
        raise TimeoutError(f"Operation exceeded safety deadline of {max_allowed_seconds}s (took {duration:.2f}s)")
