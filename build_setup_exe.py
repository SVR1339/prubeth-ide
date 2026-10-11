"""
Build production Windows installer executables:
- Mode A (Default if package >= 70 MiB): Lightweight online Setup.exe / Prubeth-Setup-3.0.0.exe
  (retrieves verified payload from GitHub Releases, keeping installer size small).
- Mode B: Full offline Prubeth-Offline-Setup-3.0.0.exe (embeds complete payload archive).
Configurable threshold: 70 MiB (binary).
"""
import os
import sys
import shutil
import zipfile
import subprocess
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from installer.release_config import (
    APP_NAME, APP_VERSION, TARGET_ARCH, DEFAULT_ONLINE_THRESHOLD_MIB,
    evaluate_delivery_mode, MODE_ONLINE, MODE_OFFLINE, MODE_AUTO
)
from scripts.build_release_artifacts import generate_release_artifacts, package_payload_zip

DIST_DIR = ROOT_DIR / "dist"
ASSETS_DIR = ROOT_DIR / "assets"
INSTALLER_DIR = ROOT_DIR / "installer"
INSTALLER_SCRIPT = INSTALLER_DIR / "setup_wizard.py"


def create_payload_archive() -> Path:
    """Packages the complete application source, assets, and binaries into a payload archive."""
    payload_zip = INSTALLER_DIR / "app_payload.zip"
    package_payload_zip(payload_zip)
    return payload_zip


def build_installer_executable(mode: str = MODE_ONLINE, threshold_mib: float = DEFAULT_ONLINE_THRESHOLD_MIB) -> bool:
    """
    Compiles the installer into a standalone executable.
    In Mode A (Online), builds a small lightweight Setup.exe without embedded payload.
    In Mode B (Offline), bundles the complete app_payload.zip.
    """
    # 1. Generate release assets and payload archive
    print("[*] Generating canonical release payload, manifest, and signatures...")
    rel_data = generate_release_artifacts(threshold_mib=threshold_mib)

    # 2. Determine effective build mode
    effective_mode = mode
    if mode == MODE_AUTO:
        effective_mode = rel_data["delivery_mode"]

    print(f"[*] Building installer in: {effective_mode.upper()} mode")

    payload_zip = INSTALLER_DIR / "app_payload.zip"

    # Configure PyInstaller arguments
    exe_name = f"Prubeth-Setup-{APP_VERSION}" if effective_mode == MODE_ONLINE else f"Prubeth-Offline-Setup-{APP_VERSION}"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        f"--name={exe_name}",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--icon={ASSETS_DIR / 'icon.ico'}",
        f"--add-data={ASSETS_DIR};assets",
        f"--add-data={INSTALLER_DIR / 'release_config.py'};installer",
        f"--add-data={INSTALLER_DIR / 'manifest_schema.py'};installer",
        f"--add-data={INSTALLER_DIR / 'disk_manager.py'};installer",
        f"--add-data={INSTALLER_DIR / 'download_engine.py'};installer",
        f"--add-data={INSTALLER_DIR / 'transactional_installer.py'};installer",
        f"--add-data={INSTALLER_DIR / 'uninstaller.py'};installer",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=cryptography",
        "--hidden-import=cryptography.hazmat.primitives.asymmetric.ed25519",
        "--hidden-import=installer.release_config",
        "--hidden-import=installer.manifest_schema",
        "--hidden-import=installer.disk_manager",
        "--hidden-import=installer.download_engine",
        "--hidden-import=installer.transactional_installer",
        "--hidden-import=installer.uninstaller"
    ]

    # In Offline Mode, embed the full payload archive
    if effective_mode == MODE_OFFLINE and payload_zip.exists():
        print(f"[*] Mode B: Embedding full application payload ({payload_zip.stat().st_size / (1024*1024):.2f} MiB)...")
        cmd.append(f"--add-data={payload_zip};.")
    else:
        print("[*] Mode A: Building lightweight online bootstrap installer (payload will be downloaded from GitHub)...")

    cmd.append(str(INSTALLER_SCRIPT))

    print(f"[*] Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"[!] Installer compilation failed: code {res.returncode}")
        return False

    out_exe = DIST_DIR / f"{exe_name}.exe"
    if out_exe.exists():
        # Deploy standardized aliases: Setup.exe and PrubethIDE-Setup.exe
        root_setup = ROOT_DIR / "Setup.exe"
        root_setup_legacy = ROOT_DIR / "setup.exe"
        root_prubeth_setup = ROOT_DIR / "PrubethIDE-Setup.exe"

        dist_setup = DIST_DIR / "Setup.exe"
        dist_setup_alias = DIST_DIR / "setup.exe"
        dist_prubeth_setup = DIST_DIR / "PrubethIDE-Setup.exe"

        for target in [root_setup, root_setup_legacy, root_prubeth_setup, dist_setup, dist_setup_alias, dist_prubeth_setup]:
            shutil.copy2(out_exe, target)

        size_mb = out_exe.stat().st_size / (1024 * 1024)
        print("=" * 70)
        print(f"[+] Installer executables built successfully ({size_mb:.2f} MB):")
        print(f"    - Mode:               {effective_mode.upper()}")
        print(f"    - Primary Binary:     {out_exe}")
        print(f"    - Lightweight Alias:  {root_setup}")
        print(f"    - Root Installer:     {root_prubeth_setup}")
        print("=" * 70)
        return True

    return False


def main():
    parser = argparse.ArgumentParser(description="PRUBETH IDE — Setup Executable Compiler")
    parser.add_argument("--mode", choices=["auto", "online", "offline"], default="auto", help="Delivery mode (default: auto).")
    parser.add_argument("--threshold", type=float, default=DEFAULT_ONLINE_THRESHOLD_MIB, help="Online threshold in MiB (default: 70.0).")
    args = parser.parse_args()

    success = build_installer_executable(mode=args.mode, threshold_mib=args.threshold)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
