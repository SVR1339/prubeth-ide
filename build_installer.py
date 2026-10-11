"""
Automated Fast Standalone Build Engine for PRUBETH IDE.
Compiles local_ai_studio_pro.py into a standalone Windows distribution (dist/PrubethIDE)
bundling Python runtime, PyQt5, QScintilla, requests, and all core modules,
excluding heavy external data science libraries.
"""
import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
ASSETS_DIR = ROOT_DIR / "assets"
APP_NAME = "PrubethIDE"
EXE_NAME = "PrubethIDE.exe"


def build_pyinstaller():
    print(f"[*] Compiling {APP_NAME} standalone binary with PyInstaller...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--icon={ASSETS_DIR / 'icon.ico'}",
        f"--add-data={ASSETS_DIR};assets",
        f"--add-data={ROOT_DIR / 'core'};core",
        f"--add-data={ROOT_DIR / 'workspace'};workspace",
        f"--add-data={ROOT_DIR / 'ai'};ai",
        f"--add-data={ROOT_DIR / 'ui'};ui",
        f"--add-data={ROOT_DIR / 'plugins'};plugins",
        f"--add-data={ROOT_DIR / 'language_services'};language_services",
        f"--add-data={ROOT_DIR / 'debugging'};debugging",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtPrintSupport",
        "--hidden-import=PyQt5.Qsci",
        "--hidden-import=requests",
        "--hidden-import=cryptography",
        "--hidden-import=sqlite3",
        "--hidden-import=json",
        "--hidden-import=math",
        "--hidden-import=difflib",
        "--exclude-module=torch",
        "--exclude-module=scipy",
        "--exclude-module=pytest",
        "--exclude-module=matplotlib",
        "--exclude-module=PIL",
        "--exclude-module=numpy",
        "--exclude-module=pandas",
        "--exclude-module=transformers",
        "--exclude-module=sympy",
        "local_ai_studio_pro.py"
    ]

    print(f"[*] Running: {' '.join(str(c) for c in cmd)}")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"[!] PyInstaller build failed with return code {res.returncode}")
        return False

    out_exe = DIST_DIR / APP_NAME / EXE_NAME
    if out_exe.exists():
        print(f"[+] Standalone binary compiled successfully: {out_exe} ({out_exe.stat().st_size / (1024*1024):.2f} MB)")
        return True
    return False


def package_portable_zip():
    app_folder = DIST_DIR / APP_NAME
    if not app_folder.exists():
        print(f"[!] {app_folder} does not exist.")
        return None

    zip_target = DIST_DIR / "PrubethIDE-v3.0.0-Windows-Portable"
    print(f"[*] Creating Portable ZIP archive: {zip_target}.zip")
    shutil.make_archive(str(zip_target), "zip", DIST_DIR, APP_NAME)
    print(f"[+] Created {zip_target}.zip")
    return zip_target.with_suffix(".zip")


if __name__ == "__main__":
    success = build_pyinstaller()
    if success:
        package_portable_zip()
        print("\n[+] Distribution build finished successfully!")
    else:
        sys.exit(1)
