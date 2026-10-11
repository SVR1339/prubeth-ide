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
    """Communicates with local Model Context Protocol servers over standard I/O (JSON-RPC 2.0).
    Supports standard LSP/MCP Content-Length header framing alongside newline-delimited JSON.
    """

    def __init__(
        self,
        command: str,
        args: Optional[List[str]] = None,
        cwd: Optional[Path] = None,
        framing: str = "content-length"
    ):
        self.command = command
        self.args = args or []
        self.cwd = cwd
        self.framing = framing  # "content-length" or "newline"
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
                cwd=str(self.cwd) if self.cwd else None,
                bufsize=0
            )
            # Send MCP initialize
            init_payload = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "SUKHI IDE — Horizon Edition", "version": "3.0.0"}
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

    def _format_message(self, payload: Dict[str, Any]) -> bytes:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if self.framing == "content-length":
            header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
            return header + data
        else:
            return data + b"\n"

    def _send_request(self, payload: Dict[str, Any], timeout: int = 10) -> Optional[Dict[str, Any]]:
        if not self.process or self.process.poll() is not None:
            return None

        raw = self._format_message(payload)
        try:
            self.process.stdin.write(raw)
            self.process.stdin.flush()
        except Exception:
            return None

        start_time = time.time()
        stdout = self.process.stdout
        while time.time() - start_time < timeout:
            if not self.process or self.process.poll() is not None:
                break

            line = stdout.readline()
            if not line:
                time.sleep(0.02)
                continue

            line_str = line.decode("utf-8", errors="replace").strip()
            if not line_str:
                continue

            # Check 1: Content-Length header framing
            if line_str.lower().startswith("content-length:"):
                try:
                    content_length = int(line_str.split(":", 1)[1].strip())
                    # Read remaining headers until empty line
                    while True:
                        hdr = stdout.readline()
                        if not hdr or not hdr.decode("utf-8", errors="replace").strip():
                            break
                    body_bytes = stdout.read(content_length)
                    return json.loads(body_bytes.decode("utf-8", errors="replace"))
                except Exception:
                    pass

            # Check 2: Direct line-delimited JSON
            elif line_str.startswith("{") and line_str.endswith("}"):
                try:
                    return json.loads(line_str)
                except Exception:
                    pass

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
