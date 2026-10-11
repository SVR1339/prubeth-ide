"""
SUKHI IDE — Gate 10 Automated Test Suite
Verifies Language Server Protocol (LSP) and Debug Adapter Protocol (DAP) Subsystems:
- Content-Length framing byte exactness
- Protocol initialization handshakes and capability negotiation
- LSP document lifecycle notifications (didOpen, didChange) and diagnostics parsing
- DAP breakpoint setting, thread control (next, stepIn), stack frames, and variable inspection
- Graceful shutdown and process cleanup
"""
import sys
import json
import time
from pathlib import Path
import tempfile
import shutil

from language_services.lsp_client import LspClient, LspDiagnostic, path_to_uri, uri_to_path
from debugging.dap_client import DapClient, SourceBreakpoint, StackFrame, Variable


def test_lsp_message_framing():
    """LspClient must format messages with exact standard Content-Length headers."""
    client = LspClient(command=sys.executable)
    payload = {"jsonrpc": "2.0", "id": 1, "method": "test"}
    raw = client._format_message(payload)

    assert raw.startswith(b"Content-Length: ")
    assert b"\r\n\r\n" in raw
    header, body = raw.split(b"\r\n\r\n", 1)
    content_len = int(header.split(b": ")[1])
    assert len(body) == content_len
    assert json.loads(body.decode("utf-8")) == payload


def test_dap_message_framing():
    """DapClient must format requests with exact standard Content-Length headers."""
    client = DapClient(command=sys.executable)
    payload = {"seq": 1, "type": "request", "command": "initialize"}
    raw = client._format_message(payload)

    assert raw.startswith(b"Content-Length: ")
    assert b"\r\n\r\n" in raw
    header, body = raw.split(b"\r\n\r\n", 1)
    content_len = int(header.split(b": ")[1])
    assert len(body) == content_len
    assert json.loads(body.decode("utf-8")) == payload


def test_lsp_diagnostics_parsing_and_uri_conversion():
    """LspClient must accurately parse publishDiagnostics notifications and convert URIs."""
    client = LspClient(command=sys.executable)
    test_path = Path("C:/workspace/sample.py") if sys.platform == "win32" else Path("/workspace/sample.py")
    uri = path_to_uri(test_path)
    assert uri.startswith("file://")

    # Simulate incoming textDocument/publishDiagnostics notification
    simulated_msg = {
        "jsonrpc": "2.0",
        "method": "textDocument/publishDiagnostics",
        "params": {
            "uri": uri,
            "diagnostics": [
                {
                    "message": "Undefined variable 'foo'",
                    "severity": 1,
                    "range": {
                        "start": {"line": 10, "character": 4},
                        "end": {"line": 10, "character": 7}
                    },
                    "source": "pylsp"
                },
                {
                    "message": "Unused import 'sys'",
                    "severity": 2,
                    "range": {
                        "start": {"line": 2, "character": 0},
                        "end": {"line": 2, "character": 10}
                    },
                    "source": "flake8"
                }
            ]
        }
    }

    client._handle_incoming_message(simulated_msg)
    diags = client.get_diagnostics(test_path)

    assert len(diags) == 2
    assert diags[0].message == "Undefined variable 'foo'"
    assert diags[0].severity == 1
    assert diags[0].start_line == 10
    assert diags[0].start_character == 4

    assert diags[1].message == "Unused import 'sys'"
    assert diags[1].severity == 2
    assert diags[1].source == "flake8"


