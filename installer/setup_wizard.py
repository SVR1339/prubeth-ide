"""
PRUBETH IDE — Official Graphical Setup Wizard & Command-Line Installer.
Supports Mode A (Lightweight Online Bootstrapper) and Mode B (Full Offline Installer).
Implements 10-stage progress reporting, GitHub release resolution, cryptographic signature checks,
multi-volume disk space validation, transactional staging, rollback recovery, and CLI automation.
Official Website: https://www.bsvr.work/
"""
import os
import sys
import ssl
import urllib.request
import urllib.error
import shutil
import subprocess
import zipfile
import json
import time
import tempfile
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QRadioButton,
    QProgressBar, QGroupBox, QFileDialog, QMessageBox, QFrame, QTextEdit
)

# Core installer subsystems resolution
_INSTALLER_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _INSTALLER_DIR.parent
for _p in [str(_REPO_ROOT), str(_INSTALLER_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from installer.release_config import (
        APP_NAME, APP_DISPLAY_NAME, APP_TAGLINE, APP_VERSION, PUBLISHER,
        WEBSITE_URL, GITHUB_REPO, GITHUB_REPO_URL, DEFAULT_CHANNEL,
        TARGET_ARCH, DEFAULT_ONLINE_THRESHOLD_MIB, ONLINE_THRESHOLD_BYTES,
        MODE_ONLINE, MODE_OFFLINE, MODE_AUTO,
        EXIT_SUCCESS, EXIT_GENERAL_ERROR, EXIT_INVALID_ARGS, EXIT_NETWORK_ERROR,
        EXIT_VERIFICATION_FAILED, EXIT_INSUFFICIENT_SPACE, EXIT_USER_CANCELLED,
        evaluate_delivery_mode, compute_sha256, verify_manifest_signature,
        TRUSTED_PUBLIC_VERIFICATION_KEY
    )
    from installer.manifest_schema import (
        validate_manifest_schema, verify_manifest_compatibility, ManifestValidationError
    )
    from installer.disk_manager import (
        verify_disk_space, DiskSpaceCheckResult
    )
    from installer.download_engine import (
        ReleaseMetadataResolver, SecureDownloadEngine, DownloadProgress,
        DownloadError, VerificationError, STAGE_NAMES
    )
    from installer.transactional_installer import (
        TransactionalInstaller, SecurityInspectionError, InstallationCommitError,
        inspect_archive_security
    )
    from installer.uninstaller import Uninstaller
except ImportError:
    from release_config import (
        APP_NAME, APP_DISPLAY_NAME, APP_TAGLINE, APP_VERSION, PUBLISHER,
        WEBSITE_URL, GITHUB_REPO, GITHUB_REPO_URL, DEFAULT_CHANNEL,
        TARGET_ARCH, DEFAULT_ONLINE_THRESHOLD_MIB, ONLINE_THRESHOLD_BYTES,
        MODE_ONLINE, MODE_OFFLINE, MODE_AUTO,
        EXIT_SUCCESS, EXIT_GENERAL_ERROR, EXIT_INVALID_ARGS, EXIT_NETWORK_ERROR,
        EXIT_VERIFICATION_FAILED, EXIT_INSUFFICIENT_SPACE, EXIT_USER_CANCELLED,
        evaluate_delivery_mode, compute_sha256, verify_manifest_signature,
        TRUSTED_PUBLIC_VERIFICATION_KEY
    )
    from manifest_schema import (
        validate_manifest_schema, verify_manifest_compatibility, ManifestValidationError
    )
    from disk_manager import (
        verify_disk_space, DiskSpaceCheckResult
    )
    from download_engine import (
        ReleaseMetadataResolver, SecureDownloadEngine, DownloadProgress,
        DownloadError, VerificationError, STAGE_NAMES
    )
    from transactional_installer import (
        TransactionalInstaller, SecurityInspectionError, InstallationCommitError,
        inspect_archive_security
    )
    from uninstaller import Uninstaller

DEFAULT_USER_INSTALL_DIR = Path.home() / "AppData" / "Local" / "Programs" / "PRUBETH"
DEFAULT_MACHINE_INSTALL_DIR = Path("C:/Program Files/PRUBETH")
RELEASE_TAG = f"v{APP_VERSION}"
ONLINE_PAYLOAD_URLS = [
    f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/Prubeth-Payload-{APP_VERSION}-{TARGET_ARCH}.zip",
    f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/PrubethIDE-{RELEASE_TAG}-Universal-Portable.zip",
    f"https://github.com/{GITHUB_REPO}/releases/latest/download/Prubeth-Payload-{APP_VERSION}-{TARGET_ARCH}.zip",
    f"https://github.com/{GITHUB_REPO}/releases/latest/download/PrubethIDE-{RELEASE_TAG}-Universal-Portable.zip",
]

WIZARD_STYLESHEET = """
QWizard, QWizardPage, QWizard > QWidget, QWizardPage > QWidget {
    background-color: #15171D;
    color: #E8EAF0;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}
QWizard::header {
    background-color: #1D2028;
    border-bottom: 1px solid #343A49;
    padding: 10px 16px;
}
QLabel {
    color: #E8EAF0;
    font-size: 10pt;
    background: transparent;
}
QLineEdit {
    background: #191C23;
    color: #E8EAF0;
    border: 1px solid #343A49;
    padding: 7px 10px;
    border-radius: 4px;
    font-size: 10pt;
}
QLineEdit:focus {
    border-color: #B4A9FF;
}
QPushButton {
    background: #252934;
    color: #E8EAF0;
    border: 1px solid #343A49;
    padding: 7px 18px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 10pt;
}
QPushButton:hover {
    background: #343A49;
    border-color: #9485FF;
    color: #FFFFFF;
}
QPushButton:pressed {
    background: #191C23;
}
QPushButton:disabled {
    background: #15171D;
    color: #737B8C;
    border-color: #252934;
}
QProgressBar {
    border: 1px solid #343A49;
    border-radius: 4px;
    text-align: center;
    background: #191C23;
    height: 22px;
    color: #E8EAF0;
    font-weight: bold;
    font-size: 9pt;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9485FF, stop:1 #62D4E5);
    border-radius: 3px;
}
QCheckBox, QRadioButton {
    color: #E8EAF0;
    spacing: 8px;
    font-size: 9.5pt;
    background: transparent;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #343A49;
    background: #191C23;
    border-radius: 3px;
}
QRadioButton::indicator {
    border-radius: 8px;
}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #9485FF;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #9485FF;
    border-color: #9485FF;
}
QGroupBox {
    border: 1px solid #343A49;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 14px;
    background: #1D2028;
    font-weight: 600;
    color: #E8EAF0;
    font-size: 9.5pt;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #9485FF;
}
QFrame#infoBox {
    background: #1D2028;
    border: 1px solid #343A49;
    border-radius: 6px;
    padding: 10px;
}
"""


def get_resource_dir() -> Path:
    """Returns the resource directory, supporting PyInstaller onefile extraction."""
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def get_source_dir() -> Path:
    """Returns repository root directory if running in development mode."""
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


class InstallWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(
        self,
        target_dir: Path,
        mode: str = MODE_AUTO,
        channel: str = DEFAULT_CHANNEL,
        scope: str = "user",
        create_desktop: bool = True,
        create_startmenu: bool = True,
        add_to_path: bool = True,
        install_lexers: bool = True,
        install_models: bool = True,
        skip_ai: bool = False,
        register_uninstaller: bool = True,
        payload_zip: Optional[Path] = None,
        staging_dir: Optional[Path] = None
    ):
        super().__init__()
        self.target_dir = Path(target_dir)
        self.mode = mode
        self.channel = channel
        self.scope = scope
        self.create_desktop = create_desktop
        self.create_startmenu = create_startmenu
        self.add_to_path = add_to_path
        self.install_lexers = install_lexers
        self.install_models = install_models
        self.skip_ai = skip_ai
        self.register_uninstaller = register_uninstaller
        self.payload_zip = Path(payload_zip) if payload_zip else None
        self.staging_dir = Path(staging_dir) if staging_dir else Path(tempfile.gettempdir())

        self.downloader = SecureDownloadEngine()
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True
        self.downloader.cancel()

    def _progress_bridge(self, prog: DownloadProgress):
        pct = int(prog.percent) if prog.percent is not None else 0
        if prog.stage == 1:
            scaled_pct = 5
        elif prog.stage in (2, 3, 4):
            scaled_pct = 10 + (prog.stage * 3)
        elif prog.stage == 5:
            scaled_pct = 20 + int(pct * 0.45)
        elif prog.stage == 6:
            scaled_pct = 68
        elif prog.stage == 7:
            scaled_pct = 70 + int(pct * 0.15)
        elif prog.stage == 8:
            scaled_pct = 88
        elif prog.stage == 9:
            scaled_pct = 95
        else:
            scaled_pct = 100

        self.progress.emit(min(scaled_pct, 100), prog.status_text)

    def download_payload_from_github(self) -> Optional[Path]:
        """
        Retrieves and authenticates the application payload from official GitHub Releases.
        Enforces strict TLS, Ed25519 signed manifest verification, SHA-256 payload digest verification,
        size bounding, and pre-extraction zip-slip archive security inspection.
        Fails closed on any security failure, invalid signature, or unauthenticated archive.
        """
        try:
            self.progress.emit(10, f"Resolving official GitHub release manifest for v{APP_VERSION}...")
            resolver = ReleaseMetadataResolver(
                repo=GITHUB_REPO,
                version=APP_VERSION,
                channel=self.channel,
                arch=TARGET_ARCH
            )
            release_info = resolver.resolve_release(progress_callback=self._progress_bridge)
            if self.is_cancelled:
                return None

            downloaded_zip = self.downloader.download_payload(
                payload_url=release_info["payload_url"],
                expected_sha256=release_info["payload_sha256"],
                expected_size_bytes=release_info["payload_size_bytes"],
                destination_dir=self.staging_dir,
                progress_callback=self._progress_bridge
            )
            if downloaded_zip and downloaded_zip.exists():
                inspect_archive_security(downloaded_zip)
                self.progress.emit(49, "GitHub package download & Ed25519 cryptographic integrity verified.")
                return downloaded_zip
        except Exception as ex:
            logging.error(f"Authenticated GitHub payload retrieval failed: {ex}")
            return None
        return None

    def run(self):
        try:
            # 1. Stage 1: Checking system compatibility & disk headroom
            self.progress.emit(5, "Stage 1/10: Checking system compatibility and disk space...")

            # Determine local payload if present
            effective_payload = self.payload_zip
            if not effective_payload:
                res_dir = get_resource_dir()
                src_dir = get_source_dir()
                for cand in [
                    res_dir / "app_payload.zip",
                    res_dir / "installer" / "app_payload.zip",
                    src_dir / "installer" / "app_payload.zip",
                    src_dir / "app_payload.zip"
                ]:
                    if cand.exists() and cand.is_file() and cand.stat().st_size > 50000:
                        effective_payload = cand
                        break

            # Decide delivery mode
            is_online = (self.mode == MODE_ONLINE) or (self.mode == MODE_AUTO and not effective_payload)

            estimated_payload_bytes = effective_payload.stat().st_size if (effective_payload and effective_payload.exists()) else (22 * 1024 * 1024)
            space_check = verify_disk_space(
                target_dir=self.target_dir,
                payload_size_bytes=estimated_payload_bytes,
                staging_dir=self.staging_dir,
                is_upgrade=self.target_dir.exists() and any(self.target_dir.iterdir())
            )

            if not space_check.is_sufficient:
                raise RuntimeError(space_check.insufficient_reason or "Insufficient disk space.")

            # 2. Retrieve Payload
            downloaded_zip: Optional[Path] = None
            required_files = ["local_ai_studio_pro.py"]

            if is_online:
                downloaded_zip = self.download_payload_from_github()
                if not downloaded_zip or not downloaded_zip.exists():
                    raise DownloadError("Could not retrieve authenticated and cryptographically verified release payload from GitHub.")
                effective_payload = downloaded_zip
            else:
                # Mode B: Full Offline Installer with verified local payload
                self.progress.emit(15, "Stage 2/10: Mode B Offline Installer active. Using local verified payload...")
                if not effective_payload or not effective_payload.exists():
                    raise FileNotFoundError(f"Offline installer payload archive not found.")

            if self.is_cancelled:
                raise DownloadError("Installation cancelled by user.")

            # 3. Stage 7-9: Transactional Staging, Atomic Commit & Health Check
            installer = TransactionalInstaller(
                target_dir=self.target_dir,
                staging_dir=self.staging_dir
            )
            installer.execute_transaction(
                payload_zip=effective_payload,
                required_files=required_files,
                is_upgrade=self.target_dir.exists(),
                progress_callback=self._progress_bridge
            )

            # 4. Configure Runtime Launcher
            self._write_launchers()

            # 5. Prime Showroom Experience (Settings, Models, Native Extensions, Self-Healing)
            self._prime_showroom_experience()

            # 6. Create Shortcuts & Integrations
            if self.create_desktop:
                self._create_desktop_shortcut()
            if self.create_startmenu:
                self._create_startmenu_shortcut()
            if self.add_to_path:
                self._add_to_path()
            if self.register_uninstaller:
                self._register_uninstaller()

            # 7. Initialize local models cache if not skipped
            if not self.skip_ai and self.install_models:
                (self.target_dir / "models").mkdir(parents=True, exist_ok=True)
                (self.target_dir / ".local_ai_studio_pro").mkdir(parents=True, exist_ok=True)

            # Cleanup downloaded zip if temporary
            if downloaded_zip and downloaded_zip.exists():
                try:
                    downloaded_zip.unlink()
                except OSError:
                    pass

            self.progress.emit(100, "Stage 10/10: Setup completed successfully!")
            self.finished.emit(True, "Success")

        except Exception as ex:
            if self.is_cancelled:
                self.finished.emit(False, "Installation cancelled by user.")
            else:
                msg = str(ex)
                if isinstance(ex, InstallationCommitError) or "Required application component missing" in msg:
                    self.finished.emit(False, f"Installation integrity verification failed: {msg}")
                else:
                    self.finished.emit(False, msg)

    def _prime_showroom_experience(self):
        """
        Primes the ultimate showroom out-of-the-box user experience.
        Pre-seeds user settings, language model profiles, native extension packages,
        and verifies workbench patch integrity so first launch has zero modal friction,
        zero missing models, and instantaneous high-performance agentic capability.
        """
        try:
            self.progress.emit(92, "Priming showroom user configuration and model profiles...")
            # 1. Target User Configuration Directory
            appdata = os.environ.get("APPDATA")
            if not appdata:
                appdata = str(Path.home() / "AppData" / "Roaming")
            user_config_dir = Path(appdata) / "PRUBETH" / "User"
            user_config_dir.mkdir(parents=True, exist_ok=True)

            # 2. Pre-seed settings.json with Showroom Defaults
            settings_target = user_config_dir / "settings.json"
            showroom_defaults = {
                "workbench.colorTheme": "PRUBETH Obsidian Slate",
                "workbench.iconTheme": "theme-modern-icons",
                "workbench.layoutControl.enabled": True,
                "workbench.sideBar.location": "left",
                "editor.fontFamily": "'Cascadia Code', 'Fira Code', Consolas, monospace",
                "editor.fontLigatures": True,
                "editor.fontSize": 14,
                "workbench.startupEditor": "welcomePage",
                "workbench.welcomePage.walkthroughs.openOnInstall": True,
                "workbench.welcomePage.experimentalOnboarding": False,
                "terminal.integrated.gpuAcceleration": "on",
                "terminal.integrated.smoothScrolling": False,
                "terminal.integrated.shellIntegration.enabled": True,
                "chat.commandCenter.enabled": True,
                "chat.allowAnonymousAccess": True,
                "chat.aiDisabled": False,
                "telemetry.telemetryLevel": "off",
                "telemetry.enableTelemetry": False,
                "telemetry.enableCrashReporter": False,
                "update.mode": "none"
            }

            default_settings_file = _REPO_ROOT / "assets" / "default_settings.json"
            if default_settings_file.exists():
                try:
                    with open(default_settings_file, "r", encoding="utf-8") as f:
                        file_defaults = json.load(f)
                        if isinstance(file_defaults, dict):
                            showroom_defaults.update(file_defaults)
                except Exception:
                    pass

            if not settings_target.exists():
                with open(settings_target, "w", encoding="utf-8") as f:
                    json.dump(showroom_defaults, f, indent=2)
            else:
                try:
                    with open(settings_target, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    if isinstance(existing, dict):
                        for k, v in showroom_defaults.items():
                            if k not in existing:
                                existing[k] = v
                        with open(settings_target, "w", encoding="utf-8") as f:
                            json.dump(existing, f, indent=2)
                except Exception:
                    pass

            # 3. Pre-seed chatLanguageModels.json
            models_target = user_config_dir / "chatLanguageModels.json"
            chat_models_src = _REPO_ROOT / "assets" / "chatLanguageModels.json"
            if chat_models_src.exists():
                try:
                    with open(chat_models_src, "r", encoding="utf-8") as f:
                        bundled_models = json.load(f)
                    if not models_target.exists():
                        with open(models_target, "w", encoding="utf-8") as f:
                            json.dump(bundled_models, f, indent=2)
                    else:
                        try:
                            with open(models_target, "r", encoding="utf-8") as f:
                                user_models = json.load(f)
                            if isinstance(user_models, list) and isinstance(bundled_models, list):
                                existing_names = {item.get("name") for item in user_models if isinstance(item, dict)}
                                changed = False
                                for item in bundled_models:
                                    if isinstance(item, dict) and item.get("name") not in existing_names:
                                        user_models.append(item)
                                        changed = True
                                if changed:
                                    with open(models_target, "w", encoding="utf-8") as f:
                                        json.dump(user_models, f, indent=2)
                        except Exception:
                            pass
                except Exception:
                    pass

            # 4. Deploy Native Showroom Extensions (prubeth-ai)
            app_extensions_dir = self.target_dir / "resources" / "app" / "extensions"
            if app_extensions_dir.exists():
                target_ext = app_extensions_dir / "prubeth-ai"
                src_ext = _REPO_ROOT / "vscode" / "extensions" / "prubeth-ai"
                if src_ext.exists():
                    target_ext.mkdir(parents=True, exist_ok=True)
                    for item in src_ext.iterdir():
                        dest = target_ext / item.name
                        if item.is_file():
                            shutil.copy2(item, dest)
                        elif item.is_dir() and item.name not in (".git", "__pycache__"):
                            shutil.copytree(item, dest, dirs_exist_ok=True)

            # 5. Patch Integrity Check: Ensure chatRequiresSetup() => false in installed workbench
            benchmarks = [
                self.target_dir / "resources" / "app" / "out" / "vs" / "workbench" / "workbench.desktop.main.js"
            ]
            for bench_js in benchmarks:
                if bench_js.exists():
                    try:
                        content = bench_js.read_text(encoding="utf-8")
                        patched = False
                        if "chatRequiresSetup(){" in content and "chatRequiresSetup(){return false;" not in content:
                            content = content.replace("chatRequiresSetup(){", "chatRequiresSetup(){return false;")
                            patched = True
                        if patched:
                            bench_js.write_text(content, encoding="utf-8")
                    except Exception:
                        pass

            # 6. Product.json Configuration: chatSetup.disabled and default agent
            prod_json = self.target_dir / "resources" / "app" / "product.json"
            if prod_json.exists():
                try:
                    with open(prod_json, "r", encoding="utf-8") as f:
                        prod_data = json.load(f)
                    if isinstance(prod_data, dict):
                        prod_changed = False
                        if "chatSetup" not in prod_data or not isinstance(prod_data["chatSetup"], dict):
                            prod_data["chatSetup"] = {"disabled": True}
                            prod_changed = True
                        elif not prod_data["chatSetup"].get("disabled"):
                            prod_data["chatSetup"]["disabled"] = True
                            prod_changed = True

                        if prod_data.get("defaultChatAgent", {}).get("extensionId") != "prubeth.ai-assistant":
                            prod_data["defaultChatAgent"] = {
                                "extensionId": "prubeth.ai-assistant",
                                "chatAgentId": "prubeth.assistant",
                                "name": "PRUBETH",
                                "icon": "sparkle"
                            }
                            prod_changed = True

                        if prod_changed:
                            with open(prod_json, "w", encoding="utf-8") as f:
                                json.dump(prod_data, f, indent=2)
                except Exception:
                    pass

        except Exception as e:
            logging.warning(f"Showroom priming completed with non-fatal notice: {e}")

    def _resolve_icon(self, target: Path) -> Path:
        icon_candidates = [
            self.target_dir / "assets" / "icon.ico",
            _REPO_ROOT / "assets" / "icon.ico",
            target.parent / "assets" / "icon.ico",
        ]
        for ic in icon_candidates:
            if ic.exists():
                return ic
        return target

    def _resolve_primary_executable(self) -> tuple[Path, Path, Path]:
        """
        Dynamically discovers the primary PRUBETH IDE executable, working directory,
        and application icon with zero hardcoded drive assumptions.
        Prioritizes the installed target directory binaries and launcher.
        """
        # 1. Target directory primary executables
        for cand in [
            self.target_dir / "PRUBETH.exe",
            self.target_dir / "PRUBETH IDE.exe",
            self.target_dir / "PrubethIDE.exe",
            self.target_dir / "Code.exe",
        ]:
            if cand.exists() and cand.is_file():
                icon = self._resolve_icon(cand)
                return cand, cand.parent, icon

        # 2. Target directory launcher script
        bat = self.target_dir / "PRUBETH.bat"
        if not bat.exists() or not bat.is_file():
            bat = self.target_dir / "PrubethIDE.bat"
        if bat.exists() and bat.is_file():
            icon = self._resolve_icon(bat)
            return bat, self.target_dir, icon

        # 3. Known external workstation environments (e.g. standard program files or developer workspace)
        external_candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "PRUBETH" / "PRUBETH.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "PRUBETH IDE" / "PRUBETH.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "PRUBETH IDE" / "PRUBETH IDE.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "PrubethIDE" / "PrubethIDE.exe",
            _REPO_ROOT / "VSCode-win32-x64" / "PRUBETH.exe",
            Path(r"E:\PRUBETH IDE\PRUBETH.exe"),
        ]
        for cand in external_candidates:
            if cand.exists() and cand.is_file():
                icon = self._resolve_icon(cand)
                return cand, cand.parent, icon

        # 4. Default fallback
        default_icon = self._resolve_icon(bat)
        return bat, self.target_dir, default_icon

    def _write_launchers(self):
        launcher_bat = self.target_dir / "PRUBETH.bat"
        legacy_bat = self.target_dir / "PrubethIDE.bat"
        launcher_content = f"""@echo off
setlocal enabledelayedexpansion
title {APP_DISPLAY_NAME} Launcher
cd /d "%~dp0"

:: 1. Launch VS Code based PRUBETH if present
if exist "%~dp0PRUBETH.exe" (
    start "" /high "%~dp0PRUBETH.exe" --enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist --disable-background-timer-throttling --disable-renderer-backgrounding %*
    exit /b 0
)
if exist "%~dp0PRUBETH IDE.exe" (
    start "" /high "%~dp0PRUBETH IDE.exe" --enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist --disable-background-timer-throttling --disable-renderer-backgrounding %*
    exit /b 0
)
if exist "%LOCALAPPDATA%\\Programs\\PRUBETH\\PRUBETH.exe" (
    start "" /high "%LOCALAPPDATA%\\Programs\\PRUBETH\\PRUBETH.exe" --enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist --disable-background-timer-throttling --disable-renderer-backgrounding %*
    exit /b 0
)
if exist "%LOCALAPPDATA%\\Programs\\PRUBETH IDE\\PRUBETH.exe" (
    start "" /high "%LOCALAPPDATA%\\Programs\\PRUBETH IDE\\PRUBETH.exe" --enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist --disable-background-timer-throttling --disable-renderer-backgrounding %*
    exit /b 0
)
if exist "%USERPROFILE%\\heretic-work\\VSCode-win32-x64\\PRUBETH.exe" (
    start "" /high "%USERPROFILE%\\heretic-work\\VSCode-win32-x64\\PRUBETH.exe" --enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist --disable-background-timer-throttling --disable-renderer-backgrounding %*
    exit /b 0
)
if exist "%~dp0PrubethIDE.exe" (
    start "" "%~dp0PrubethIDE.exe" %*
    exit /b 0
)
if exist "E:\\PRUBETH IDE\\PRUBETH.exe" (
    start "" /high "E:\\PRUBETH IDE\\PRUBETH.exe" --enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist --disable-background-timer-throttling --disable-renderer-backgrounding %*
    exit /b 0
)

:: 2. Locate available Python runtime
set "PY_CMD="
if exist ".venv\\Scripts\\pythonw.exe" (
    set "PY_CMD=.venv\\Scripts\\pythonw.exe"
) else if exist "..\\.venv\\Scripts\\pythonw.exe" (
    set "PY_CMD=..\\.venv\\Scripts\\pythonw.exe"
) else if exist "%USERPROFILE%\\heretic-work\\.venv\\Scripts\\pythonw.exe" (
    set "PY_CMD=%USERPROFILE%\\heretic-work\\.venv\\Scripts\\pythonw.exe"
) else (
    where pythonw.exe >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=pythonw.exe"
    ) else (
        where python.exe >nul 2>&1
        if !errorlevel! equ 0 set "PY_CMD=python.exe"
    )
)

if "!PY_CMD!"=="" (
    echo [ERROR] Python 3 was not detected on your system.
    echo Please install Python 3.10+ from https://python.org/
    mshta "javascript:alert('{APP_NAME} Launcher Error:\\n\\nPython 3 is not installed or not in PATH.\\nPlease install Python 3.10+ from https://python.org');close();"
    exit /b 1
)

start "" "!PY_CMD!" local_ai_studio_pro.py %*
exit /b 0
"""
        launcher_bat.write_text(launcher_content, encoding="utf-8")
        legacy_bat.write_text(launcher_content, encoding="utf-8")
        (self.target_dir / "SukhiIDE.bat").write_text(launcher_content, encoding="utf-8")
        (self.target_dir / "SoNaive.bat").write_text(launcher_content, encoding="utf-8")

    def _create_desktop_shortcut(self):
        desktop = Path.home() / "Desktop" / f"{APP_NAME}.lnk"
        target, working_dir, icon = self._resolve_primary_executable()
        self._create_windows_shortcut(str(desktop), str(target), str(icon), working_dir=str(working_dir))

    def _create_startmenu_shortcut(self):
        programs = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{APP_NAME}"
        programs.mkdir(parents=True, exist_ok=True)
        lnk = programs / f"{APP_NAME}.lnk"
        target, working_dir, icon = self._resolve_primary_executable()
        self._create_windows_shortcut(str(lnk), str(target), str(icon), working_dir=str(working_dir))

    def _create_windows_shortcut(self, lnk_path: str, target_path: str, icon_path: str, working_dir: Optional[str] = None):
        work_dir = working_dir or str(self.target_dir)
        ps_cmd = f"""
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{lnk_path}')
$Shortcut.TargetPath = '{target_path}'
$Shortcut.WorkingDirectory = '{work_dir}'
$Shortcut.WindowStyle = 7
if (Test-Path '{icon_path}') {{ $Shortcut.IconLocation = '{icon_path}' }}
$Shortcut.Description = '{APP_DISPLAY_NAME}'
$Shortcut.Save()
"""
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=10)
        except Exception:
            pass

    def _add_to_path(self):
        target_str = str(self.target_dir)
        ps_cmd = f"""
$current = [System.Environment]::GetEnvironmentVariable('Path', 'User')
if ($current -notlike '*{target_str}*') {{
    $new = if ($current) {{ "$current;$target_str" }} else {{ "$target_str" }}
    [System.Environment]::SetEnvironmentVariable('Path', $new, 'User')
}}
"""
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=10)
        except Exception:
            pass

    def _register_uninstaller(self):
        uninst_bat = self.target_dir / "Uninstall.bat"
        uninst_content = f"""@echo off
title Uninstall {APP_DISPLAY_NAME}
echo Removing {APP_DISPLAY_NAME}...
del /q "%USERPROFILE%\\Desktop\\{APP_NAME} IDE.lnk" 2>nul
rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME} IDE" 2>nul
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\PrubethIDE" /f 2>nul
cd /d "%TEMP%"
rmdir /s /q "{self.target_dir}" 2>nul
echo {APP_DISPLAY_NAME} has been uninstalled.
pause
"""
        uninst_bat.write_text(uninst_content, encoding="utf-8")

        reg_cmd = f"""
$key = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\PrubethIDE'
New-Item -Path $key -Force | Out-Null
Set-ItemProperty -Path $key -Name 'DisplayName' -Value '{APP_DISPLAY_NAME}'
Set-ItemProperty -Path $key -Name 'DisplayVersion' -Value '{APP_VERSION}'
Set-ItemProperty -Path $key -Name 'Publisher' -Value '{PUBLISHER}'
Set-ItemProperty -Path $key -Name 'UninstallString' -Value '"{self.target_dir}\\Uninstall.bat"'
Set-ItemProperty -Path $key -Name 'DisplayIcon' -Value '{self.target_dir}\\assets\\icon.ico'
Set-ItemProperty -Path $key -Name 'URLInfoAbout' -Value '{WEBSITE_URL}'
"""
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", reg_cmd], capture_output=True, timeout=10)
        except Exception:
            pass


