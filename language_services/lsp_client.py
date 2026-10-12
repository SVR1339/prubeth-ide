"""
PRUBETH IDE â€” Language Server Protocol (LSP) Client Engine
Implements standard JSON-RPC 2.0 framing over stdin/stdout with Content-Length headers,
document synchronization, symbol definition requests, and diagnostic capturing.
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
from typing import Dict, Any, List, Optional, Tuple, Callable


@dataclass
class LspLocation:
    uri: str
    start_line: int
    start_character: int
    end_line: int
    end_character: int


@dataclass
class LspDiagnostic:
    uri: str
    message: str
    severity: int  # 1: Error, 2: Warning, 3: Info, 4: Hint
    start_line: int
    start_character: int
    end_line: int
    end_character: int
    source: Optional[str] = None


def path_to_uri(file_path: Path) -> str:
    """Converts a local filesystem path to a standard file:// URI."""
    return file_path.resolve().as_uri()


def uri_to_path(uri: str) -> Path:
    """Converts a file:// URI to a local filesystem Path."""
    if uri.startswith("file:///"):
        # Windows file:///C:/path or Unix file:///path
        clean = uri[8:] if sys.platform == "win32" and uri[9:11] == ":/" else uri[7:]
        return Path(clean)
    return Path(uri)


class LspClient:
    """Communicates with LSP servers (e.g. pylsp, pyright) over standard I/O."""

    def __init__(self, command: str, args: Optional[List[str]] = None, cwd: Optional[Path] = None):
        self.command = command
        self.args = args or []
        self.cwd = Path(cwd).resolve() if cwd else Path.cwd()
        self.process: Optional[subprocess.Popen] = None
        self._req_id = 0
        self._pending_requests: Dict[int, queue.Queue] = {}
        self._diagnostics: Dict[str, List[LspDiagnostic]] = {}
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

            # Send initialize request
            root_uri = path_to_uri(self.cwd)
            init_req = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "processId": os.getpid(),
                    "rootUri": root_uri,
                    "capabilities": {
                        "textDocument": {
                            "synchronization": {"dynamicRegistration": False, "willSave": False, "didSave": True},
                            "definition": {"dynamicRegistration": False},
                            "publishDiagnostics": {"relatedInformation": True}
                        }
                    },
                    "clientInfo": {"name": "PRUBETH IDE", "version": "1.12.0"}
                }
            }
            resp = self._send_request(init_req, timeout=timeout_seconds)
            if resp and "result" in resp:
                # Send initialized notification
                self._send_notification("initialized", {})
                return True
            return False
        except Exception:
            self.stop()
            return False

    def stop(self):
        self._is_running = False
        if self.process:
            try:
                # Graceful shutdown
                req_id = self._next_id()
                self._send_request({"jsonrpc": "2.0", "id": req_id, "method": "shutdown", "params": None}, timeout=2)
                self._send_notification("exit", None)
            except Exception:
                pass
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process = None

    def open_document(self, file_path: Path, content: str, language_id: str = "python", version: int = 1):
        uri = path_to_uri(file_path)
        params = {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": version,
                "text": content
            }
        }
        self._send_notification("textDocument/didOpen", params)

    def change_document(self, file_path: Path, new_content: str, version: int = 2):
        uri = path_to_uri(file_path)
        params = {
            "textDocument": {"uri": uri, "version": version},
            "contentChanges": [{"text": new_content}]
        }
        self._send_notification("textDocument/didChange", params)

    def goto_definition(self, file_path: Path, line: int, character: int, timeout: int = 5) -> List[LspLocation]:
        uri = path_to_uri(file_path)
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character}
            }
        }
        resp = self._send_request(req, timeout=timeout)
        locations = []
        if not resp or "result" not in resp or not resp["result"]:
            return locations

        res = resp["result"]
        # Can be Location, LocationLink, or List of either
        raw_items = res if isinstance(res, list) else [res]
        for item in raw_items:
            target_uri = item.get("uri") or item.get("targetUri")
            target_range = item.get("range") or item.get("targetRange")
            if target_uri and target_range:
                start = target_range.get("start", {})
                end = target_range.get("end", {})
                locations.append(LspLocation(
                    uri=target_uri,
                    start_line=start.get("line", 0),
                    start_character=start.get("character", 0),
                    end_line=end.get("line", 0),
                    end_character=end.get("character", 0)
                ))
        return locations

    def get_diagnostics(self, file_path: Path) -> List[LspDiagnostic]:
        uri = path_to_uri(file_path)
        return self._diagnostics.get(uri, [])

    def _next_id(self) -> int:
        with self._lock:
            self._req_id += 1
            return self._req_id

    def _send_request(self, payload: Dict[str, Any], timeout: int = 5) -> Optional[Dict[str, Any]]:
        req_id = payload["id"]
        q = queue.Queue()
        with self._lock:
            self._pending_requests[req_id] = q

        raw = self._format_message(payload)
        try:
            self.process.stdin.write(raw)
            self.process.stdin.flush()
        except Exception:
            with self._lock:
                self._pending_requests.pop(req_id, None)
            return None

        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
        finally:
            with self._lock:
                self._pending_requests.pop(req_id, None)

    def _send_notification(self, method: str, params: Any):
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        raw = self._format_message(payload)
        try:
            self.process.stdin.write(raw)
            self.process.stdin.flush()
        except Exception:
            pass

    def _read_loop(self):
        """Reads Content-Length headers and dispatches JSON payloads from server stdout."""
        stdout = self.process.stdout
        while self._is_running and self.process and self.process.poll() is None:
            try:
                # Read header lines until empty line
                content_length = None
                while True:
                    line = stdout.readline()
                    if not line:
                        return
                    line_str = line.decode("ascii", errors="replace").strip()
                    if not line_str:
                        break  # empty line marks end of headers
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
        # Check if response to pending request
        msg_id = msg.get("id")
        if msg_id is not None and msg_id in self._pending_requests:
            self._pending_requests[msg_id].put(msg)
            return

        # Check if notification
        method = msg.get("method")
        if method == "textDocument/publishDiagnostics":
            params = msg.get("params", {})
            uri = params.get("uri", "")
            diag_items = params.get("diagnostics", [])
            parsed = []
            for d in diag_items:
                rng = d.get("range", {})
                start = rng.get("start", {})
                end = rng.get("end", {})
                parsed.append(LspDiagnostic(
                    uri=uri,
                    message=d.get("message", ""),
                    severity=d.get("severity", 1),
                    start_line=start.get("line", 0),
                    start_character=start.get("character", 0),
                    end_line=end.get("line", 0),
                    end_character=end.get("character", 0),
                    source=d.get("source")
                ))
            self._diagnostics[uri] = parsed

