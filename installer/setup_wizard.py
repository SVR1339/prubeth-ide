"""
PRUBETH IDE — Graphical Setup Wizard (Windows Installer).
Installs PRUBETH IDE into %LOCALAPPDATA%\\Programs\\PrubethIDE,
configures Desktop & Start Menu shortcuts, and registers in Windows Control Panel.
Official Website: https://www.bsvr.work/
"""
import os
import sys
import shutil
import subprocess
import zipfile
import time
import tempfile
import urllib.request
import ssl
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar,
    QFileDialog, QMessageBox, QFrame
)

APP_NAME = "Prudeth"
APP_DISPLAY_NAME = "Prudeth IDE — Bloom Edition"
APP_TAGLINE = "Bloom, ideas unfolding"
APP_VERSION = "3.0.0"
PUBLISHER = "BSVR Technologies"
WEBSITE_URL = "https://www.bsvr.work/"
PROJECTS_URL = "https://www.bsvr.work/#projects"
GITHUB_REPO = "imyouiamyou/prubeth-ide"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO}"
RELEASE_TAG = "v3.0.0"
ONLINE_PAYLOAD_URLS = [
    f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/PrubethIDE-v3.0.0-Universal-Portable.zip",
    f"https://github.com/{GITHUB_REPO}/releases/latest/download/PrubethIDE-v3.0.0-Universal-Portable.zip",
    f"https://github.com/{GITHUB_REPO}/archive/refs/tags/{RELEASE_TAG}.zip",
    f"https://github.com/{GITHUB_REPO}/archive/refs/heads/master.zip",
]
DEFAULT_INSTALL_DIR = Path.home() / "AppData" / "Local" / "Programs" / "PrudethIDE"


def get_resource_dir() -> Path:
    """Returns the resource directory, supporting PyInstaller onefile extraction."""
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def get_source_dir() -> Path:
    """Returns the repository source directory if running in development mode."""
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


class InstallWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, target_dir, create_desktop, create_startmenu, payload_zip=None):
        super().__init__()
        self.target_dir = Path(target_dir)
        self.create_desktop = create_desktop
        self.create_startmenu = create_startmenu
        self.payload_zip = payload_zip

    def download_payload_from_github(self) -> Path:
        """Downloads full application resource archive from GitHub with live progress updates."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        dest_temp = Path(tempfile.gettempdir()) / f"prubeth_github_payload_{int(time.time())}.zip"
        headers = {"User-Agent": f"PrubethIDE-Installer/{APP_VERSION} (Windows NT 10.0; Win64; x64)"}

        for url in ONLINE_PAYLOAD_URLS:
            try:
                self.progress.emit(12, f"Connecting to GitHub: {url.split('/')[2]}...")
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                    if resp.status not in (200, 302):
                        continue
                    total_bytes = int(resp.headers.get("content-length", 0))
                    downloaded = 0
                    chunk_size = 65536
                    with open(dest_temp, "wb") as f_out:
                        while True:
                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            f_out.write(chunk)
                            downloaded += len(chunk)
                            if total_bytes > 0:
                                pct = int(12 + (downloaded / total_bytes) * 36)
                                mb_done = downloaded / (1024 * 1024)
                                mb_tot = total_bytes / (1024 * 1024)
                                self.progress.emit(min(pct, 48), f"Downloading from GitHub: {mb_done:.1f} MB / {mb_tot:.1f} MB ({int((downloaded/total_bytes)*100)}%)...")
                            else:
                                mb_done = downloaded / (1024 * 1024)
                                self.progress.emit(25, f"Downloading from GitHub: {mb_done:.1f} MB...")
                    if dest_temp.exists() and dest_temp.stat().st_size > 1000:
                        try:
                            with zipfile.ZipFile(dest_temp, 'r') as z:
                                if z.testzip() is None:
                                    self.progress.emit(49, "GitHub package download & integrity verified.")
                                    return dest_temp
                        except Exception:
                            pass
            except Exception as ex:
                continue
        return None

    def run(self):
        try:
            self.progress.emit(10, "Preparing target installation directory...")
            self.target_dir.mkdir(parents=True, exist_ok=True)

            res_dir = get_resource_dir()
            src_dir = get_source_dir()
            installed_anything = False

            # 1. Determine payload archive
            effective_payload = None
            if self.payload_zip and Path(self.payload_zip).exists():
                effective_payload = Path(self.payload_zip)
            else:
                for cand in [
                    res_dir / "app_payload.zip",
                    res_dir / "installer" / "app_payload.zip",
                    res_dir / "PrubethIDE-v3.0.0-Universal-Portable.zip",
                    src_dir / "app_payload.zip",
                    src_dir / "installer" / "app_payload.zip",
                    src_dir / "PrubethIDE-v3.0.0-Universal-Portable.zip",
                    src_dir / "dist" / "PrubethIDE-v3.0.0-Universal-Portable.zip",
                ]:
                    if cand.exists() and cand.is_file() and cand.stat().st_size > 50000:
                        effective_payload = cand
                        break

            # 2. If no valid local payload exists and we're not running from full source tree, fetch from GitHub
            if not effective_payload and not (src_dir / "local_ai_studio_pro.py").exists():
                self.progress.emit(12, "Stand-alone installer detected. Fetching complete resources from GitHub...")
                downloaded = self.download_payload_from_github()
                if downloaded:
                    effective_payload = downloaded

            # 3. Extract payload archive if available
            if effective_payload and effective_payload.exists():
                self.progress.emit(50, f"Extracting application payload ({effective_payload.name})...")
                with zipfile.ZipFile(effective_payload, 'r') as z:
                    names = z.namelist()
                    top_prefix = None
                    dirs = [n for n in names if '/' in n]
                    if dirs:
                        first_top = dirs[0].split('/')[0] + '/'
                        if all(n.startswith(first_top) for n in names if n != first_top):
                            top_prefix = first_top

                    if top_prefix:
                        for member in z.infolist():
                            if member.filename.startswith(top_prefix):
                                rel = member.filename[len(top_prefix):]
                                if not rel:
                                    continue
                                out_p = self.target_dir / rel
                                if member.is_dir():
                                    out_p.mkdir(parents=True, exist_ok=True)
                                else:
                                    out_p.parent.mkdir(parents=True, exist_ok=True)
                                    with z.open(member) as src_m, open(out_p, "wb") as dst_m:
                                        shutil.copyfileobj(src_m, dst_m)
                    else:
                        z.extractall(self.target_dir)
                installed_anything = True
            else:
                # 4. Fall back to copying from available source/resource bases
                for cand in [src_dir / "dist" / "PrubethIDE", src_dir / "dist" / "SukhiIDE", src_dir / "dist" / "SoNaive"]:
                    if cand.exists() and cand.is_dir():
                        self.progress.emit(35, "Deploying standalone application binaries...")
                        shutil.copytree(cand, self.target_dir, dirs_exist_ok=True)
                        installed_anything = True
                        break

                search_bases = [src_dir, res_dir]
                core_files = [
                    "local_ai_studio_pro.py",
                    "README.md",
                    "LICENSE",
                    "ARCHITECTURE.md",
                    "CHANGELOG.md",
                    "INSTALL.md",
                    "DEVELOPER_EXTENSIONS_GUIDE.md",
                    "install.ps1",
                    "install.sh",
                    "requirements.txt",
                    "run_local_ai_studio_pro.bat",
                    "pyproject.toml",
                    "FINAL_RELEASE_VERIFICATION.md"
                ]

                self.progress.emit(45, "Verifying and synchronizing core modules...")
                for f in core_files:
                    for base in search_bases:
                        candidate = base / f
                        if candidate.exists() and candidate.is_file():
                            dest = self.target_dir / f
                            if not dest.exists():
                                shutil.copy2(candidate, dest)
                                installed_anything = True
                            break

                # Copy subsystem directories
                sub_dirs = [
                    "core", "workspace", "source_control", "language_services",
                    "debugging", "ai", "ui", "plugins", "assets", "tests",
                    "horizon_engine", "security_research"
                ]
                for sub in sub_dirs:
                    for base in search_bases:
                        sub_src = base / sub
                        if sub_src.exists() and sub_src.is_dir():
                            shutil.copytree(sub_src, self.target_dir / sub, dirs_exist_ok=True)
                            break

            # 5. Strict verification of installed payload
            has_exe = (
                (self.target_dir / "PrubethIDE.exe").exists() or
                (self.target_dir / "SukhiIDE.exe").exists() or
                (self.target_dir / "SoNaive.exe").exists()
            )
            has_py = (self.target_dir / "local_ai_studio_pro.py").exists()

            if not (has_exe or has_py):
                raise RuntimeError(
                    f"Installation integrity verification failed: neither 'PrubethIDE.exe' nor 'local_ai_studio_pro.py' "
                    f"could be installed to '{self.target_dir}'. "
                    f"The setup package does not contain an executable payload."
                )

            self.progress.emit(65, "Configuring runtime launcher and diagnostic wrappers...")
            # Create robust, self-diagnosing launcher batch files
            launcher_prubeth = self.target_dir / "PrubethIDE.bat"
            launcher_sukhi = self.target_dir / "SukhiIDE.bat"
            launcher_bat = self.target_dir / "SoNaive.bat"

            launcher_content = f"""@echo off
