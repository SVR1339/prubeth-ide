"""
Tests for Gate 4 — MCP Protocol Header Framing:
Tests Content-Length header framing, line framing, auto-detection, and error tolerance.
"""
import sys
import json
import pytest
from pathlib import Path
from core.plugin_engine import RealMCPStdioClient


def test_mcp_client_content_length_framing_roundtrip(tmp_path):
    # Create a mock MCP server script that responds with Content-Length header framing
    server_script = tmp_path / "mock_mcp_server.py"
    server_script.write_text("""
import sys, json

while True:
    line = sys.stdin.buffer.readline()
    if not line:
        break
    line_str = line.decode("ascii", errors="replace").strip()
    if line_str.lower().startswith("content-length:"):
        length = int(line_str.split(":", 1)[1].strip())
        while True:
            hdr = sys.stdin.buffer.readline()
            if hdr in (b"\\r\\n", b"\\n", b""):
                break
        body_raw = sys.stdin.buffer.read(length)
        req = json.loads(body_raw.decode("utf-8"))
        method = req.get("method")
        req_id = req.get("id")

        if method == "initialize":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}}
            }
        elif method == "tools/list":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": [{"name": "echo_tool", "description": "Echoes input"}]}
            }
        elif method == "tools/call":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": "echoed"}]}
            }
        else:
            res = {"jsonrpc": "2.0", "id": req_id, "result": {}}

        payload = json.dumps(res).encode("utf-8")
        header = f"Content-Length: {len(payload)}\\r\\n\\r\\n".encode("ascii")
        sys.stdout.buffer.write(header + payload)
        sys.stdout.buffer.flush()
""", encoding="utf-8")

    client = RealMCPStdioClient(sys.executable, [str(server_script)], framing="content-length")
    try:
        ok = client.start(timeout_seconds=5)
        assert ok is True

        tools = client.list_tools(timeout_seconds=5)
        assert len(tools) == 1
        assert tools[0]["name"] == "echo_tool"

        call_res = client.call_tool("echo_tool", {"msg": "hello"}, timeout_seconds=5)
        assert "content" in call_res
        assert call_res["content"][0]["text"] == "echoed"
    finally:
        client.stop()


def test_mcp_client_newline_delimited_framing(tmp_path):
    # Mock server that responds with raw newline JSON
    server_script = tmp_path / "mock_mcp_newline.py"
    server_script.write_text("""
import sys, json

while True:
    line = sys.stdin.readline()
    if not line:
        break
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        method = req.get("method")
        req_id = req.get("id")
        if method == "initialize":
            res = {"jsonrpc": "2.0", "id": req_id, "result": {"capabilities": {}}}
        elif method == "tools/list":
            res = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [{"name": "line_tool"}]}}
        else:
            res = {"jsonrpc": "2.0", "id": req_id, "result": {}}
        sys.stdout.write(json.dumps(res) + "\\n")
        sys.stdout.flush()
    except Exception:
        pass
""", encoding="utf-8")

    client = RealMCPStdioClient(sys.executable, [str(server_script)], framing="newline")
    try:
        ok = client.start(timeout_seconds=5)
        assert ok is True

        tools = client.list_tools(timeout_seconds=5)
        assert len(tools) == 1
        assert tools[0]["name"] == "line_tool"
    finally:
        client.stop()