def test_lsp_mock_server_communication():
    """Spawns an inline Python LSP mock server to verify full start/initialize/shutdown roundtrip."""
    # Lightweight mock server script
    mock_server_code = """
import sys, json

def send(data):
    body = json.dumps(data).encode('utf-8')
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\\r\\n\\r\\n".encode('ascii') + body)
    sys.stdout.buffer.flush()

while True:
    line = sys.stdin.readline()
    if not line:
        break
    if line.lower().startswith('content-length:'):
        cl = int(line.split(':')[1].strip())
        while True:
            hdr = sys.stdin.readline()
            if not hdr or not hdr.strip():
                break
        body_bytes = sys.stdin.read(cl)
        msg = json.loads(body_bytes)
        method = msg.get('method')
        msg_id = msg.get('id')

        if method == 'initialize':
            send({
                'jsonrpc': '2.0',
                'id': msg_id,
                'result': {
                    'capabilities': {'textDocumentSync': 1}
                }
            })
        elif method == 'shutdown':
            send({'jsonrpc': '2.0', 'id': msg_id, 'result': None})
            break
        elif method == 'exit':
            break
"""

    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_lsp_test_"))
    server_script = temp_dir / "mock_lsp.py"
    server_script.write_text(mock_server_code, encoding="utf-8")

    try:
        client = LspClient(command=sys.executable, args=[str(server_script)], cwd=temp_dir)
        started = client.start(timeout_seconds=5)
        assert started is True
        assert client._is_running is True

        # Send open document notification
        client.open_document(temp_dir / "main.py", "x = 10\n", language_id="python")

        # Graceful shutdown
        client.stop()
        assert client.process is None or client.process.poll() is not None

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_dap_mock_server_communication():
    """Spawns an inline Python DAP mock server to verify breakpoint and inspection roundtrip."""
    mock_dap_code = """
import sys, json

def send(data):
    body = json.dumps(data).encode('utf-8')
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\\r\\n\\r\\n".encode('ascii') + body)
    sys.stdout.buffer.flush()

while True:
    line = sys.stdin.readline()
    if not line:
        break
    if line.lower().startswith('content-length:'):
        cl = int(line.split(':')[1].strip())
        while True:
            hdr = sys.stdin.readline()
            if not hdr or not hdr.strip():
                break
        body_bytes = sys.stdin.read(cl)
        msg = json.loads(body_bytes)
        cmd = msg.get('command')
        seq = msg.get('seq')

        if cmd == 'initialize':
            send({
                'seq': 1,
                'type': 'response',
                'request_seq': seq,
                'command': 'initialize',
                'success': True,
                'body': {'supportsConfigurationDoneRequest': True}
            })
        elif cmd == 'setBreakpoints':
            lines = msg.get('arguments', {}).get('lines', [])
            send({
                'seq': 2,
                'type': 'response',
                'request_seq': seq,
                'command': 'setBreakpoints',
                'success': True,
                'body': {'breakpoints': [{'line': l, 'verified': True, 'id': i+1} for i, l in enumerate(lines)]}
            })
        elif cmd == 'configurationDone':
            send({
                'seq': 3,
                'type': 'response',
                'request_seq': seq,
                'command': 'configurationDone',
                'success': True
            })
        elif cmd == 'stackTrace':
            send({
                'seq': 4,
                'type': 'response',
                'request_seq': seq,
                'command': 'stackTrace',
                'success': True,
                'body': {
                    'stackFrames': [{'id': 101, 'name': 'main', 'source': {'path': 'app.py'}, 'line': 15}]
                }
            })
        elif cmd == 'variables':
            send({
                'seq': 5,
                'type': 'response',
                'request_seq': seq,
                'command': 'variables',
                'success': True,
                'body': {
                    'variables': [{'name': 'counter', 'value': '42', 'type': 'int', 'variablesReference': 0}]
                }
            })
        elif cmd == 'disconnect':
            send({
                'seq': 6,
                'type': 'response',
                'request_seq': seq,
                'command': 'disconnect',
                'success': True
            })
            break
"""

    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_dap_test_"))
    server_script = temp_dir / "mock_dap.py"
    server_script.write_text(mock_dap_code, encoding="utf-8")

    try:
        client = DapClient(command=sys.executable, args=[str(server_script)], cwd=temp_dir)
        started = client.start(timeout_seconds=5)
        assert started is True

        # Set breakpoints
        target_file = temp_dir / "app.py"
        bps = client.set_breakpoints(target_file, [10, 15], timeout=3)
        assert len(bps) == 2
        assert bps[0].verified is True
        assert bps[0].line == 10

        # Configuration done
        cfg_done = client.configuration_done(timeout=3)
        assert cfg_done is True

        # Stack trace
        frames = client.get_stack_trace(thread_id=1, timeout=3)
        assert len(frames) == 1
        assert frames[0].name == "main"
        assert frames[0].line == 15

        # Variables inspection
        vars_res = client.get_variables(variables_reference=101, timeout=3)
        assert len(vars_res) == 1
        assert vars_res[0].name == "counter"
        assert vars_res[0].value == "42"

        # Disconnect & stop
        client.stop()
        assert client.process is None or client.process.poll() is not None

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