setlocal enabledelayedexpansion
title {APP_DISPLAY_NAME} Launcher
cd /d "%~dp0"

:: 1. If standalone executable is installed, launch it directly
if exist "PrubethIDE.exe" (
    start "" "PrubethIDE.exe" %*
    exit /b 0
)
if exist "SukhiIDE.exe" (
    start "" "SukhiIDE.exe" %*
    exit /b 0
)
if exist "SoNaive.exe" (
    start "" "SoNaive.exe" %*
    exit /b 0
)

:: 2. Locate available Python runtime
set "PY_CMD="
set "PY_CON="

if exist ".venv\\Scripts\\pythonw.exe" (
    set "PY_CMD=.venv\\Scripts\\pythonw.exe"
    set "PY_CON=.venv\\Scripts\\python.exe"
) else if exist "..\\.venv\\Scripts\\pythonw.exe" (
    set "PY_CMD=..\\.venv\\Scripts\\pythonw.exe"
    set "PY_CON=..\\.venv\\Scripts\\python.exe"
) else (
    where pythonw.exe >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=pythonw.exe"
        set "PY_CON=python.exe"
    ) else (
        where python.exe >nul 2>&1
        if !errorlevel! equ 0 (
            set "PY_CMD=python.exe"
            set "PY_CON=python.exe"
        )
    )
)

if "!PY_CMD!"=="" (
    echo [ERROR] Python 3 was not detected on your system.
    echo Please install Python 3.10+ from https://python.org/
    mshta "javascript:alert('{APP_NAME} Launcher Error:\\n\\nPython 3 is not installed or not in PATH.\\nPlease install Python 3.10+ from https://python.org');close();"
    pause
    exit /b 1
)

:: 3. Verify application file existence
if not exist "local_ai_studio_pro.py" (
    echo [ERROR] local_ai_studio_pro.py was not found in %~dp0
    mshta "javascript:alert('{APP_NAME} Launcher Error:\\n\\nApplication core file (local_ai_studio_pro.py) was not found in installation folder.');close();"
    pause
    exit /b 1
)

:: 4. Verify core dependencies
if exist "!PY_CON!" (
    "!PY_CON!" -c "import PyQt5, requests" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] Required libraries (PyQt5, requests) are not installed.
        echo Run: pip install -r requirements.txt
        mshta "javascript:alert('{APP_NAME} Launcher Warning:\\n\\nRequired libraries (PyQt5, requests) were not found in Python environment.\\nPlease run: pip install -r requirements.txt');close();"
    )
)

:: 5. Launch application
start "" "!PY_CMD!" local_ai_studio_pro.py %*
exit /b 0
"""
            launcher_prubeth.write_text(launcher_content, encoding="utf-8")
            launcher_sukhi.write_text(launcher_content, encoding="utf-8")
            launcher_bat.write_text(launcher_content, encoding="utf-8")

            # 4. Create Shortcuts
            target_exe = self.target_dir / "PrubethIDE.exe"
            if not target_exe.exists():
                target_exe = self.target_dir / "SukhiIDE.exe"
            if not target_exe.exists():
                target_exe = self.target_dir / "SoNaive.exe"
            target_path = str(target_exe if target_exe.exists() else launcher_prubeth)
            icon_path = str(self.target_dir / "assets" / "icon.ico")

            if self.create_desktop:
                self.progress.emit(78, "Creating Desktop shortcut...")
                desktop = Path.home() / "Desktop" / f"{APP_NAME} IDE.lnk"
                self.create_windows_shortcut(str(desktop), target_path, icon_path)

            if self.create_startmenu:
                self.progress.emit(88, "Creating Start Menu shortcut...")
                programs = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{APP_NAME} IDE"
                programs.mkdir(parents=True, exist_ok=True)
                lnk = programs / f"{APP_NAME} IDE.lnk"
                self.create_windows_shortcut(str(lnk), target_path, icon_path)

            self.progress.emit(95, "Registering Windows Uninstall hooks...")
            self.register_uninstaller()

            self.progress.emit(100, "Installation complete!")
            self.finished.emit(True, "Success")
        except Exception as e:
            self.finished.emit(False, str(e))

    def create_windows_shortcut(self, lnk_path, target_path, icon_path):
        is_bat = target_path.lower().endswith(".bat")
        window_style = "7" if is_bat else "1"
        ps_cmd = f"""
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{lnk_path}')
$Shortcut.TargetPath = '{target_path}'
$Shortcut.WorkingDirectory = '{self.target_dir}'
$Shortcut.WindowStyle = {window_style}
if (Test-Path '{icon_path}') {{
    $Shortcut.IconLocation = '{icon_path}'
}}
$Shortcut.Description = '{APP_DISPLAY_NAME}'
$Shortcut.Save()
"""
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)

    def register_uninstaller(self):
        uninst_bat = self.target_dir / "Uninstall.bat"
        uninst_content = f"""@echo off