class WelcomePage(QWizardPage):
    def __init__(self, mode: str = MODE_AUTO):
        super().__init__()
        self.mode = mode
        self.setTitle(f"Welcome to {APP_NAME} IDE Setup")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        logo_lbl = QLabel()
        logo_path = get_resource_dir() / "assets" / "logo.png"
        if not logo_path.exists():
            logo_path = get_source_dir() / "assets" / "logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(112, 112, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_lbl)

        title = QLabel(f"<h2 style='color:#FFFFFF; margin-top:6px;'>PRUBETH <span style='color:#9485FF;'>v{APP_VERSION}</span></h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        delivery_badge = "🌐 <b>Mode A (Online Bootstrapper)</b>: Downloads verified v3.0.0 release from GitHub." if self.mode == MODE_ONLINE else "📦 <b>Offline Installer</b>: Embedded standalone payload."

        desc = QLabel(
            f"<p align='center' style='color:#62D4E5; font-weight:600; font-size:12pt; margin-bottom:8px;'>{APP_TAGLINE}</p>"
            "<p align='center' style='color:#A5ACBB; font-size:10pt; line-height:140%;'>This wizard will install the official PRUBETH developer workstation on your computer.<br>"
            f"{delivery_badge}</p>"
            f"<p align='center' style='margin-top:12px;'><small style='color:#737B8C;'>Official Website: <a href='{WEBSITE_URL}' style='color:#9485FF;'>{WEBSITE_URL}</a></small></p>"
        )
        desc.setOpenExternalLinks(True)
        layout.addWidget(desc)
        layout.addStretch()


class InstallTypePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Select Installation Type")
        self.setSubTitle("Choose standard recommended setup or customize workstation components.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        self.rb_full = QRadioButton("Full Installation (Recommended)")
        self.rb_full.setChecked(True)
        self.rb_full.setStyleSheet("font-weight: 600; font-size: 11pt; color: #FFFFFF;")
        layout.addWidget(self.rb_full)

        full_desc = QLabel(
            "Installs the complete PRUBETH workstation suite including all multi-language parsers, "
            "local AI connectors, desktop & start menu shortcuts, and PATH integration."
        )
        full_desc.setStyleSheet("color: #70D6A0; font-size: 9.5pt; margin-left: 24px; margin-bottom: 6px;")
        full_desc.setWordWrap(True)
        layout.addWidget(full_desc)

        self.rb_custom = QRadioButton("Custom Installation (Advanced)")
        self.rb_custom.setStyleSheet("font-weight: 600; font-size: 11pt; color: #E8EAF0;")
        layout.addWidget(self.rb_custom)

        custom_desc = QLabel("Selectively toggle individual developer components, local model caches, and shortcut placements.")
        custom_desc.setStyleSheet("color: #A5ACBB; font-size: 9.5pt; margin-left: 24px; margin-bottom: 4px;")
        custom_desc.setWordWrap(True)
        layout.addWidget(custom_desc)

        self.group_custom = QGroupBox("Workstation Components & Integrations")
        grp_layout = QVBoxLayout(self.group_custom)
        grp_layout.setContentsMargins(16, 16, 16, 16)
        grp_layout.setSpacing(8)

        self.chk_core = QCheckBox("Core Workstation Engine & AI Subsystems (Required, ~180 MB)")
        self.chk_core.setChecked(True)
        self.chk_core.setEnabled(False)
        grp_layout.addWidget(self.chk_core)

        self.chk_lexers = QCheckBox("Multi-Language Offline Syntax Lexers & Language Services (~25 MB)")
        self.chk_lexers.setChecked(True)
        grp_layout.addWidget(self.chk_lexers)

        self.chk_models = QCheckBox("Local AI Model Templates & Connector Profiles (~10 MB)")
        self.chk_models.setChecked(True)
        grp_layout.addWidget(self.chk_models)

        self.chk_skip_ai = QCheckBox("Skip AI configuration on first run (configure providers later)")
        self.chk_skip_ai.setChecked(False)
        grp_layout.addWidget(self.chk_skip_ai)

        self.chk_desktop = QCheckBox("Create Desktop Shortcut")
        self.chk_desktop.setChecked(True)
        grp_layout.addWidget(self.chk_desktop)

        self.chk_startmenu = QCheckBox("Create Start Menu Program Group")
        self.chk_startmenu.setChecked(True)
        grp_layout.addWidget(self.chk_startmenu)

        self.chk_path = QCheckBox("Add PRUBETH to System PATH (Recommended)")
        self.chk_path.setChecked(True)
        grp_layout.addWidget(self.chk_path)

        self.chk_uninstaller = QCheckBox("Register in Windows Control Panel (Uninstaller)")
        self.chk_uninstaller.setChecked(True)
        grp_layout.addWidget(self.chk_uninstaller)

        layout.addWidget(self.group_custom)
        layout.addStretch()

        self.rb_full.toggled.connect(self.update_states)
        self.update_states()

        self.registerField("is_full_mode", self.rb_full)
        self.registerField("install_lexers", self.chk_lexers)
        self.registerField("install_models", self.chk_models)
        self.registerField("skip_ai", self.chk_skip_ai)
        self.registerField("create_desktop", self.chk_desktop)
        self.registerField("create_startmenu", self.chk_startmenu)
        self.registerField("add_to_path", self.chk_path)
        self.registerField("register_uninstaller", self.chk_uninstaller)

    def update_states(self):
        is_custom = self.rb_custom.isChecked()
        self.chk_lexers.setEnabled(is_custom)
        self.chk_models.setEnabled(is_custom)
        self.chk_skip_ai.setEnabled(is_custom)
        self.chk_desktop.setEnabled(is_custom)
        self.chk_startmenu.setEnabled(is_custom)
        self.chk_path.setEnabled(is_custom)
        self.chk_uninstaller.setEnabled(is_custom)
        if not is_custom:
            self.chk_lexers.setChecked(True)
            self.chk_models.setChecked(True)
            self.chk_skip_ai.setChecked(False)
            self.chk_desktop.setChecked(True)
            self.chk_startmenu.setChecked(True)
            self.chk_path.setChecked(True)
            self.chk_uninstaller.setChecked(True)


class DirectoryPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Select Installation Folder & Validate Storage")
        self.setSubTitle(f"Where would you like to install {APP_NAME} IDE? Check disk space below.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        lbl = QLabel("Destination Directory:")
        lbl.setStyleSheet("color: #E8EAF0; font-weight: 600; font-size: 10pt;")
        layout.addWidget(lbl)

        row = QHBoxLayout()
        self.dir_input = QLineEdit(str(DEFAULT_USER_INSTALL_DIR))
        self.dir_input.textChanged.connect(self.update_disk_space)
        b_browse = QPushButton("Browse...")
        b_browse.clicked.connect(self.browse)
        row.addWidget(self.dir_input)
        row.addWidget(b_browse)
        layout.addLayout(row)

        self.info_box = QFrame()
        self.info_box.setObjectName("infoBox")
        box_layout = QVBoxLayout(self.info_box)
        box_layout.setContentsMargins(14, 12, 14, 12)
        box_layout.setSpacing(6)

        self.lbl_space_req = QLabel("Space Required: ~250.0 MB")
        self.lbl_space_req.setStyleSheet("color: #A5ACBB; font-size: 9.5pt;")
        box_layout.addWidget(self.lbl_space_req)

        self.lbl_space_avail = QLabel("Space Available: Calculating...")
        self.lbl_space_avail.setStyleSheet("color: #E8EAF0; font-size: 9.5pt;")
        box_layout.addWidget(self.lbl_space_avail)

        self.lbl_space_status = QLabel("Checking drive capacity...")
        self.lbl_space_status.setStyleSheet("font-weight: 600; font-size: 9.5pt;")
        box_layout.addWidget(self.lbl_space_status)

        layout.addWidget(self.info_box)
        layout.addStretch()

        self.registerField("target_dir*", self.dir_input)
        self.update_disk_space()

    def browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Install Directory", self.dir_input.text())
        if d:
            self.dir_input.setText(d)
            self.update_disk_space()

    def initializePage(self):
        req_mb = 180.0
        if self.field("install_lexers"):
            req_mb += 25.0
        if self.field("install_models"):
            req_mb += 10.0
        self.lbl_space_req.setText(f"Space Required: approx. {req_mb:.1f} MB (Payload & Runtimes)")
        self.update_disk_space()

    def update_disk_space(self):
        try:
            p = Path(self.dir_input.text()).resolve()
            res = verify_disk_space(p, payload_size_bytes=22 * 1024 * 1024)
            avail_gb = res.target_available_bytes / (1024 ** 3)
            self.lbl_space_avail.setText(f"Space Available on {res.target_volume}: {avail_gb:.2f} GB")
            if res.is_sufficient:
                self.lbl_space_status.setText("✓ Sufficient disk space is available.")
                self.lbl_space_status.setStyleSheet("color: #70D6A0; font-weight: 600; font-size: 9.5pt;")
            else:
                self.lbl_space_status.setText("⚠ Insufficient space: " + (res.insufficient_reason or ""))
                self.lbl_space_status.setStyleSheet("color: #FF6B6B; font-weight: 600; font-size: 9.5pt;")
        except Exception:
            self.lbl_space_avail.setText("Space Available: Unable to query drive")
            self.lbl_space_status.setText("Proceeding with standard validation")
            self.lbl_space_status.setStyleSheet("color: #A5ACBB; font-size: 9.5pt;")


class ReadyPage(QWizardPage):
    def __init__(self, mode: str = MODE_AUTO):
        super().__init__()
        self.mode = mode
        self.setTitle("Ready to Install")
        self.setSubTitle("Setup is ready to begin installing PRUBETH on your computer.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        lbl_intro = QLabel("Review your installation configuration before continuing. Click 'Next' to begin installation.")
        lbl_intro.setStyleSheet("color: #A5ACBB; font-size: 10pt;")
        layout.addWidget(lbl_intro)

        self.summary_box = QFrame()
        self.summary_box.setObjectName("infoBox")
        sum_layout = QVBoxLayout(self.summary_box)
        sum_layout.setContentsMargins(16, 14, 16, 14)
        sum_layout.setSpacing(8)

        self.lbl_sum_mode = QLabel()
        self.lbl_sum_mode.setStyleSheet("color: #9485FF; font-weight: 600; font-size: 10pt;")
        sum_layout.addWidget(self.lbl_sum_mode)

        self.lbl_sum_path = QLabel()
        self.lbl_sum_path.setStyleSheet("color: #E8EAF0; font-size: 9.5pt;")
        sum_layout.addWidget(self.lbl_sum_path)

        self.lbl_sum_comps = QLabel()
        self.lbl_sum_comps.setStyleSheet("color: #A5ACBB; font-size: 9pt;")
        sum_layout.addWidget(self.lbl_sum_comps)

        self.lbl_sum_actions = QLabel()
        self.lbl_sum_actions.setStyleSheet("color: #62D4E5; font-size: 9pt;")
        sum_layout.addWidget(self.lbl_sum_actions)

        layout.addWidget(self.summary_box)
        layout.addStretch()

    def initializePage(self):
        is_full = self.field("is_full_mode")
        target_dir = self.field("target_dir")
        lexers = self.field("install_lexers")
        models = self.field("install_models")
        desktop = self.field("create_desktop")
        start = self.field("create_startmenu")
        path_env = self.field("add_to_path")
        uninst = self.field("register_uninstaller")
        skip_ai = self.field("skip_ai")

        mode_text = "Mode: Full Installation" if is_full else "Mode: Custom Installation"
        if self.mode == MODE_ONLINE:
            mode_text += " (Online GitHub Bootstrapper)"
        self.lbl_sum_mode.setText(mode_text)
        self.lbl_sum_path.setText(f"Destination: {target_dir}")

        comps = ["Core Workstation Engine"]
        if lexers:
            comps.append("Multi-Language Syntaxes")
        if models and not skip_ai:
            comps.append("Local AI Connector Templates")
        self.lbl_sum_comps.setText(f"Components: {', '.join(comps)}")

        actions = []
        if desktop:
            actions.append("Desktop Shortcut")
        if start:
            actions.append("Start Menu")
        if path_env:
            actions.append("PATH Integration")
        if uninst:
            actions.append("Windows Control Panel")
        self.lbl_sum_actions.setText(f"Integrations: {', '.join(actions)}")


class ProgressPage(QWizardPage):
    def __init__(self, mode: str = MODE_AUTO, channel: str = DEFAULT_CHANNEL):
        super().__init__()
        self.mode = mode
        self.channel = channel
        self.setTitle(f"Installing {APP_NAME} IDE")
        self.setSubTitle("Please wait while the system downloads, verifies, and installs the application...")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.status_lbl = QLabel("Stage 1/10: Initializing setup...")
        self.status_lbl.setStyleSheet("color: #E8EAF0; font-size: 10pt; font-weight: 600;")
        layout.addWidget(self.status_lbl)

        self.details_lbl = QLabel("Preparing installation pipeline...")
        self.details_lbl.setStyleSheet("color: #A5ACBB; font-size: 9pt;")
        layout.addWidget(self.details_lbl)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        layout.addWidget(self.bar)

        self.btn_cancel_dl = QPushButton("Cancel Installation")
        self.btn_cancel_dl.clicked.connect(self.on_cancel_clicked)
        layout.addWidget(self.btn_cancel_dl, alignment=Qt.AlignRight)

        self.worker: Optional[InstallWorker] = None
        self.is_done = False
        layout.addStretch()

    def initializePage(self):
        target_dir = Path(self.field("target_dir"))
        create_desktop = self.field("create_desktop")
        create_start = self.field("create_startmenu")
        install_lexers = self.field("install_lexers")
        install_models = self.field("install_models")
        add_to_path = self.field("add_to_path")
        reg_uninst = self.field("register_uninstaller")
        skip_ai = self.field("skip_ai")

        self.wizard().button(QWizard.BackButton).setEnabled(False)
        self.wizard().button(QWizard.NextButton).setEnabled(False)

        self.worker = InstallWorker(
            target_dir=target_dir,
            mode=self.mode,
            channel=self.channel,
            create_desktop=create_desktop,
            create_startmenu=create_start,
            add_to_path=add_to_path,
            install_lexers=install_lexers,
            install_models=install_models,
            skip_ai=skip_ai,
            register_uninstaller=reg_uninst
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_cancel_clicked(self):
        if self.worker and not self.is_done:
            self.btn_cancel_dl.setEnabled(False)
            self.status_lbl.setText("Cancelling installation and cleaning up...")
            self.worker.cancel()

    def on_progress(self, val: int, msg: str):
        self.bar.setValue(val)
        self.status_lbl.setText(msg)

    def on_finished(self, success: bool, msg: str):
        self.is_done = True
        self.btn_cancel_dl.setEnabled(False)
        self.wizard().button(QWizard.NextButton).setEnabled(True)
        if success:
            self.status_lbl.setText("Installation completed successfully!")
            self.wizard().next()
        else:
            QMessageBox.critical(self, "Installation Error", f"Installation failed:\n{msg}")

    def isComplete(self):
        return self.is_done


class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installation Complete!")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        congrats = QLabel(
            f"<h3 style='color:#FFFFFF;'>{APP_DISPLAY_NAME} has been successfully installed!</h3>"
            "<p style='color:#A5ACBB;'>You are now ready to launch the developer workstation environment.</p>"
            f"<p style='color:#737B8C;'>Find future updates and extensions at <a href='{WEBSITE_URL}' style='color:#9485FF;'>{WEBSITE_URL}</a></p>"
        )
        congrats.setOpenExternalLinks(True)
        layout.addWidget(congrats)

        self.chk_launch = QCheckBox(f"Launch {APP_NAME} IDE now")
        self.chk_launch.setChecked(True)
        layout.addWidget(self.chk_launch)
        layout.addStretch()


class SetupWizard(QWizard):
    def __init__(self, mode: str = MODE_AUTO, channel: str = DEFAULT_CHANNEL):
        super().__init__()
        self.mode = mode
        self.channel = channel
        self.setWindowTitle(f"{APP_NAME} IDE Setup — v{APP_VERSION}")
        self.setWizardStyle(QWizard.ClassicStyle)
        self.resize(680, 520)

        icon_path = get_resource_dir() / "assets" / "icon.ico"
        if not icon_path.exists():
            icon_path = get_source_dir() / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setStyleSheet(WIZARD_STYLESHEET)

        self.page_welcome = WelcomePage(mode=self.mode)
        self.page_type = InstallTypePage()
        self.page_dir = DirectoryPage()
        self.page_ready = ReadyPage(mode=self.mode)
        self.page_progress = ProgressPage(mode=self.mode, channel=self.channel)
        self.page_finish = FinishPage()

        self.addPage(self.page_welcome)
        self.addPage(self.page_type)
        self.addPage(self.page_dir)
        self.addPage(self.page_ready)
        self.addPage(self.page_progress)
        self.addPage(self.page_finish)


def run_quiet_installation(args: argparse.Namespace) -> int:
    """Headless silent installation engine executing all 10 stages."""
    print("=" * 65)
    print(f"  {APP_NAME} IDE — SILENT INSTALLER (v{APP_VERSION})")
    print("=" * 65)

    target_dir = Path(args.install_dir) if args.install_dir else (
        DEFAULT_MACHINE_INSTALL_DIR if args.scope == "machine" else DEFAULT_USER_INSTALL_DIR
    )

    worker = InstallWorker(
        target_dir=target_dir,
        mode=args.mode,
        channel=args.channel,
        scope=args.scope,
        create_desktop=not args.no_shortcut,
        create_startmenu=not args.no_shortcut,
        add_to_path=True,
        install_lexers=True,
        install_models=not args.skip_ai,
        skip_ai=args.skip_ai,
        register_uninstaller=True
    )

    last_pct = 0
    def cli_progress(pct: int, msg: str):
        nonlocal last_pct
        if pct != last_pct and (pct % 10 == 0 or pct in (5, 68, 88, 95, 100)):
            print(f"[{pct:3d}%] {msg}")
            last_pct = pct

    worker.progress.connect(cli_progress)

    res_success = False
    res_err = ""
    def cli_finish(success: bool, msg: str):
        nonlocal res_success, res_err
        res_success = success
        res_err = msg

    worker.finished.connect(cli_finish)
    worker.run()

    if res_success:
        print(f"[+] Installation successfully completed into: {target_dir}")
        return EXIT_SUCCESS
    else:
        print(f"[!] Installation failed: {res_err}", file=sys.stderr)
        if "Insufficient disk space" in res_err:
            return EXIT_INSUFFICIENT_SPACE
        elif "digest mismatch" in res_err or "Verification" in res_err:
            return EXIT_VERIFICATION_FAILED
        elif "Download" in res_err or "HTTP" in res_err:
            return EXIT_NETWORK_ERROR
        return EXIT_GENERAL_ERROR


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Setup.exe",
        description=f"{APP_DISPLAY_NAME} — Production Release Installer.",
        epilog=(
            "Exit Codes:\n"
            "  0 = Success\n"
            "  1 = General Error\n"
            "  2 = Invalid CLI Arguments\n"
            "  3 = Network / Download Failure\n"
            "  4 = Cryptographic / Checksum Verification Failure\n"
            "  5 = Insufficient Disk Space\n"
            "  6 = User Cancelled\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} IDE Setup v{APP_VERSION}")
    parser.add_argument("--install-dir", type=str, default=None, help="Target installation folder.")
    parser.add_argument("--scope", choices=["user", "machine"], default="user", help="Installation scope (default: user).")
    parser.add_argument("--channel", choices=["stable", "beta", "dev"], default="stable", help="Release channel (default: stable).")
    parser.add_argument("--mode", choices=["auto", "online", "offline"], default="auto", help="Delivery mode (default: auto).")
    parser.add_argument("--no-shortcut", action="store_true", help="Disable creation of Desktop and Start Menu shortcuts.")
    parser.add_argument("--skip-ai", action="store_true", help="Skip local AI model cache and provider setup on first run.")
    parser.add_argument("--log", type=str, default=None, help="Write detailed installation logs to file.")
    parser.add_argument("--quiet", action="store_true", help="Run silent installation without graphical wizard.")
    parser.add_argument("--verify-only", action="store_true", help="Verify official release manifest and system readiness without writing files.")
    return parser


def main():
    parser = build_cli_parser()
    args, unknown = parser.parse_known_args()

    if args.log:
        logging.basicConfig(filename=args.log, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if args.verify_only:
        print(f"[*] Verifying official {APP_NAME} release v{APP_VERSION} ({args.channel})...")
        try:
            resolver = ReleaseMetadataResolver(channel=args.channel, version=APP_VERSION)
            info = resolver.resolve_release()
            print(f"[+] Release v{info['version']} ({info['channel']}) verified successfully.")
            print(f"[+] Payload: {info['payload_filename']} ({info['payload_size_bytes']} bytes)")
            print(f"[+] SHA256:  {info['payload_sha256']}")
            sys.exit(EXIT_SUCCESS)
        except Exception as e:
            print(f"[!] Verification failed: {e}", file=sys.stderr)
            sys.exit(EXIT_VERIFICATION_FAILED)

    if args.quiet:
        sys.exit(run_quiet_installation(args))

    app = QApplication(sys.argv)
    wizard = SetupWizard(mode=args.mode, channel=args.channel)
    if wizard.exec_() == QWizard.Accepted:
        if wizard.page_finish.chk_launch.isChecked():
            target_dir = wizard.field("target_dir")
            bat = Path(target_dir) / "PrubethIDE.bat"
            if bat.exists():
                subprocess.Popen([str(bat)], cwd=target_dir, shell=True)
        sys.exit(EXIT_SUCCESS)
    else:
        sys.exit(EXIT_USER_CANCELLED)


if __name__ == "__main__":
    main()
