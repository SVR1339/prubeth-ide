"""
PRUBETH IDE — Zero-Silent-Failure Startup Recovery Dialog
Part of the Zero-Silent-Failure Launcher & Application Startup Engine.

Displays an actionable recovery dialog when startup encounters an unhandled
failure or missing mandatory prerequisite. Offers Safe Mode, Settings Reset,
Diagnostic Log viewing, and clean termination.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Callable


class StartupRecoveryHandler:
    """
    Guarantees no silent termination. Either renders a PyQt5 modal recovery window
    or emits structured diagnostic recovery text to stderr/terminal.
    """

    @classmethod
    def show_recovery_dialog(
        cls,
        title: str,
        error_message: str,
        traceback_str: str,
        log_file_path: Optional[Path] = None,
        on_safe_mode: Optional[Callable[[], None]] = None,
        on_reset_settings: Optional[Callable[[], None]] = None
    ) -> str:
        """
        Attempts to display a PyQt5 graphical recovery modal.
        Falls back to console dialog if GUI cannot initialize.
        
        Returns:
            User decision: 'safe_mode', 'reset_settings', 'view_log', or 'exit'.
        """
        try:
            from PyQt5.QtWidgets import (
                QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                QLabel, QTextEdit, QPushButton, QMessageBox
            )
            from PyQt5.QtCore import Qt

            # Ensure QApplication exists
            app = QApplication.instance() or QApplication(sys.argv)

            dialog = QDialog()
            dialog.setWindowTitle(f"PRUBETH IDE — Startup Recovery ({title})")
            dialog.setMinimumSize(640, 420)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #0B0D13;
                    color: #F0F4F8;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLabel {
                    color: #F0F4F8;
                }
                QTextEdit {
                    background-color: #121620;
                    color: #FF5370;
                    border: 1px solid #232938;
                    border-radius: 4px;
                    font-family: 'Cascadia Code', 'Consolas', monospace;
                    font-size: 11px;
                }
                QPushButton {
                    background-color: #1A2030;
                    color: #00F0FF;
                    border: 1px solid #00F0FF;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #00F0FF;
                    color: #0B0D13;
                }
                QPushButton#dangerBtn {
                    color: #FF5370;
                    border-color: #FF5370;
                }
                QPushButton#dangerBtn:hover {
                    background-color: #FF5370;
                    color: #0B0D13;
                }
            """)

            layout = QVBoxLayout(dialog)

            header = QLabel(f"<h2>⚠ Startup Failure Detected</h2><p><b>{error_message}</b></p>")
            header.setWordWrap(True)
            layout.addWidget(header)

            details_box = QTextEdit()
            details_box.setReadOnly(True)
            details_box.setPlainText(traceback_str or error_message)
            layout.addWidget(details_box)

            guidance = QLabel("<p>Select a recovery action below to resolve the startup failure:</p>")
            layout.addWidget(guidance)

            button_layout = QHBoxLayout()

            btn_safe_mode = QPushButton("Start in Safe Mode")
            btn_reset = QPushButton("Reset Settings to Defaults")
            btn_log = QPushButton("View Startup Log")
            btn_exit = QPushButton("Exit Application")
            btn_exit.setObjectName("dangerBtn")

            button_layout.addWidget(btn_safe_mode)
            button_layout.addWidget(btn_reset)
            button_layout.addWidget(btn_log)
            button_layout.addWidget(btn_exit)

            layout.addLayout(button_layout)

            chosen_action = ["exit"]

            def handle_safe():
                chosen_action[0] = "safe_mode"
                if on_safe_mode:
                    on_safe_mode()
                dialog.accept()

            def handle_reset():
                chosen_action[0] = "reset_settings"
                if on_reset_settings:
                    on_reset_settings()
                dialog.accept()

            def handle_log():
                if log_file_path and log_file_path.exists():
                    try:
                        if sys.platform == "win32":
                            os.startfile(str(log_file_path))
                        else:
                            subprocess.Popen(["xdg-open", str(log_file_path)])
                    except Exception:
                        pass

            def handle_exit():
                chosen_action[0] = "exit"
                dialog.reject()

            btn_safe_mode.clicked.connect(handle_safe)
            btn_reset.clicked.connect(handle_reset)
            btn_log.clicked.connect(handle_log)
            btn_exit.clicked.connect(handle_exit)

            dialog.exec_()
            return chosen_action[0]

        except Exception:
            # Fallback to console emission if PyQt5 cannot render
            print("\n" + "=" * 70, file=sys.stderr)
            print("  PRUBETH IDE — STARTUP FAILURE & EMERGENCY RECOVERY", file=sys.stderr)
            print("=" * 70, file=sys.stderr)
            print(f"Error: {error_message}\n", file=sys.stderr)
            if traceback_str:
                print(traceback_str, file=sys.stderr)
            print("=" * 70, file=sys.stderr)
            print("Actionable Recovery Options:", file=sys.stderr)
            print("  1. Run with --safe-mode to bypass extensions and optional probes.", file=sys.stderr)
            print("  2. Run with --reset-settings to restore default configuration.", file=sys.stderr)
            if log_file_path:
                print(f"  3. Inspect diagnostic startup log: {log_file_path}", file=sys.stderr)
            print("=" * 70 + "\n", file=sys.stderr)
            return "exit"