title Uninstall {APP_DISPLAY_NAME}
echo Removing {APP_DISPLAY_NAME}...
timeout /t 2 /nobreak >nul
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
Set-ItemProperty -Path $key -Name 'HelpLink' -Value '{PROJECTS_URL}'
"""
        subprocess.run(["powershell", "-NoProfile", "-Command", reg_cmd], capture_output=True)


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle(f"Welcome to {APP_NAME} IDE Setup")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        logo_lbl = QLabel()
        logo_path = get_resource_dir() / "assets" / "logo.png"
        if not logo_path.exists():
            logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(112, 112, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_lbl)

        title = QLabel(f"<h2 style='color:#E8EAF0; margin-top:6px;'>Prudeth IDE <span style='color:#9485FF;'>v{APP_VERSION}</span></h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            f"<p align='center' style='color:#62D4E5; font-weight:600; font-size:12pt; margin-bottom:8px;'>{APP_TAGLINE}</p>"
            "<p align='center' style='color:#A5ACBB; font-size:10pt; line-height:140%;'>This wizard will install the official Prudeth IDE developer workstation on your computer.<br>"
            "Engineered with a unified dark design system, intelligent multi-model cascade, and hardware scaling.</p>"
            f"<p align='center' style='margin-top:12px;'><small style='color:#737B8C;'>Official Website: <a href='{WEBSITE_URL}' style='color:#9485FF;'>{WEBSITE_URL}</a></small></p>"
        )
        desc.setOpenExternalLinks(True)
        layout.addWidget(desc)
        layout.addStretch()


class DirectoryPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Select Installation Folder")
        self.setSubTitle(f"Where would you like to install {APP_NAME} IDE?")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        lbl = QLabel("Destination Directory:")
        lbl.setStyleSheet("color: #E8EAF0; font-weight: 600;")
        layout.addWidget(lbl)

        row = QHBoxLayout()
        self.dir_input = QLineEdit(str(DEFAULT_INSTALL_DIR))
        b_browse = QPushButton("Browse...")
        b_browse.clicked.connect(self.browse)
        row.addWidget(self.dir_input)
        row.addWidget(b_browse)
        layout.addLayout(row)

        layout.addSpacing(15)
        self.chk_desktop = QCheckBox("Create Desktop Shortcut")
        self.chk_desktop.setChecked(True)
        layout.addWidget(self.chk_desktop)

        self.chk_start = QCheckBox("Create Start Menu Shortcut")
        self.chk_start.setChecked(True)
        layout.addWidget(self.chk_start)

        self.registerField("target_dir*", self.dir_input)
        self.registerField("create_desktop", self.chk_desktop)
        self.registerField("create_startmenu", self.chk_start)
        layout.addStretch()

    def browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Install Directory", self.dir_input.text())
        if d:
            self.dir_input.setText(d)


class ProgressPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle(f"Installing {APP_NAME} IDE")
        self.setSubTitle("Please wait while the system installs files, assets, and shortcuts...")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        self.status_lbl = QLabel("Initializing setup...")
        self.status_lbl.setStyleSheet("color: #A5ACBB;")
        layout.addWidget(self.status_lbl)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        layout.addWidget(self.bar)

        self.worker = None
        self.is_done = False
        layout.addStretch()

    def initializePage(self):
        target_dir = self.field("target_dir")
        create_desktop = self.field("create_desktop")
        create_start = self.field("create_startmenu")

        self.wizard().button(QWizard.BackButton).setEnabled(False)
        self.wizard().button(QWizard.NextButton).setEnabled(False)

        res_dir = get_resource_dir()
        src_dir = get_source_dir()

        payload_candidates = [
            res_dir / "app_payload.zip",
            res_dir / "installer" / "app_payload.zip",
            res_dir / "PrubethIDE-v3.0.0-Universal-Portable.zip",
            src_dir / "app_payload.zip",
            src_dir / "installer" / "app_payload.zip",
            src_dir / "PrubethIDE-v3.0.0-Universal-Portable.zip",
            src_dir / "SukhiIDE-v3.0.0-Universal-Portable.zip",
            src_dir / "SoNaive-v3.0.0-Universal-Portable.zip",
        ]
        payload_zip = None
        for p in payload_candidates:
            if p.exists() and p.is_file():
                payload_zip = p
                break

        self.worker = InstallWorker(target_dir, create_desktop, create_start, payload_zip=payload_zip)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, val, msg):
        self.bar.setValue(val)
        self.status_lbl.setText(msg)

    def on_finished(self, success, err):
        self.is_done = True
        self.wizard().button(QWizard.NextButton).setEnabled(True)
        if success:
            self.status_lbl.setText("Installation completed successfully!")
            self.wizard().next()
        else:
            QMessageBox.critical(self, "Installation Error", f"Failed to install:\n{err}")

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
            f"<h3 style='color:#E8EAF0;'>{APP_DISPLAY_NAME} has been successfully installed!</h3>"
            "<p style='color:#A5ACBB;'>You are now ready to launch the sovereign developer workstation environment.</p>"
            f"<p style='color:#737B8C;'>Find future updates and extensions at <a href='{PROJECTS_URL}' style='color:#9485FF;'>{PROJECTS_URL}</a></p>"
        )
        congrats.setOpenExternalLinks(True)
        layout.addWidget(congrats)

        self.chk_launch = QCheckBox(f"Launch {APP_NAME} IDE now")
        self.chk_launch.setChecked(True)
        layout.addWidget(self.chk_launch)
        layout.addStretch()


class SetupWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} IDE Setup — v{APP_VERSION}")
        self.setWizardStyle(QWizard.ClassicStyle)
        self.resize(650, 450)

        icon_path = get_resource_dir() / "assets" / "icon.ico"
        if not icon_path.exists():
            icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setStyleSheet("""
            QWizard, QWizardPage, QWizard > QWidget, QWizardPage > QWidget {
                background-color: #15171D;
                color: #E8EAF0;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QWizard::header {
                background-color: #1D2028;
                border-bottom: 1px solid #343A49;
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
                height: 18px;
                color: #E8EAF0;
                font-weight: bold;
                font-size: 9pt;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9485FF, stop:1 #62D4E5);
                border-radius: 3px;
            }
            QCheckBox {
                color: #E8EAF0;
                spacing: 8px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #343A49;
                background: #191C23;
                border-radius: 3px;
            }
            QCheckBox::indicator:hover {
                border-color: #9485FF;
            }
            QCheckBox::indicator:checked {
                background-color: #9485FF;
                border-color: #9485FF;
            }
        """)

        self.page_welcome = WelcomePage()
        self.page_dir = DirectoryPage()
        self.page_progress = ProgressPage()
        self.page_finish = FinishPage()

        self.addPage(self.page_welcome)
        self.addPage(self.page_dir)
        self.addPage(self.page_progress)
        self.addPage(self.page_finish)


def main():
    app = QApplication(sys.argv)
    wizard = SetupWizard()
    if wizard.exec_() == QWizard.Accepted:
        if wizard.page_finish.chk_launch.isChecked():
            target_dir = wizard.field("target_dir")
            exe = Path(target_dir) / "PrubethIDE.exe"
            if not exe.exists():
                exe = Path(target_dir) / "SukhiIDE.exe"
            bat = Path(target_dir) / "PrubethIDE.bat"
            if not bat.exists():
                bat = Path(target_dir) / "SukhiIDE.bat"
            launch_target = str(exe if exe.exists() else bat)
            subprocess.Popen([launch_target], cwd=target_dir, shell=True)


if __name__ == "__main__":
    main()
