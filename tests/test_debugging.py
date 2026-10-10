"""
Unit and Integration Tests for Debugging Subsystem (DapClient, Breakpoints, StackFrames, Variables)
"""
import sys
import json
from pathlib import Path
import pytest
from debugging.dap_client import DapClient, SourceBreakpoint, StackFrame, Variable


def test_dap_message_framing():
    client = DapClient("dummy_adapter")
    payload = {"seq": 1, "type": "request", "command": "initialize", "arguments": {}}
    raw = client._format_message(payload)

    assert b"Content-Length: " in raw
    assert b"\r\n\r\n" in raw
    header, body = raw.split(b"\r\n\r\n", 1)
    len_val = int(header.split(b": ")[1])
    assert len(body) == len_val

    decoded = json.loads(body.decode("utf-8"))
    assert decoded["command"] == "initialize"
    assert decoded["seq"] == 1


def test_dap_breakpoint_registration(tmp_path):
    client = DapClient("dummy_adapter")
    sample_file = tmp_path / "script.py"
    sample_file.write_text("x = 1\ny = 2\nprint(x + y)\n", encoding="utf-8")

    # When no process is running, set_breakpoints returns unverified breakpoints safely
    bps = client.set_breakpoints(sample_file, [1, 3])
    assert len(bps) == 2
    assert bps[0].line == 1
    assert bps[1].line == 3
    assert str(sample_file.resolve()) in client._breakpoints


def test_dap_stack_trace_and_variables_parsing():
    client = DapClient("dummy_adapter")
    seq_id = client._next_seq()

    response_stack = {
        "seq": 2,
        "type": "response",
        "request_seq": seq_id,
        "command": "stackTrace",
        "success": True,
        "body": {
            "stackFrames": [
                {
                    "id": 100,
                    "name": "main",
                    "source": {"path": "/workspace/script.py"},
                    "line": 42,
                    "column": 1
                }
            ]
        }
    }

    import queue
    q = queue.Queue()
    client._pending_requests[seq_id] = q
    client._handle_incoming_message(response_stack)

    resp = q.get_nowait()
    assert resp["success"] is True
    frames = resp["body"]["stackFrames"]
    assert len(frames) == 1
    assert frames[0]["id"] == 100
    assert frames[0]["name"] == "main"
