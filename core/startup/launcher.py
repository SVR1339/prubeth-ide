"""
PRUBETH IDE — Authoritative Application Launcher & Lifecycle Orchestrator
Part of the Zero-Silent-Failure Launcher & Application Startup Engine.

Provides the single authoritative entry point across all launch methods:
- Desktop Shortcuts & Start Menu
- PowerShell & Batch Scripts (run_local_ai_studio_pro.bat, run_ide.bat, run_ide.sh)
- Direct Python Module Invocation (python local_ai_studio_pro.py)
- Standalone Packaged Executables (PrubethIDE.exe / PrubethIDE-v3.0.0-Setup.exe)
Guarantees fast preflight sanity, dependency-ordered initialization, safe mode recovery,
and zero silent crashes.
"""

from __future__ import annotations

import os
import sys
import argparse
import traceback
from pathlib import Path
from typing import List, Optional

from core.startup.path_resolver import PathResolver, ResolvedPaths
from core.startup.state_machine import StartupStateMachine, StartupState
from core.startup.preflight import PreflightChecker, CheckStatus, PreflightReport
from core.startup.service_initializer import ServiceInitializer
from core.startup.recovery_dialog import StartupRecoveryHandler

APP_NAME = "PRUBETH IDE"
APP_VERSION = "3.0.0"


