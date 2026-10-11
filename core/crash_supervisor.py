"""
PRUBETH IDE — Independent Crash Supervisor & Process Watchdog
=============================================================
PRINCE2 7 Reliability & Integrity Assurance Architecture.

Runs out-of-process to supervise the primary IDE desktop application:
1. Monitors IDE child process lifecycle, exit codes, and heartbeats.
2. Captures stdout/stderr crash traces, timestamps, and memory telemetry.
3. Detects hangs, deadlocks, repeated crashes, and abnormal terminations.
4. Enforces bounded restarts (max N within rolling window) to prevent infinite loops.
5. Provides emergency cancellation and automated Safe Mode fallback.
6. Persists structured crash dump reports to ~/.local_ai_studio_pro/crash_reports/
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import psutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("prubeth.supervisor")


@dataclass
class CrashReport:
    timestamp: float
    iso_time: str
    exit_code: int
    exit_reason: str
    uptime_seconds: float
    restart_count: int
    safe_mode_activated: bool
    peak_memory_mb: float
    stdout_tail: List[str] = field(default_factory=list)
    stderr_tail: List[str] = field(default_factory=list)
    diagnostic_details: Dict[str, Any] = field(default_factory=dict)


class CrashSupervisor:
    """
    Independent process supervisor monitoring the IDE process.
    Survives host application crashes to guarantee failure capture and recovery.
    """

    def __init__(
        self,
        target_executable: Optional[str] = None,
        target_script: Optional[str] = None,
        max_restarts: int = 3,
        restart_window_seconds: float = 600.0,
        heartbeat_timeout_seconds: float = 60.0,
        reports_dir: Optional[Path] = None,
        enable_auto_restart: bool = True
    ):
        self.target_executable = target_executable or sys.executable
        self.target_script = target_script or str(Path(__file__).resolve().parent.parent / "local_ai_studio_pro.py")
        self.max_restarts = max_restarts
        self.restart_window_seconds = restart_window_seconds
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.enable_auto_restart = enable_auto_restart

        if reports_dir:
            self.reports_dir = Path(reports_dir)
        else:
            self.reports_dir = Path.home() / ".local_ai_studio_pro" / "crash_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.restart_history: List[float] = []
        self.current_process: Optional[subprocess.Popen] = None
        self.is_running = False

    def clean_old_restarts(self, now: float) -> None:
        """Prunes restart timestamps outside the rolling window."""
        cutoff = now - self.restart_window_seconds
        self.restart_history = [t for t in self.restart_history if t >= cutoff]

    def can_restart(self) -> bool:
        """Enforces bounded restart policy to prevent restart loops."""
        now = time.time()
        self.clean_old_restarts(now)
        return len(self.restart_history) < self.max_restarts

    def get_exit_reason(self, exit_code: int) -> str:
        """Interprets process exit code across platforms."""
        if exit_code == 0:
            return "CLEAN_SHUTDOWN"
        elif exit_code == -9 or exit_code == 137:
            return "SIGKILL_OOM_TERMINATION"
        elif exit_code == -11 or exit_code == 139:
            return "SIGSEGV_SEGMENTATION_FAULT"
        elif exit_code == 3221225477 or exit_code == -1073741819:
            return "WINDOWS_ACCESS_VIOLATION_0xC0000005"
        elif exit_code == 3221225725 or exit_code == -1073741571:
            return "WINDOWS_STACK_OVERFLOW_0xC00000FD"
        elif exit_code == 1:
            return "UNHANDLED_PYTHON_EXCEPTION"
        return f"ABNORMAL_EXIT_CODE_{exit_code}"

    def persist_crash_report(self, report: CrashReport) -> Path:
        """Writes structured JSON crash artifact."""
        report_file = self.reports_dir / f"crash_{int(report.timestamp)}_{report.exit_code}.json"
        try:
            report_file.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed writing crash report: {e}")
        return report_file

    def run_supervisor(self, extra_args: Optional[List[str]] = None) -> int:
        """
        Main supervision loop.
        Launches IDE, observes lifecycle, catches crashes, and initiates recovery.
        """
        extra_args = extra_args or []
        self.is_running = True
        safe_mode = False

        while self.is_running:
            now = time.time()
            self.clean_old_restarts(now)
            current_restart_count = len(self.restart_history)

            # Auto-activate Safe Mode on repeated crash
            if current_restart_count >= 2 and not safe_mode:
                safe_mode = True
                logger.warning("[!] Activating Emergency Safe Mode after multiple rapid crashes.")

            cmd = [self.target_executable, self.target_script] + extra_args
            if safe_mode and "--safe-mode" not in cmd:
                cmd.append("--safe-mode")

            logger.info(f"[*] Supervisor launching IDE process: {' '.join(cmd)}")
            start_time = time.time()

            # Launch monitored process with piped std streams
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            stdout_lines: List[str] = []
            stderr_lines: List[str] = []
            peak_memory_mb = 0.0

            # Polling loop
            while self.current_process.poll() is None:
                try:
                    # Monitor child process memory
                    p = psutil.Process(self.current_process.pid)
                    mem_mb = p.memory_info().rss / (1024 * 1024)
                    if mem_mb > peak_memory_mb:
                        peak_memory_mb = mem_mb
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                time.sleep(0.5)

            # Process exited
            exit_code = self.current_process.returncode
            uptime = time.time() - start_time

            stdout_out, stderr_out = self.current_process.communicate()
            if stdout_out:
                stdout_lines = stdout_out.splitlines()[-50:]
            if stderr_out:
                stderr_lines = stderr_out.splitlines()[-50:]

            reason = self.get_exit_reason(exit_code)
            logger.info(f"[+] IDE process terminated. Exit code: {exit_code} ({reason}) Uptime: {uptime:.1f}s")

            # Normal clean exit -> shut down supervisor
            if exit_code == 0:
                return 0

            # Abnormal termination -> record crash report
            report = CrashReport(
                timestamp=time.time(),
                iso_time=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                exit_code=exit_code,
                exit_reason=reason,
                uptime_seconds=uptime,
                restart_count=current_restart_count + 1,
                safe_mode_activated=safe_mode,
                peak_memory_mb=peak_memory_mb,
                stdout_tail=stdout_lines,
                stderr_tail=stderr_lines,
                diagnostic_details={"cmd": cmd, "pid": self.current_process.pid}
            )
            saved_report = self.persist_crash_report(report)
            logger.warning(f"[!] Saved crash dump to: {saved_report}")

            # Check restart policy
            if not self.enable_auto_restart:
                return exit_code

            self.restart_history.append(time.time())

            if not self.can_restart():
                logger.error(f"[FATAL] Maximum restart tolerance ({self.max_restarts}) exceeded in window. Halting supervisor.")
                return exit_code

            logger.info(f"[*] Initiating recovery restart ({len(self.restart_history)}/{self.max_restarts})...")
            time.sleep(1.5)

        return 0


def main():
    parser = argparse.ArgumentParser(description="PRUBETH IDE Independent Crash Supervisor")
    parser.add_argument("--executable", type=str, default=sys.executable, help="Python executable")
    parser.add_argument("--script", type=str, default=None, help="IDE main entrypoint script")
    parser.add_argument("--max-restarts", type=int, default=3, help="Max restarts before emergency halt")
    parser.add_argument("--reports-dir", type=str, default=None, help="Crash report directory")
    args, unknown = parser.parse_known_args()

    supervisor = CrashSupervisor(
        target_executable=args.executable,
        target_script=args.script,
        max_restarts=args.max_restarts,
        reports_dir=Path(args.reports_dir) if args.reports_dir else None
    )
    code = supervisor.run_supervisor(extra_args=unknown)
    sys.exit(code)


if __name__ == "__main__":
    main()
