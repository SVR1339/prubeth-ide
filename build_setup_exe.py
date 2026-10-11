"""
Build standalone Windows installer: PrubethIDE-v3.0.0-Setup.exe
using PyInstaller on installer/setup_wizard.py with embedded application payload.
"""
import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"
ASSETS_DIR = ROOT_DIR / "assets"
INSTALLER_DIR = ROOT_DIR / "installer"
INSTALLER_SCRIPT = INSTALLER_DIR / "setup_wizard.py"


def create_payload_archive() -> Path:
    """Packages the complete application source, assets, and binaries into a payload archive."""
    payload_zip = INSTALLER_DIR / "app_payload.zip"
    print(f"[*] Packaging self-contained application payload archive into: {payload_zip}")

    files_to_pack = [
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

    with zipfile.ZipFile(payload_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for f in files_to_pack:
            p = ROOT_DIR / f
            if p.exists() and p.is_file():
                z.write(p, arcname=f)

        # Include application subsystem modules and resources
        module_dirs = [
            "core", "workspace", "source_control", "language_services",
            "debugging", "ai", "ui", "plugins", "assets", "tests", "docs", "scripts",
            "horizon_engine", "security_research"
        ]
        for m_name in module_dirs:
            m_dir = ROOT_DIR / m_name
            if m_dir.exists():
                for p in m_dir.rglob("*"):
                    if p.is_file() and "__pycache__" not in str(p) and not p.name.endswith(".pyc"):
                        z.write(p, arcname=str(p.relative_to(ROOT_DIR)))

        # Include standalone pre-compiled binaries if present
        for dist_cand in [DIST_DIR / "PrubethIDE", DIST_DIR / "SukhiIDE", DIST_DIR / "SoNaive"]:
            if dist_cand.exists() and dist_cand.is_dir():
                print(f"[*] Including compiled standalone binaries from {dist_cand} into payload...")
                for p in dist_cand.rglob("*"):
                    if p.is_file():
                        z.write(p, arcname=str(p.relative_to(dist_cand)))
                break

    size_kb = payload_zip.stat().st_size / 1024
    print(f"[+] Application payload archive generated successfully ({size_kb:.1f} KB)")
    return payload_zip


def build_setup_executable():
    print("[*] Compiling Graphical Setup Wizard into standalone PrubethIDE-v3.0.0-Setup.exe...")

    payload_zip = create_payload_archive()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=PrubethIDE-Setup",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--icon={ASSETS_DIR / 'icon.ico'}",
        f"--add-data={ASSETS_DIR};assets",
        f"--add-data={payload_zip};.",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        str(INSTALLER_SCRIPT)
    ]

    print(f"[*] Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"[!] Installer compilation failed: code {res.returncode}")
        return False

    out_exe = DIST_DIR / "PrubethIDE-Setup.exe"
    if out_exe.exists():
        # Copy to root directory for immediate single-click launch
        root_setup = ROOT_DIR / "PrubethIDE-Setup.exe"
        root_setup_alias = ROOT_DIR / "setup.exe"
        shutil.copy2(out_exe, root_setup)
        shutil.copy2(out_exe, root_setup_alias)

        # Copy to dist/setup.exe
        dist_setup_alias = DIST_DIR / "setup.exe"
        shutil.copy2(out_exe, dist_setup_alias)

        print(f"[+] Setup executables deployed successfully:")
        print(f"    - {root_setup} ({root_setup.stat().st_size / (1024*1024):.2f} MB)")
        print(f"    - {root_setup_alias} ({root_setup_alias.stat().st_size / (1024*1024):.2f} MB)")
        print(f"    - {out_exe} ({out_exe.stat().st_size / (1024*1024):.2f} MB)")
        return True
    return False


if __name__ == "__main__":
    success = build_setup_executable()
    if not success:
        sys.exit(1)