class AuthoritativeLauncher:
    """
    Unified application launcher that orchestrates preflight checks,
    dependency-ordered service startup, recovery dialogs, and GUI instantiation.
    """

    def __init__(self, argv: Optional[List[str]] = None):
        self.argv = argv if argv is not None else sys.argv[1:]
        self.state_machine = StartupStateMachine()
        self.paths: ResolvedPaths = PathResolver.resolve()

    def parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog="prubeth",
            description=f"{APP_NAME} — Sovereign Autonomous AI Developer Environment (v{APP_VERSION})"
        )
        parser.add_argument("--safe-mode", action="store_true", help="Launch in Safe Mode with extensions and probes disabled.")
        parser.add_argument("--reset-settings", action="store_true", help="Backup existing settings and restore default configuration.")
        parser.add_argument("--preflight-only", action="store_true", help="Execute preflight checks, print structured report, and exit.")
        parser.add_argument("--headless", action="store_true", help="Initialize all services and state machines without opening GUI.")
        parser.add_argument("--workspace", type=str, default=None, help="Initial workspace directory to open.")
        parser.add_argument("--diagnostics", action="store_true", help="Print system diagnostic report and telemetry to stdout.")
        return parser.parse_args(self.argv)

    def launch(self) -> int:
        """
        Executes the authoritative startup sequence.
        Returns:
            Exit code (0 for clean exit, non-zero for failure).
        """
        args = self.parse_args()

        # Handle explicit settings reset request
        if args.reset_settings:
            self._handle_reset_settings()

        # 1. Staged State: PREFLIGHT
        self.state_machine.transition_to(StartupState.PREFLIGHT)
        report = PreflightChecker.run_preflight(
            self.paths,
            allow_safe_mode_recovery=True
        )

        if args.preflight_only or args.diagnostics:
            print("\n" + "=" * 60)
            print(f"  {APP_NAME} v{APP_VERSION} PREFLIGHT DIAGNOSTICS REPORT")
            print("=" * 60)
            print(f"Overall Status: {report.overall_status.value}")
            print(f"Summary:        {report.summary}\n")
            for it in report.items:
                mark = "✓" if it.status == CheckStatus.PASS else ("⚠" if it.status == CheckStatus.WARN else "✗")
                print(f"[{mark}] [{it.category.upper()}] {it.name}: {it.message}")
                if it.remediation_guidance:
                    print(f"    Guidance: {it.remediation_guidance}")
            print("=" * 60 + "\n")
            return 0 if report.can_proceed else 1

        # Check for mandatory preflight failure
        if not report.can_proceed:
            self.state_machine.transition_to(
                StartupState.FAILED,
                error_message=report.summary
            )
            # Display emergency recovery dialog
            failed_items = [it for it in report.items if it.status == CheckStatus.FAIL]
            msg = "\n".join(f"• {it.name}: {it.message}" for it in failed_items)
            guidance = "\n".join(f"• {it.remediation_guidance}" for it in failed_items if it.remediation_guidance)
            
            StartupRecoveryHandler.show_recovery_dialog(
                title="Preflight Validation Failed",
                error_message=f"Mandatory requirements were not satisfied:\n{msg}",
                traceback_str=f"Remediation Guidance:\n{guidance}",
                log_file_path=self.paths.logs_dir / "startup.log"
            )
            return 1

        # Determine effective safe mode
        effective_safe_mode = args.safe_mode or report.requires_safe_mode

        # 2. Staged State: Service Initialization
        initializer = ServiceInitializer(
            paths=self.paths,
            state_machine=self.state_machine,
            safe_mode=effective_safe_mode
        )

        success, descriptors = initializer.initialize_all()
        if not success:
            failed_svcs = [d for d in descriptors if d.status.value == "FAILED"]
            err_msg = ", ".join(d.name for d in failed_svcs)
            StartupRecoveryHandler.show_recovery_dialog(
                title="Service Initialization Failed",
                error_message=f"Could not start required application services: {err_msg}",
                traceback_str=failed_svcs[0].diagnostics.get("traceback", "") if failed_svcs else "",
                log_file_path=self.paths.logs_dir / "startup.log",
                on_safe_mode=lambda: self._restart_in_safe_mode(),
                on_reset_settings=lambda: self._handle_reset_settings()
            )
            initializer.shutdown()
            return 1

        # If running in headless mode, finish here
        if args.headless:
            initializer.shutdown()
            return 0

        # 3. Staged State: GUI Initialization & Event Loop
        try:
            return self._launch_gui(args, effective_safe_mode)
        finally:
            initializer.shutdown()

    def _launch_gui(self, args: argparse.Namespace, safe_mode: bool) -> int:
        """Initializes PyQt5 application and main window."""
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt

            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv[:1] + self.argv)

            app.setApplicationName(APP_NAME)
            app.setStyle("Fusion")

            # Import Studio dynamically to allow all services to be ready first
            import local_ai_studio_pro

            self.state_machine.transition_to(StartupState.GUI_READY)

            window = local_ai_studio_pro.Studio()
            
            # Apply initial workspace if passed via CLI
            if args.workspace and Path(args.workspace).exists():
                try:
                    window.open_folder(args.workspace)
                except Exception:
                    pass

            if safe_mode:
                window.statusBar().showMessage("⚠ Running in Safe Mode (Minimal configuration)", 10000)

            window.show()

            self.state_machine.transition_to(StartupState.APPLICATION_READY)

            # Enter main Qt event loop
            exit_code = app.exec_()
            self.state_machine.transition_to(StartupState.SHUTDOWN)
            return exit_code

        except Exception as gui_ex:
            tb = traceback.format_exc()
            self.state_machine.transition_to(
                StartupState.FAILED,
                error_message=str(gui_ex)
            )
            StartupRecoveryHandler.show_recovery_dialog(
                title="GUI Window Failure",
                error_message=f"Could not display main IDE window: {gui_ex}",
                traceback_str=tb,
                log_file_path=self.paths.logs_dir / "startup.log",
                on_safe_mode=lambda: self._restart_in_safe_mode(),
                on_reset_settings=lambda: self._handle_reset_settings()
            )
            return 1

    def _handle_reset_settings(self) -> None:
        """Backs up existing settings and writes factory default configuration."""
        cfg = self.paths.config_file
        if cfg.exists():
            import time, shutil
            bak = self.paths.user_data_dir / f"settings.backup.{int(time.time())}.bak"
            try:
                shutil.copy2(cfg, bak)
                cfg.unlink()
            except Exception:
                pass

    def _restart_in_safe_mode(self) -> None:
        """Restarts the current Python process with --safe-mode flag."""
        import subprocess
        cmd = [sys.executable, str(self.paths.app_root / "local_ai_studio_pro.py"), "--safe-mode"]
        subprocess.Popen(cmd)
        sys.exit(0)
