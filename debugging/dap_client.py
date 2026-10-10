"""
SUKHI IDE — Debug Adapter Protocol (DAP) Client Engine
Implements standard DAP framing with Content-Length headers, breakpoint registration,
launch requests, thread stepping, and variable inspection.
"""
import os
import sys
import json
import time
import queue
import threading
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class SourceBreakpoint:
    line: int
    verified: bool = False
    id: Optional[int] = None
    condition: Optional[str] = None
    hit_condition: Optional[str] = None


@dataclass
class StackFrame:
    id: int
    name: str
    source_path: str
    line: int
    column: int = 1


@dataclass
class Variable:
    name: str
    value: str
    type_name: str = ""
    variables_reference: int = 0
    evaluate_name: Optional[str] = None


class DapClient:
    """Communicates with DAP-compliant debug adapters (e.g. debugpy) over standard I/O."""

    def __init__(self, command: str, args: Optional[List[str]] = None, cwd: Optional[Path] = None):
        self.command = command
        self.args = args or []
        self.cwd = Path(cwd).resolve() if cwd else Path.cwd()
        self.process: Optional[subprocess.Popen] = None
        self._seq = 0
        self._pending_requests: Dict[int, queue.Queue] = {}
        self._breakpoints: Dict[str, List[SourceBreakpoint]] = {}
        self._is_running = False
        self._reader_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def _format_message(self, payload: Dict[str, Any]) -> bytes:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        return header + data

    def start(self, timeout_seconds: int = 10) -> bool:
        cmd = [self.command] + self.args
        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.cwd),
                bufsize=0
            )
            self._is_running = True
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()

            init_req = {
                "seq": self._next_seq(),
                "type": "request",
                "command": "initialize",
                "arguments": {
                    "clientID": "sukhi-ide",
                    "clientName": "SUKHI IDE",
                    "adapterID": "python",
                    "linesStartAt1": True,
                    "columnsStartAt1": True,
                    "pathFormat": "path",
                    "supportsVariableType": True,
                    "supportsRunInTerminalRequest": False
                }
            }
            resp = self._send_request(init_req, timeout=timeout_seconds)
            return resp is not None and resp.get("success", False)
        except Exception:
            self.stop()
            return False

    def stop(self):
        self._is_running = False
        if self.process:
            try:
                disc_req = {
                    "seq": self._next_seq(),
                    "type": "request",
                    "command": "disconnect",
                    "arguments": {"restart": False, "terminateDebuggee": True}
                }
                self._send_request(disc_req, timeout=2)
            except Exception:
                pass
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process = None

    def launch(self, script_path: Path, args: Optional[List[str]] = None, cwd: Optional[Path] = None, timeout: int = 10) -> bool:
        launch_req = {
            "seq": self._next_seq(),
            "type": "request",
            "command": "launch",
            "arguments": {
                "name": f"Debug {script_path.name}",
                "type": "python",
                "request": "launch",
                "program": str(script_path.resolve()),
                "args": args or [],
                "cwd": str(cwd.resolve() if cwd else self.cwd),
                "stopOnEntry": False
            }
        }
        resp = self._send_request(launch_req, timeout=timeout)
        return resp is not None and resp.get("success", False)

    def set_breakpoints(self, file_path: Path, lines: List[int], timeout: int = 5) -> List[SourceBreakpoint]:
        path_str = str(file_path.resolve())
        bp_list = [{"line": l} for l in sorted(lines)]
        req = {
            "seq": self._next_seq(),
            "type": "request",
            "command": "setBreakpoints",
            "arguments": {
                "source": {"path": path_str},
                "lines": lines,
                "breakpoints": bp_list
            }
        }
        resp = self._send_request(req, timeout=timeout)
        results = []
        if resp and resp.get("success"):
            raw_bps = resp.get("body", {}).get("breakpoints", [])
            for rb in raw_bps:
                results.append(SourceBreakpoint(
                    line=rb.get("line", 0),
                    verified=rb.get("verified", False),
                    id=rb.get("id")
                ))
        else:
            for l in lines:
                results.append(SourceBreakpoint(line=l, verified=False))

        self._breakpoints[path_str] = results
        return results

    def configuration_done(self, timeout: int = 5) -> bool:
        req = {
            "seq": self._next_seq(),
            "type": "request",
            "command": "configurationDone"
        }
        resp = self._send_request(req, timeout=timeout)
        return resp is not None and resp.get("success", False)

    def continue_execution(self, thread_id: int = 1, timeout: int = 5) -> bool:
        req = {
            "seq": self._next_seq(),
            "type": "request",
            "command": "continue",
            "arguments": {"threadId": thread_id}
        }
        resp = self._send_request(req, timeout=timeout)
        return resp is not None and resp.get("success", False)

    def next_step(self, thread_id: int = 1, timeout: int = 5) -> bool:
        req = {
            "seq": self._next_seq(),
            "type": "request",
            "command": "next",
            "arguments": {"threadId": thread_id}
        }
        resp = self._send_request(req, timeout=timeout)
        return resp is not None and resp.get("success", False)

    def step_in(self, thread_id: int = 1, timeout: int = 5) -> bool:
        req = {
            "seq": self._next_seq(),
            "type": "request",
            "command": "stepIn",
            "arguments": {"threadId": thread_id}
        }
        resp = self._send_request(req, timeout=timeout)
        return resp is not None and resp.get("success", False)

    def step_out(self, thread_id: int = 1, timeout: int = 5) -> bool:
        req = {
            "seq": self._next_seq(),
            "type": "request",
            "command": "stepOut",
            "arguments": {"threadId": thread_id}
        }
        resp = self._send_request(req, timeout=timeout)
        return resp is not None and resp.get("success", False)

    def get_stack_trace(self, thread_id: int = 1, timeout: int = 5) -> List[StackFrame]:
        req = {
            "seq": self._next_seq(),
            "type": "request",
            "command": "stackTrace",
            "arguments": {"threadId": thread_id}
        }
        resp = self._send_request(req, timeout=timeout)
        frames = []
        if resp and resp.get("success"):
            for f in resp.get("body", {}).get("stackFrames", []):
                src = f.get("source", {}).get("path", "")
                frames.append(StackFrame(
                    id=f.get("id", 0),
                    name=f.get("name", "<anonymous>"),
                    source_path=src,
                    line=f.get("line", 1),
                    column=f.get("column", 1)
                ))
        return frames

    def get_variables(self, variables_reference: int, timeout: int = 5) -> List[Variable]:
        req = {
            "seq": self._next_seq(),
            "type": "request",
            "command": "variables",
            "arguments": {"variablesReference": variables_reference}
        }
        resp = self._send_request(req, timeout=timeout)
        variables = []
        if resp and resp.get("success"):
            for v in resp.get("body", {}).get("variables", []):
                variables.append(Variable(
                    name=v.get("name", ""),
                    value=v.get("value", ""),
                    type_name=v.get("type", ""),
                    variables_reference=v.get("variablesReference", 0),
                    evaluate_name=v.get("evaluateName")
                ))
        return variables

    def _next_seq(self) -> int:
        with self._lock:
            self._seq += 1
            return self._seq

    def _send_request(self, payload: Dict[str, Any], timeout: int = 5) -> Optional[Dict[str, Any]]:
        seq = payload["seq"]
        q = queue.Queue()
        with self._lock:
            self._pending_requests[seq] = q

        raw = self._format_message(payload)
        try:
            self.process.stdin.write(raw)
            self.process.stdin.flush()
        except Exception:
            with self._lock:
                self._pending_requests.pop(seq, None)
            return None

        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
        finally:
            with self._lock:
                self._pending_requests.pop(seq, None)

    def _read_loop(self):
        stdout = self.process.stdout
        while self._is_running and self.process and self.process.poll() is None:
            try:
                content_length = None
                while True:
                    line = stdout.readline()
                    if not line:
                        return
                    line_str = line.decode("ascii", errors="replace").strip()
                    if not line_str:
                        break
                    if line_str.lower().startswith("content-length:"):
                        content_length = int(line_str.split(":", 1)[1].strip())

                if content_length is not None and content_length > 0:
                    body_bytes = stdout.read(content_length)
                    if not body_bytes:
                        return
                    body_str = body_bytes.decode("utf-8", errors="replace")
                    msg = json.loads(body_str)
                    self._handle_incoming_message(msg)
            except Exception:
                break

    def _handle_incoming_message(self, msg: Dict[str, Any]):
        msg_type = msg.get("type")
        if msg_type == "response":
            req_seq = msg.get("request_seq")
            if req_seq is not None and req_seq in self._pending_requests:
                self._pending_requests[req_seq].put(msg)
