"""
PRUBETH IDE — Bulletproof Error Vault & Persistent Bug Ledger
=============================================================
PRINCE2 7 Reliability & Autonomous Self-Healing Subsystem.

Universal, immutable, persistent ledger for all exceptions, bugs,
runtime errors, and defect reports across the entire IDE workstation.

Features:
1. Global exception hooks: sys.excepthook, threading.excepthook, Qt message handler.
2. Immutable JSONL ledger (~/.local_ai_studio_pro/error_vault/error_ledger.jsonl).
3. Fast snapshot index (~/.local_ai_studio_pro/error_vault/error_index.json).
4. Stable SHA-256 fingerprinting for automatic deduplication & occurrence counting.
5. Automated Daily Health & Reliability Digest generation (JSON & Markdown).
6. 1-Click "Solve & Fix" dispatch payload for AI Copilot auto-remediation.
7. Bulletproof fail-safe design: recording an error will NEVER crash or raise.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
import os
import sys
import threading
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("prubeth.error_vault")


class ErrorSeverity(str, Enum):
    CRITICAL = "CRITICAL"   # Fatal or process-threatening error
    ERROR = "ERROR"         # Standard unhandled exception or failure
    WARNING = "WARNING"     # Deprecation, recoverable timeout, degraded service
    DEFECT = "DEFECT"       # Logic defect, validation violation, regression


class ErrorStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"       # Newly logged or open issue
    IN_PROGRESS = "IN_PROGRESS"     # Currently being diagnosed or patched
    RESOLVED = "RESOLVED"           # Fixed and verified
    AUTO_REPAIRED = "AUTO_REPAIRED" # Automatically patched by AI Copilot
    IGNORED = "IGNORED"             # Acknowledged non-issue or intentional


@dataclass
class ErrorRecord:
    """Immutable persistent record of a single unique bug or runtime failure."""
    error_id: str
    fingerprint: str
    error_type: str
    message: str
    traceback_str: str
    subsystem: str = "CORE"
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    first_seen_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    occurrence_count: int = 1
    severity: str = ErrorSeverity.ERROR.value
    status: str = ErrorStatus.UNRESOLVED.value
    context_dump: Dict[str, Any] = field(default_factory=dict)
    remediation_notes: str = ""
    resolved_at_iso: Optional[str] = None
    resolved_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorRecord":
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


def compute_error_fingerprint(
    error_type: str,
    file_path: Optional[str],
    line_number: Optional[int],
    message: str
) -> str:
    """
    Computes a stable SHA-256 fingerprint for deduplicating identical bugs.
    Normalizes variable memory addresses, timestamps, and quotes.
    """
    import re
    norm_msg = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", str(message or "").strip().lower())
    norm_msg = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "TIMESTAMP", norm_msg)
    norm_file = os.path.basename(file_path or "").lower()
    raw = f"{error_type}:{norm_file}:{line_number or 0}:{norm_msg[:200]}"
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


class ErrorVault:
    """
    Universal persistent error vault and bug ledger.
    Thread-safe singleton with append-only ledger and fast query index.
    """
    _instance: Optional["ErrorVault"] = None
    _lock = threading.RLock()

    def __init__(self, vault_dir: Optional[Path] = None):
        if vault_dir:
            self.vault_dir = Path(vault_dir).resolve()
        else:
            self.vault_dir = Path.home() / ".local_ai_studio_pro" / "error_vault"

        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.daily_dir = self.vault_dir / "daily_reports"
        self.daily_dir.mkdir(parents=True, exist_ok=True)

        self.ledger_file = self.vault_dir / "error_ledger.jsonl"
        self.index_file = self.vault_dir / "error_index.json"

        self._records: Dict[str, ErrorRecord] = {}           # error_id -> ErrorRecord
        self._fingerprints: Dict[str, str] = {}              # fingerprint -> error_id
        self._listeners: List[Callable[[ErrorRecord], None]] = []
        self._internal_lock = threading.RLock()

        # Load existing index & ledger
        self._load_vault()

    @classmethod
    def get_instance(cls, vault_dir: Optional[Path] = None) -> "ErrorVault":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(vault_dir=vault_dir)
            return cls._instance

    @classmethod
    def reset_instance_for_testing(cls, vault_dir: Optional[Path] = None) -> "ErrorVault":
        """Used in test suites to isolate test vaults."""
        with cls._lock:
            cls._instance = cls(vault_dir=vault_dir)
            return cls._instance

    def register_listener(self, callback: Callable[[ErrorRecord], None]) -> None:
        """Register a callback that fires whenever an error is recorded or updated."""
        with self._internal_lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[ErrorRecord], None]) -> None:
        with self._internal_lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def _load_vault(self) -> None:
        """Loads index and rebuilds state from ledger if necessary."""
        with self._internal_lock:
            # 1. Try loading cached fast index
            loaded_from_index = False
            if self.index_file.exists():
                try:
                    data = json.loads(self.index_file.read_text(encoding="utf-8", errors="replace"))
                    if isinstance(data, dict):
                        for k, v in data.items():
                            rec = ErrorRecord.from_dict(v)
                            self._records[rec.error_id] = rec
                            self._fingerprints[rec.fingerprint] = rec.error_id
                        loaded_from_index = True
                except Exception as e:
                    logger.warning(f"Failed loading error index: {e}, falling back to ledger rebuild.")

            # 2. Replay ledger if index was missing or corrupted
            if not loaded_from_index and self.ledger_file.exists():
                self._replay_ledger()

    def _replay_ledger(self) -> None:
        """Reconstructs state table by replaying append-only ledger entries."""
        try:
            with open(self.ledger_file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        op = entry.get("op", "RECORD")
                        if op == "RECORD":
                            rec_data = entry.get("record", {})
                            rec = ErrorRecord.from_dict(rec_data)
                            self._records[rec.error_id] = rec
                            self._fingerprints[rec.fingerprint] = rec.error_id
                        elif op == "UPDATE":
                            rec_data = entry.get("record", {})
                            e_id = rec_data.get("error_id")
                            if e_id and e_id in self._records:
                                self._records[e_id] = ErrorRecord.from_dict(rec_data)
                    except Exception:
                        continue
            self._save_index()
        except Exception as e:
            logger.error(f"Error replaying ledger: {e}")

    def _save_index(self) -> None:
        """Writes in-memory records to fast index JSON snapshot."""
        try:
            data = {k: v.to_dict() for k, v in self._records.items()}
            tmp_file = self.index_file.with_suffix(".tmp")
            tmp_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
            if os.name == "nt" and self.index_file.exists():
                try:
                    self.index_file.unlink()
                except Exception:
                    pass
            tmp_file.replace(self.index_file)
        except Exception as e:
            logger.warning(f"Failed writing error index snapshot: {e}")

    def _append_ledger(self, op: str, record: ErrorRecord) -> None:
        """Appends state transition event to immutable JSONL ledger."""
        try:
            entry = {
                "op": op,
                "timestamp_iso": datetime.now().isoformat(),
                "record": record.to_dict()
            }
            with open(self.ledger_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception as e:
            logger.critical(f"FATAL: ErrorVault failed appending to ledger: {e}")

    def record_error(
        self,
        message: str,
        error_type: Optional[str] = None,
        traceback_str: Optional[str] = None,
        subsystem: str = "CORE",
        severity: str = ErrorSeverity.ERROR.value,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        function_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorRecord:
        """
        Record any runtime error or bug into the vault.
        Completely bulletproof: NEVER raises an exception.
        Deduplicates occurrences using fingerprinting and increments occurrence_count.
        """
        try:
            with self._internal_lock:
                now_iso = datetime.now().isoformat()
                err_type = error_type or "RuntimeError"
                clean_msg = str(message or "Unknown runtime failure").strip()
                tb_str = str(traceback_str or "").strip()

                # Extract file and line from traceback if not explicitly provided
                if (not file_path or not line_number) and tb_str:
                    extracted_file, extracted_line, extracted_func = self._parse_traceback_location(tb_str)
                    file_path = file_path or extracted_file
                    line_number = line_number or extracted_line
                    function_name = function_name or extracted_func

                fingerprint = compute_error_fingerprint(err_type, file_path, line_number, clean_msg)

                # Check if this exact bug is already known
                existing_id = self._fingerprints.get(fingerprint)
                if existing_id and existing_id in self._records:
                    record = self._records[existing_id]
                    # If it was resolved, re-open it because it regressed!
                    if record.status in (ErrorStatus.RESOLVED.value, ErrorStatus.AUTO_REPAIRED.value):
                        record.status = ErrorStatus.UNRESOLVED.value
                        record.remediation_notes += f"\n[!] REGRESSION DETECTED on {now_iso}"

                    record.occurrence_count += 1
                    record.last_seen_iso = now_iso
                    if context:
                        record.context_dump.update(context)
                    if tb_str:
                        record.traceback_str = tb_str

                    self._append_ledger("UPDATE", record)
                    self._save_index()
                    self._notify_listeners(record)
                    return record

                # Brand new bug
                now_tag = datetime.now().strftime("%Y%m%d-%H%M%S")
                short_hash = hashlib.sha256(f"{fingerprint}:{time.time()}".encode()).hexdigest()[:6].upper()
                error_id = f"BUG-{now_tag}-{short_hash}"

                record = ErrorRecord(
                    error_id=error_id,
                    fingerprint=fingerprint,
                    error_type=err_type,
                    message=clean_msg,
                    traceback_str=tb_str,
                    subsystem=subsystem.upper(),
                    file_path=file_path,
                    line_number=line_number,
                    function_name=function_name,
                    first_seen_iso=now_iso,
                    last_seen_iso=now_iso,
                    occurrence_count=1,
                    severity=severity.upper(),
                    status=ErrorStatus.UNRESOLVED.value,
                    context_dump=context or {},
                )

                self._records[error_id] = record
                self._fingerprints[fingerprint] = error_id
                self._append_ledger("RECORD", record)
                self._save_index()
                self._notify_listeners(record)
                return record

        except Exception as ex:
            # Absolute fallback: output to stderr, never crash application
            try:
                sys.stderr.write(f"\n[CRITICAL ERROR_VAULT FAILURE] Failed to record error: {ex}\n")
                sys.stderr.flush()
            except Exception:
                pass
            return ErrorRecord(
                error_id="ERR-EMERGENCY-FALLBACK",
                fingerprint="0000000000000000",
                error_type="VaultEmergencyFallback",
                message=str(message),
                traceback_str=str(traceback_str or ""),
                subsystem="VAULT"
            )

    def record_exception(
        self,
        exc: BaseException,
        subsystem: str = "CORE",
        severity: str = ErrorSeverity.ERROR.value,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorRecord:
        """
        Records a Python exception with automated traceback formatting and source extraction.
        """
        try:
            err_type = type(exc).__name__
            msg = str(exc) or err_type
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            file_p, line_n, func_n = self._parse_traceback_location(tb)

            ctx = context or {}
            ctx.setdefault("thread_name", threading.current_thread().name)
            ctx.setdefault("timestamp", time.time())

            return self.record_error(
                message=msg,
                error_type=err_type,
                traceback_str=tb,
                subsystem=subsystem,
                severity=severity,
                file_path=file_p,
                line_number=line_n,
                function_name=func_n,
                context=ctx
            )
        except Exception as e:
            logger.error(f"Error in record_exception: {e}")
            return self.record_error(str(exc), subsystem=subsystem, severity=severity)

    def _parse_traceback_location(self, tb_str: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
        """Parses the most relevant source file, line number, and function from a traceback string."""
        if not tb_str:
            return None, None, None
        try:
            import re
            # Match lines like: File "path/to/file.py", line 123, in func_name
            matches = list(re.finditer(r'File\s+"([^"]+)",\s+line\s+(\d+)(?:,\s+in\s+([^\n\r]+))?', tb_str))
            if matches:
                # Pick the last frame (closest to origin of exception)
                last_m = matches[-1]
                f_path = last_m.group(1)
                l_num = int(last_m.group(2))
                fn_name = last_m.group(3).strip() if last_m.group(3) else None
                return f_path, l_num, fn_name
        except Exception:
            pass
        return None, None, None

    def _notify_listeners(self, record: ErrorRecord) -> None:
        """Dispatches update notifications to registered UI listeners."""
        with self._internal_lock:
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener(record)
            except Exception as e:
                logger.warning(f"ErrorVault listener failed: {e}")

    def get_all_errors(self) -> List[ErrorRecord]:
        """Returns all recorded errors sorted by last_seen_iso descending."""
        with self._internal_lock:
            return sorted(self._records.values(), key=lambda r: r.last_seen_iso, reverse=True)

    def get_unresolved_errors(self) -> List[ErrorRecord]:
        """Returns unresolved and in-progress errors."""
        with self._internal_lock:
            return [
                r for r in self.get_all_errors()
                if r.status in (ErrorStatus.UNRESOLVED.value, ErrorStatus.IN_PROGRESS.value)
            ]

    def get_error(self, error_id: str) -> Optional[ErrorRecord]:
        with self._internal_lock:
            return self._records.get(error_id)

    def resolve_error(
        self,
        error_id: str,
        notes: str = "",
        resolved_by: str = "USER",
        auto_repaired: bool = False
    ) -> bool:
        """Marks an error as RESOLVED or AUTO_REPAIRED with remediation notes."""
        with self._internal_lock:
            rec = self._records.get(error_id)
            if not rec:
                return False

            now_iso = datetime.now().isoformat()
            rec.status = ErrorStatus.AUTO_REPAIRED.value if auto_repaired else ErrorStatus.RESOLVED.value
            rec.resolved_at_iso = now_iso
            rec.resolved_by = resolved_by
            if notes:
                rec.remediation_notes = f"{rec.remediation_notes}\n[{now_iso}] {notes}".strip()

            self._append_ledger("UPDATE", rec)
            self._save_index()
            self._notify_listeners(rec)
            return True

    def update_status(self, error_id: str, status: str, notes: str = "") -> bool:
        """Updates error lifecycle status (e.g. IN_PROGRESS, IGNORED)."""
        with self._internal_lock:
            rec = self._records.get(error_id)
            if not rec:
                return False

            rec.status = status.upper()
            if notes:
                now_iso = datetime.now().isoformat()
                rec.remediation_notes = f"{rec.remediation_notes}\n[{now_iso}] {notes}".strip()

            self._append_ledger("UPDATE", rec)
            self._save_index()
            self._notify_listeners(rec)
            return True

    def clear_resolved_errors(self) -> int:
        """Prunes resolved and auto-repaired records from active index (ledger remains intact)."""
        with self._internal_lock:
            to_remove = [
                eid for eid, r in self._records.items()
                if r.status in (ErrorStatus.RESOLVED.value, ErrorStatus.AUTO_REPAIRED.value, ErrorStatus.IGNORED.value)
            ]
            for eid in to_remove:
                rec = self._records.pop(eid, None)
                if rec and rec.fingerprint in self._fingerprints:
                    self._fingerprints.pop(rec.fingerprint, None)

            self._save_index()
            return len(to_remove)

    def generate_daily_report(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Compiles and persists an authoritative Daily Bug & Reliability Audit Report.
        Format: date_str YYYY-MM-DD (defaults to current date).
        Persists JSON and Markdown report to ~/.local_ai_studio_pro/error_vault/daily_reports/.
        """
        target_date = date_str or datetime.now().strftime("%Y-%m-%d")

        with self._internal_lock:
            all_errors = list(self._records.values())

        # Filter errors occurring or touched on target date
        day_errors = [
            r for r in all_errors
            if (r.first_seen_iso and r.first_seen_iso.startswith(target_date)) or
               (r.last_seen_iso and r.last_seen_iso.startswith(target_date)) or
               (r.resolved_at_iso and r.resolved_at_iso.startswith(target_date))
        ]

        total_day_occurrences = sum(r.occurrence_count for r in day_errors)
        unresolved_count = sum(1 for r in day_errors if r.status == ErrorStatus.UNRESOLVED.value)
        in_progress_count = sum(1 for r in day_errors if r.status == ErrorStatus.IN_PROGRESS.value)
        resolved_count = sum(1 for r in day_errors if r.status == ErrorStatus.RESOLVED.value)
        auto_repaired_count = sum(1 for r in day_errors if r.status == ErrorStatus.AUTO_REPAIRED.value)

        # By Severity
        sev_counts: Dict[str, int] = {}
        for r in day_errors:
            sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1

        # By Subsystem
        subsystem_counts: Dict[str, int] = {}
        for r in day_errors:
            subsystem_counts[r.subsystem] = subsystem_counts.get(r.subsystem, 0) + 1

        resolved_total = resolved_count + auto_repaired_count
        active_total = unresolved_count + in_progress_count
        total_unique = len(day_errors)
        fix_rate_pct = (resolved_total / total_unique * 100.0) if total_unique > 0 else 100.0

        report_data = {
            "report_date": target_date,
            "generated_at_iso": datetime.now().isoformat(),
            "total_unique_bugs_active": total_unique,
            "total_occurrences": total_day_occurrences,
            "unresolved": unresolved_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "auto_repaired": auto_repaired_count,
            "fix_rate_percentage": round(fix_rate_pct, 2),
            "severity_breakdown": sev_counts,
            "subsystem_breakdown": subsystem_counts,
            "bugs": [r.to_dict() for r in day_errors]
        }

        # Persist JSON report
        json_path = self.daily_dir / f"daily_report_{target_date}.json"
        try:
            json_path.write_text(json.dumps(report_data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed writing daily report JSON: {e}")

        # Persist Markdown report
        md_path = self.daily_dir / f"daily_report_{target_date}.md"
        try:
            md_content = self._render_daily_markdown(report_data)
            md_path.write_text(md_content, encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed writing daily report Markdown: {e}")

        return report_data

    def _render_daily_markdown(self, data: Dict[str, Any]) -> str:
        """Formats report into executive Markdown for daily review & reporting."""
        d = data["report_date"]
        fix_rate = data["fix_rate_percentage"]
        status_badge = "🟢 HEALTHY" if fix_rate >= 90.0 else ("🟡 ATTENTION" if fix_rate >= 50.0 else "🔴 CRITICAL")

        lines = [
            f"# PRUBETH IDE — Daily Error & Reliability Audit Report",
            f"**Date:** `{d}` | **Audit Status:** {status_badge} | **Fix Rate:** `{fix_rate:.1f}%`",
            f"**Generated:** `{data['generated_at_iso']}`",
            "",
            "## 1. Executive Summary",
            f"- **Total Unique Issues Observed:** {data['total_unique_bugs_active']}",
            f"- **Cumulative Failure Occurrences:** {data['total_occurrences']}",
            f"- **Unresolved Issues:** {data['unresolved']}",
            f"- **In Progress:** {data['in_progress']}",
            f"- **Resolved by Team:** {data['resolved']}",
            f"- **Auto-Repaired by AI:** {data['auto_repaired']}",
            "",
            "## 2. Severity Breakdown",
        ]
        for sev, cnt in data["severity_breakdown"].items():
            lines.append(f"- **{sev}:** {cnt}")

        lines.extend([
            "",
            "## 3. Subsystem Impact",
        ])
        for sub, cnt in data["subsystem_breakdown"].items():
            lines.append(f"- **{sub}:** {cnt}")

        lines.extend([
            "",
            "## 4. Itemized Bug Ledger",
            "| ID | Severity | Status | Subsystem | Occurrences | Error Message | Location |",
            "| :--- | :--- | :--- | :--- | :---: | :--- | :--- |"
        ])

        for b in data["bugs"]:
            loc = f"`{os.path.basename(b.get('file_path') or '')}:{b.get('line_number') or 0}`" if b.get('file_path') else "`N/A`"
            msg = b.get('message', '').replace("\n", " ")[:65]
            lines.append(f"| `{b['error_id']}` | {b['severity']} | `{b['status']}` | {b['subsystem']} | {b['occurrence_count']} | {msg} | {loc} |")

        lines.append("")
        lines.append("---")
        lines.append("*PRUBETH Bulletproof Error Vault — PRINCE2 7 Automated Reliability Ledger.*")
        return "\n".join(lines)


# =====================================================================
# GLOBAL HOOKS INSTALLATION (UNHANDLED EXCEPTIONS & THREAD CRASHES)
# =====================================================================

_prev_sys_excepthook = None
_prev_threading_excepthook = None
_hooks_installed = False


def _global_sys_excepthook(exc_type, exc_value, exc_traceback):
    """Global sys.excepthook to trap and record all unhandled main-thread exceptions."""
    try:
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow clean user interruption
            if _prev_sys_excepthook:
                _prev_sys_excepthook(exc_type, exc_value, exc_traceback)
            return

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        vault = ErrorVault.get_instance()
        vault.record_error(
            message=str(exc_value) or str(exc_type.__name__),
            error_type=exc_type.__name__,
            traceback_str=tb_str,
            subsystem="RUNTIME",
            severity=ErrorSeverity.CRITICAL.value,
            context={"thread": "MainThread", "unhandled": True}
        )
    except Exception as e:
        sys.stderr.write(f"[ERROR_VAULT_FAIL] {e}\n")

    # Call original hook to preserve standard stderr behavior
    if _prev_sys_excepthook:
        try:
            _prev_sys_excepthook(exc_type, exc_value, exc_traceback)
        except Exception:
            pass


def _global_threading_excepthook(args):
    """Global threading.excepthook to trap unhandled background worker thread exceptions."""
    try:
        exc_type = args.exc_type
        exc_value = args.exc_value
        exc_traceback = args.exc_traceback
        thread = args.thread

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        vault = ErrorVault.get_instance()
        vault.record_error(
            message=str(exc_value) or str(exc_type.__name__),
            error_type=exc_type.__name__,
            traceback_str=tb_str,
            subsystem="BACKGROUND_WORKER",
            severity=ErrorSeverity.ERROR.value,
            context={"thread": thread.name if thread else "UnknownThread", "unhandled": True}
        )
    except Exception as e:
        sys.stderr.write(f"[ERROR_VAULT_FAIL_THREAD] {e}\n")

    if _prev_threading_excepthook:
        try:
            _prev_threading_excepthook(args)
        except Exception:
            pass


def install_global_hooks() -> None:
    """
    Installs process-wide exception hooks into Python and Qt.
    Guarantees no crash goes unrecorded.
    """
    global _prev_sys_excepthook, _prev_threading_excepthook, _hooks_installed

    if _hooks_installed:
        return

    # 1. Sys excepthook
    _prev_sys_excepthook = sys.excepthook
    sys.excepthook = _global_sys_excepthook

    # 2. Threading excepthook (Python 3.8+)
    if hasattr(threading, "excepthook"):
        _prev_threading_excepthook = threading.excepthook
        threading.excepthook = _global_threading_excepthook

    # 3. Qt Message Handler (if PyQt5 is available)
    try:
        from PyQt5.QtCore import qInstallMessageHandler, QtMsgType

        def _qt_message_handler(mode, context, message):
            # Only record Qt Warning, Critical, or Fatal; filter Info/Debug
            if mode == QtMsgType.QtFatalMsg:
                ErrorVault.get_instance().record_error(
                    message=f"[Qt Fatal] {message}",
                    error_type="QtFatalError",
                    subsystem="QT_CORE",
                    severity=ErrorSeverity.CRITICAL.value,
                    file_path=context.file if context else None,
                    line_number=context.line if context else None,
                )
            elif mode == QtMsgType.QtCriticalMsg:
                ErrorVault.get_instance().record_error(
                    message=f"[Qt Critical] {message}",
                    error_type="QtCriticalError",
                    subsystem="QT_CORE",
                    severity=ErrorSeverity.ERROR.value,
                    file_path=context.file if context else None,
                    line_number=context.line if context else None,
                )
            # Standard output for console visibility
            sys.stderr.write(f"[Qt] {message}\n")

        qInstallMessageHandler(_qt_message_handler)
    except Exception:
        pass

    _hooks_installed = True
    logger.info("[*] Global Bulletproof ErrorVault hooks successfully installed.")
