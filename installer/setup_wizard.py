"""
SO NAIVE IDE — Graphical Setup Wizard (Windows Installer).
Installs SO NAIVE IDE into %LOCALAPPDATA%\\Programs\\SoNaive,
configures Desktop & Start Menu shortcuts, and registers in Windows Control Panel.
Official Website: https://www.bsvr.work/
"""
import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar,
    QFileDialog, QMessageBox, QFrame
)

APP_NAME = "SUKHI IDE"
APP_DISPLAY_NAME = "SUKHI IDE — Horizon Edition"
APP_VERSION = "3.0.0"
PUBLISHER = "BSVR Technologies"
WEBSITE_URL = "https://www.bsvr.work/"
PROJECTS_URL = "https://www.bsvr.work/#projects"
DEFAULT_INSTALL_DIR = Path.home() / "AppData" / "Local" / "Programs" / "SukhiIDE"


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

    def run(self):
        try:
            self.progress.emit(10, "Preparing target installation directory...")
            self.target_dir.mkdir(parents=True, exist_ok=True)

            res_dir = get_resource_dir()
            src_dir = get_source_dir()
            installed_anything = False

            # 1. Extract payload archive if available
            if self.payload_zip and Path(self.payload_zip).exists():
                self.progress.emit(25, f"Extracting application payload ({Path(self.payload_zip).name})...")
                with zipfile.ZipFile(self.payload_zip, 'r') as z:
                    z.extractall(self.target_dir)
                installed_anything = True
            else:
                # 2. If no payload zip, fall back to copying from available source/resource bases
                dist_src = src_dir / "dist" / "SoNaive"
                if dist_src.exists() and dist_src.is_dir():
                    self.progress.emit(35, "Deploying standalone application binaries...")
                    shutil.copytree(dist_src, self.target_dir, dirs_exist_ok=True)
                    installed_anything = True

                search_bases = [src_dir, res_dir]
                core_files = [
                    "local_ai_studio_pro.py",
                    "README.md",
                    "LICENSE",
                    "ARCHITECTURE.md",
                    "CHANGELOG.md",
                    "INSTALL.md",
                    "requirements.txt",
                    "run_local_ai_studio_pro.bat",
                    "run_ide.bat",
                    "run_ide.sh",
                    "test_ollama.py"
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

                # Copy core modules directory
                for base in search_bases:
                    core_src = base / "core"
                    if core_src.exists() and core_src.is_dir():
                        shutil.copytree(core_src, self.target_dir / "core", dirs_exist_ok=True)
                        break

                # Copy assets directory
                for base in search_bases:
                    assets_src = base / "assets"
                    if assets_src.exists() and assets_src.is_dir():
                        shutil.copytree(assets_src, self.target_dir / "assets", dirs_exist_ok=True)
                        break

                # Copy tests directory
                for base in search_bases:
                    tests_src = base / "tests"
                    if tests_src.exists() and tests_src.is_dir():
                        shutil.copytree(tests_src, self.target_dir / "tests", dirs_exist_ok=True)
                        break

            # 4. Strict verification of installed payload
            has_exe = (self.target_dir / "SoNaive.exe").exists()
            has_py = (self.target_dir / "local_ai_studio_pro.py").exists()

            if not (has_exe or has_py):
                raise RuntimeError(
                    f"Installation integrity verification failed: neither 'SoNaive.exe' nor 'local_ai_studio_pro.py' "
                    f"could be installed to '{self.target_dir}'. "
                    f"The setup package does not contain an executable payload."
                )

            self.progress.emit(65, "Configuring runtime launcher and diagnostic wrappers...")
            # Create a robust, self-diagnosing launcher batch file for SUKHI IDE and SoNaive alias
            launcher_sukhi = self.target_dir / "SukhiIDE.bat"
            launcher_bat = self.target_dir / "SoNaive.bat"
            launcher_content = f"""@echo off
setlocal enabledelayedexpansion
title {APP_NAME} Launcher
cd /d "%~dp0"

:: 1. If standalone executable is installed, launch it directly
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
            launcher_sukhi.write_text(launcher_content, encoding="utf-8")
            launcher_bat.write_text(launcher_content, encoding="utf-8")

            # 5. Create Shortcuts
            target_exe = self.target_dir / "SukhiIDE.exe"
            if not target_exe.exists():
                target_exe = self.target_dir / "SoNaive.exe"
            target_path = str(target_exe if target_exe.exists() else launcher_sukhi)
            icon_path = str(self.target_dir / "assets" / "icon.ico")

            if self.create_desktop:
                self.progress.emit(78, "Creating Desktop shortcut...")
                desktop = Path.home() / "Desktop" / f"{APP_NAME}.lnk"
                self.create_windows_shortcut(str(desktop), target_path, icon_path)

            if self.create_startmenu:
                self.progress.emit(88, "Creating Start Menu shortcut...")
                programs = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME
                programs.mkdir(parents=True, exist_ok=True)
                lnk = programs / f"{APP_NAME}.lnk"
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
$Shortcut.Description = '{APP_NAME} - Next-Gen Agentic AI IDE'
$Shortcut.Save()
"""
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)

    def register_uninstaller(self):
        uninst_bat = self.target_dir / "Uninstall.bat"
        uninst_content = f"""@echo off
title Uninstall {APP_NAME}
echo Removing {APP_NAME}...
timeout /t 2 /nobreak >nul
del /q "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk" 2>nul
rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\SO NAIVE" 2>nul
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\SoNaiveIDE" /f 2>nul
cd /d "%TEMP%"
rmdir /s /q "{self.target_dir}" 2>nul
echo {APP_NAME} has been uninstalled.
pause
"""
        uninst_bat.write_text(uninst_content, encoding="utf-8")

        reg_cmd = f"""
$key = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\SoNaiveIDE'
New-Item -Path $key -Force | Out-Null
Set-ItemProperty -Path $key -Name 'DisplayName' -Value '{APP_NAME}'
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
        self.setTitle("Welcome to SO NAIVE IDE Setup")
        layout = QVBoxLayout(self)

        logo_lbl = QLabel()
        logo_path = get_resource_dir() / "assets" / "logo.png"
        if not logo_path.exists():
            logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_lbl)

        title = QLabel(f"<h2>{APP_NAME} <span style='color:#00F0FF;'>v{APP_VERSION}</span></h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            "<p align='center' style='color:#A855F7; font-weight:bold;'>So Naive, It Solves Everything — 1M Context & Local CUDA Speed</p>"
            "<p align='center'>This wizard will install the official SO NAIVE IDE distribution on your computer.<br>"
            "Includes Intelligent Multi-Model Cascade, Instant Auto-Fix Compiler, and Autonomous Agent Loop.</p>"
            f"<p align='center'><small>Official Website: <a href='{WEBSITE_URL}'>{WEBSITE_URL}</a></small></p>"
        )
        desc.setOpenExternalLinks(True)
        layout.addWidget(desc)
        layout.addStretch()


class DirectoryPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Select Installation Folder")
        self.setSubTitle(f"Where would you like to install {APP_NAME}?")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Destination Directory:"))

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
        self.setTitle("Installing SO NAIVE IDE")
        self.setSubTitle("Please wait while the system installs files and shortcuts...")

        layout = QVBoxLayout(self)
        self.status_lbl = QLabel("Initializing setup...")
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
            res_dir / "SoNaive-v3.0.0-Universal-Portable.zip",
            res_dir / "dist" / "SoNaive-v3.0.0-Windows-Portable.zip",
            src_dir / "app_payload.zip",
            src_dir / "installer" / "app_payload.zip",
            src_dir / "SoNaive-v3.0.0-Universal-Portable.zip",
            src_dir / "dist" / "SoNaive-v3.0.0-Windows-Portable.zip",
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

        congrats = QLabel(
            f"<h3>{APP_NAME} has been successfully installed!</h3>"
            "<p>You are now ready to launch the next-generation agentic AI IDE.</p>"
            f"<p>Find future updates and community extensions at <a href='{PROJECTS_URL}'>{PROJECTS_URL}</a></p>"
        )
        congrats.setOpenExternalLinks(True)
        layout.addWidget(congrats)

        self.chk_launch = QCheckBox(f"Launch {APP_NAME} now")
        self.chk_launch.setChecked(True)
        layout.addWidget(self.chk_launch)
        layout.addStretch()


class SetupWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} Setup — v{APP_VERSION}")
        self.setWizardStyle(QWizard.ModernStyle)
        self.resize(600, 420)

        icon_path = get_resource_dir() / "assets" / "icon.ico"
        if not icon_path.exists():
            icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setStyleSheet("""
            QWizard {
                background: #0d1117;
                color: #e6edf7;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel { color: #dce7fa; font-size: 10pt; }
            QLineEdit {
                background: #161b22;
                color: #ffffff;
                border: 1px solid #30363d;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background: #238636;
                color: #ffffff;
                border: 1px solid #2ea043;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2ea043; }
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 4px;
                text-align: center;
                background: #161b22;
                height: 18px;
            }
            QProgressBar::chunk { background: #00F0FF; border-radius: 3px; }
            QCheckBox { color: #dce7fa; spacing: 8px; }
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
            exe = Path(target_dir) / "SoNaive.exe"
            bat = Path(target_dir) / "SoNaive.bat"
            launch_target = str(exe if exe.exists() else bat)
            subprocess.Popen([launch_target], cwd=target_dir, shell=True)


if __name__ == "__main__":
    main()
