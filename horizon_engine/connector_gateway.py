"""
PRUBETH IDE — Universal Connector Gateway
Pillar 2 & Pillar 7: Architecture & Operations Governance

Provides universal connectivity across any external application, software,
local AI runtime (Ollama, LM Studio, vLLM, llama.cpp), cloud endpoints,
developer CLI toolchains (Git, Python, Node, Docker, WSL), and MCP server ecosystems.
"""

from __future__ import annotations

import os
import sys
import json
import shutil
import socket
import urllib.request
import urllib.error
import subprocess
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class ConnectedService:
    """Represents a discovered or connected external software or AI engine."""
    service_id: str
    name: str
    category: str  # local_ai, cloud_ai, cli_tool, mcp_server, ide_bridge
    endpoint_or_path: str
    status: str    # online, offline, available, not_installed
    latency_ms: Optional[float] = None
    version: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectorGateway:
    """Universal hub for probing, connecting, and orchestrating external applications."""

    STANDARD_LOCAL_AI_TARGETS = [
        ("ollama", "Ollama Engine", "http://127.0.0.1:11434", 11434, "/api/tags"),
        ("lmstudio", "LM Studio Server", "http://127.0.0.1:1234", 1234, "/v1/models"),
        ("vllm", "vLLM High-Throughput", "http://127.0.0.1:8000", 8000, "/v1/models"),
        ("llamacpp", "llama.cpp Server", "http://127.0.0.1:8080", 8080, "/health"),
        ("jan", "Jan.ai Desktop Server", "http://127.0.0.1:1337", 1337, "/v1/models"),
        ("textgen", "Text-Gen WebUI", "http://127.0.0.1:5000", 5000, "/v1/models")
    ]

    STANDARD_CLI_TOOLS = [
        ("git", "Git Version Control", "git", ["--version"]),
        ("python", "Python Runtime", sys.executable, ["--version"]),
        ("node", "Node.js JavaScript Engine", "node", ["--version"]),
        ("npm", "Node Package Manager", "npm", ["--version"]),
        ("docker", "Docker Container Engine", "docker", ["--version"]),
        ("powershell", "PowerShell Core", "pwsh" if shutil.which("pwsh") else "powershell", ["-v"]),
        ("wsl", "Windows Subsystem for Linux", "wsl", ["--status"]),
        ("rust", "Rust Compiler (cargo)", "cargo", ["--version"]),
        ("go", "Go Programming Language", "go", ["version"]),
    ]

    @classmethod
    def probe_port(cls, host: str, port: int, timeout: float = 0.4) -> bool:
        """Fast TCP socket probe to verify if a local port is listening."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                return s.connect_ex((host, port)) == 0
        except Exception:
            return False

    @classmethod
    def probe_local_ai_runtimes(cls) -> List[ConnectedService]:
        """Probes all standard local AI endpoints and retrieves their model catalogs."""
        results: List[ConnectedService] = []
        for sid, name, base_url, port, probe_path in cls.STANDARD_LOCAL_AI_TARGETS:
            is_listening = cls.probe_port("127.0.0.1", port)
            if not is_listening:
                results.append(ConnectedService(
                    service_id=sid,
                    name=name,
                    category="local_ai",
                    endpoint_or_path=base_url,
                    status="offline",
                    metadata={"listening": False}
                ))
                continue

            # Query HTTP endpoint for version/models
            status = "online"
            version = "running"
            models: List[str] = []
            try:
                import time
                t0 = time.time()
                req = urllib.request.Request(f"{base_url}{probe_path}", headers={"User-Agent": "PRUBETH-IDE/1.0"})
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    latency = round((time.time() - t0) * 1000, 1)
                    raw = json.loads(resp.read().decode("utf-8"))
                    if "models" in raw and isinstance(raw["models"], list):
                        # Ollama style
                        for m in raw["models"]:
                            models.append(m.get("name", m.get("model", "")))
                    elif "data" in raw and isinstance(raw["data"], list):
                        # OpenAI / LM Studio style
                        for m in raw["data"]:
                            models.append(m.get("id", ""))
            except Exception:
                latency = None

            results.append(ConnectedService(
                service_id=sid,
                name=name,
                category="local_ai",
                endpoint_or_path=base_url,
                status="online",
                latency_ms=latency,
                version=version,
                metadata={"models": models, "listening": True}
            ))
        return results

    @classmethod
    def probe_developer_toolchains(cls) -> List[ConnectedService]:
        """Discovers developer toolchains, compilers, runtimes, and VCS installed on the host."""
        results: List[ConnectedService] = []
        for sid, name, binary, args in cls.STANDARD_CLI_TOOLS:
            path = shutil.which(binary) if binary != sys.executable else binary
            if not path:
                results.append(ConnectedService(
                    service_id=sid,
                    name=name,
                    category="cli_tool",
                    endpoint_or_path="",
                    status="not_installed"
                ))
                continue

            version = ""
            try:
                proc = subprocess.run([path] + args, capture_output=True, text=True, timeout=2)
                if proc.returncode == 0:
                    version = proc.stdout.strip().split("\n")[0]
            except Exception:
                version = "Installed (Query error)"

            results.append(ConnectedService(
                service_id=sid,
                name=name,
                category="cli_tool",
                endpoint_or_path=path,
                status="available",
                version=version
            ))
        return results

    @classmethod
    def test_custom_endpoint(cls, endpoint_url: str, api_key: str = "", timeout: float = 3.0) -> Tuple[bool, str, Optional[float]]:
        """Tests health and measures latency of any user-configured OpenAI-compatible, cloud, or custom URL."""
        import time
        if not endpoint_url.startswith(("http://", "https://")):
            return False, "Endpoint must start with http:// or https://", None

        url = endpoint_url.rstrip("/")
        test_url = f"{url}/models" if not url.endswith("/models") else url
        headers = {"User-Agent": "PRUBETH-IDE/1.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        t0 = time.time()
        try:
            req = urllib.request.Request(test_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                latency = round((time.time() - t0) * 1000, 1)
                return True, f"HTTP {resp.status}: Connected successfully", latency
        except urllib.error.HTTPError as e:
            # 401/403 means endpoint is alive but auth failed
            latency = round((time.time() - t0) * 1000, 1)
            if e.code in (401, 403):
                return False, f"HTTP {e.code}: Authentication failed (check API key)", latency
            return False, f"HTTP {e.code}: {e.reason}", latency
        except Exception as exc:
            return False, f"Connection failed: {str(exc)}", None

    @classmethod
    def full_system_scan(cls) -> Dict[str, Any]:
        """Runs an end-to-end audit of all local AI engines, toolchains, and bridges."""
        local_ai = cls.probe_local_ai_runtimes()
        toolchains = cls.probe_developer_toolchains()

        active_engines = [s for s in local_ai if s.status == "online"]
        installed_tools = [t for t in toolchains if t.status == "available"]

        return {
            "total_local_ai_scanned": len(local_ai),
            "active_local_ai_count": len(active_engines),
            "active_local_ai": [s.name for s in active_engines],
            "total_toolchains_scanned": len(toolchains),
            "available_toolchains_count": len(installed_tools),
            "available_toolchains": [f"{t.name} ({t.version})" for t in installed_tools],
            "services": [asdict(s) for s in (local_ai + toolchains)]
        }
