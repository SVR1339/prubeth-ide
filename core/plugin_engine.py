"""
SO NAIVE IDE — Real MCP Protocol Transport & Plugin Manifest Engine
Provides JSON-RPC 2.0 stdio protocol transport for Model Context Protocol servers
and strict extension manifest validation.
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class PluginManifestValidationError(ValueError):
    """Raised when an extension manifest fails strict schema validation."""
    pass


class PluginManifestValidator:
    """Validates extension manifests against strict structural and permission requirements."""

    REQUIRED_FIELDS = ["id", "name", "version", "publisher", "description", "permissions"]

    VALID_PERMISSIONS = {
        "workspace:read",
        "workspace:write",
        "command:execute",
        "network:connect",
        "credentials:proxy",
        "settings:read"
    }

    @classmethod
    def validate(cls, manifest_dict: Dict[str, Any]) -> bool:
        for f in cls.REQUIRED_FIELDS:
            if f not in manifest_dict or not manifest_dict[f]:
                raise PluginManifestValidationError(f"Missing required manifest field: '{f}'")

        perms = manifest_dict.get("permissions", [])
        if not isinstance(perms, list):
            raise PluginManifestValidationError("'permissions' must be a list of permission tokens")

        for p in perms:
            if p not in cls.VALID_PERMISSIONS:
                raise PluginManifestValidationError(f"Unrecognized or excessively privileged permission: '{p}'")

        return True


class RealMCPStdioClient:
    """Communicates with local Model Context Protocol servers over standard I/O (JSON-RPC 2.0)."""

    def __init__(self, command: str, args: Optional[List[str]] = None, cwd: Optional[Path] = None):
        self.command = command
        self.args = args or []
        self.cwd = cwd
        self.process: Optional[subprocess.Popen] = None
        self._req_id = 0

    def start(self, timeout_seconds: int = 10) -> bool:
        cmd = [self.command] + self.args
        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.cwd) if self.cwd else None,
                bufsize=1
            )
            # Send MCP initialize
            init_payload = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "SO NAIVE IDE", "version": "3.0.0"}
                }
            }
            resp = self._send_request(init_payload, timeout=timeout_seconds)
            return resp is not None and "result" in resp
        except Exception:
            self.stop()
            return False

    def list_tools(self, timeout_seconds: int = 10) -> List[Dict[str, Any]]:
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {}
        }
        resp = self._send_request(req, timeout=timeout_seconds)
        if resp and "result" in resp:
            return resp["result"].get("tools", [])
        return []

    def call_tool(self, name: str, arguments: Dict[str, Any], timeout_seconds: int = 30) -> Dict[str, Any]:
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        resp = self._send_request(req, timeout=timeout_seconds)
        if resp and "result" in resp:
            return resp["result"]
        elif resp and "error" in resp:
            raise RuntimeError(f"MCP Server Error: {resp['error']}")
        return {"content": [{"type": "text", "text": "No response received from MCP server."}]}

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _send_request(self, payload: Dict[str, Any], timeout: int = 10) -> Optional[Dict[str, Any]]:
        if not self.process or self.process.poll() is not None:
            return None
        line = json.dumps(payload) + "\n"
        self.process.stdin.write(line)
        self.process.stdin.flush()

        # Read JSON-RPC response line
        # Non-blocking or timed read
        start_time = time.time()
        while time.time() - start_time < timeout:
            raw_line = self.process.stdout.readline()
            if raw_line:
                raw_line = raw_line.strip()
                if raw_line.startswith("{") and raw_line.endswith("}"):
                    try:
                        return json.loads(raw_line)
                    except Exception:
                        pass
            time.sleep(0.05)
        return None

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
