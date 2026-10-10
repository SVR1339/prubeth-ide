"""
Unit and Integration Tests for Language Services Subsystem (LspClient, Protocol Framing, Diagnostics)
"""
import sys
import json
from pathlib import Path
import pytest
from language_services.lsp_client import (
    LspClient, LspDiagnostic, LspLocation, path_to_uri, uri_to_path
)


def test_path_uri_roundtrip(tmp_path):
    test_file = tmp_path / "sample.py"
    test_file.write_text("x = 1\n", encoding="utf-8")

    uri = path_to_uri(test_file)
    assert uri.startswith("file://")
    resolved_path = uri_to_path(uri)
    assert resolved_path.resolve() == test_file.resolve()


def test_lsp_message_framing():
    client = LspClient("dummy_server")
    payload = {"jsonrpc": "2.0", "id": 1, "method": "testMethod", "params": {"key": "value"}}
    raw = client._format_message(payload)

    # Must contain Content-Length header separated by \r\n\r\n
    assert b"Content-Length: " in raw
    assert b"\r\n\r\n" in raw
    header, body = raw.split(b"\r\n\r\n", 1)
    len_val = int(header.split(b": ")[1])
    assert len(body) == len_val
    decoded = json.loads(body.decode("utf-8"))
    assert decoded["id"] == 1
    assert decoded["method"] == "testMethod"


def test_lsp_diagnostics_dispatch():
    client = LspClient("dummy_server")
    test_uri = "file:///workspace/app.py"
    notification = {
        "jsonrpc": "2.0",
        "method": "textDocument/publishDiagnostics",
        "params": {
            "uri": test_uri,
            "diagnostics": [
                {
                    "range": {
                        "start": {"line": 10, "character": 4},
                        "end": {"line": 10, "character": 12}
                    },
                    "severity": 1,
                    "message": "Undefined variable 'foobar'",
                    "source": "pyright"
                }
            ]
        }
    }

    client._handle_incoming_message(notification)
    diags = client._diagnostics.get(test_uri, [])
    assert len(diags) == 1
    d = diags[0]
    assert d.message == "Undefined variable 'foobar'"
    assert d.severity == 1
    assert d.start_line == 10
    assert d.source == "pyright"


def test_lsp_definition_parsing():
    client = LspClient("dummy_server")
    msg_id = client._next_id()

    # Emulate incoming server response
    response_msg = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": [
            {
                "uri": "file:///workspace/models.py",
                "range": {
                    "start": {"line": 42, "character": 0},
                    "end": {"line": 42, "character": 10}
                }
            }
        ]
    }

    # Simulate pending request
    import queue
    q = queue.Queue()
    client._pending_requests[msg_id] = q
    client._handle_incoming_message(response_msg)

    resp = q.get_nowait()
    assert resp["id"] == msg_id
    assert len(resp["result"]) == 1
    assert resp["result"][0]["range"]["start"]["line"] == 42
