"""
Automated Build & Packaging Engine for SO NAIVE IDE.
Compiles local_ai_studio_pro.py into a standalone Windows distribution
and packages a self-contained Setup Installer and Portable ZIP.
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
APP_NAME = "SoNaive"
EXE_NAME = "SoNaive.exe"
SETUP_EXE_NAME = "SoNaive-v3.0.0-Setup.exe"


def build_pyinstaller():
    print(f"[*] Building {APP_NAME} binary with PyInstaller...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--icon={ASSETS_DIR / 'icon.ico'}",
        f"--add-data={ASSETS_DIR};assets",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.Qsci",
        "--hidden-import=requests",
        "--hidden-import=json",
        "--hidden-import=math",
        "--hidden-import=difflib",
        "local_ai_studio_pro.py"
    ]

    print(f"[*] Running: {' '.join(str(c) for c in cmd)}")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"[!] PyInstaller build failed with return code {res.returncode}")
        return False
    print(f"[+] PyInstaller build successful in: {DIST_DIR / APP_NAME}")
    return True


def package_portable_zip():
    app_folder = DIST_DIR / APP_NAME
    if not app_folder.exists():
        print(f"[!] {app_folder} does not exist.")
        return None

    zip_target = DIST_DIR / "SoNaive-v3.0.0-Windows-Portable"
    print(f"[*] Creating Portable ZIP archive: {zip_target}.zip")
    shutil.make_archive(str(zip_target), "zip", DIST_DIR, APP_NAME)
    print(f"[+] Created {zip_target}.zip")
    return zip_target.with_suffix(".zip")


def package_universal_source_zip():
    """Generates the universal cross-platform source zip distribution."""
    out_zip = ROOT_DIR / "SukhiIDE-v3.0.0-Universal-Portable.zip"
    legacy_zip = ROOT_DIR / "SoNaive-v3.0.0-Universal-Portable.zip"
    print(f"[*] Packaging Universal Portable ZIP: {out_zip}")
    files_to_pack = [
        "local_ai_studio_pro.py",
        "run_local_ai_studio_pro.bat",
        "run_ide.bat",
        "run_ide.sh",
        "requirements.txt",
        "README.md",
        "LICENSE",
        "ARCHITECTURE.md",
        "CHANGELOG.md",
        "INSTALL.md",
        "pyproject.toml",
        "test_ollama.py"
    ]
    with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for f in files_to_pack:
            p = ROOT_DIR / f
            if p.exists() and p.is_file():
                z.write(p, arcname=f)

        # Include application subsystem modules and resources
        module_dirs = [
            "core", "workspace", "source_control", "language_services",
            "debugging", "ai", "ui", "plugins", "assets", "tests", "docs", "scripts"
        ]
        for m_name in module_dirs:
            m_dir = ROOT_DIR / m_name
            if m_dir.exists():
                for p in m_dir.rglob("*"):
                    if p.is_file() and "__pycache__" not in str(p) and not p.name.endswith(".pyc"):
                        z.write(p, arcname=str(p.relative_to(ROOT_DIR)))

    shutil.copy2(out_zip, legacy_zip)
    print(f"[+] Created {out_zip} ({out_zip.stat().st_size / 1024:.1f} KB)")
    print(f"[+] Synced legacy alias {legacy_zip}")
    return out_zip


if __name__ == "__main__":
    if not (ASSETS_DIR / "icon.ico").exists():
        print("[*] Generating brand assets first...")
        subprocess.run([sys.executable, "generate_assets.py"], check=True)

    package_universal_source_zip()

    # Build binary if requested or if PyInstaller available
    if "--no-binary" not in sys.argv:
        success = build_pyinstaller()
        if success:
            package_portable_zip()
            print("\n[+] Distribution build finished successfully!")
        else:
            print("[!] Skipping standalone binary packaging.")
