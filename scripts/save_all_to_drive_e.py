"""
Saves all PRUBETH IDE files, reports, assets, installers, and source tree
to Local Disk E (E:\PRUBETH_IDE_V3).
"""
import os
import sys
import shutil
from pathlib import Path

ROOT_DIR = Path(r"c:\Users\asus\heretic-work")
TARGET_BASE = Path(r"E:\PRUBETH_IDE_V3")

REPORTS_DIR = TARGET_BASE / "Reports_and_Documentation"
RELEASE_DIR = TARGET_BASE / "Release_Package"
SOURCE_DIR = TARGET_BASE / "Full_Project_Source"
ASSETS_DIR = TARGET_BASE / "Brand_Assets"


def save_all_to_e():
    print(f"[*] Preparing target directory on Local Disk E: {TARGET_BASE}")
    for d in [TARGET_BASE, REPORTS_DIR, RELEASE_DIR, SOURCE_DIR, ASSETS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    manifest_entries = []

    # 1. Copy Primary Reports (PDF, HTML, MD)
    print("[*] Copying Full Reports...")
    report_files = [
        ROOT_DIR / "PRUBETH_IDE_V3_FULL_DEVELOPMENT_REPORT.pdf",
        ROOT_DIR / "PRUBETH_IDE_V3_FULL_DEVELOPMENT_REPORT.html",
        ROOT_DIR / "docs" / "engineering" / "PRUBETH_IDE_V3_FULL_DEVELOPMENT_REPORT.pdf",
        ROOT_DIR / "docs" / "engineering" / "PRUBETH_IDE_V3_FULL_DEVELOPMENT_REPORT.html",
        Path(r"C:\Users\asus\.gemini\antigravity\brain\f0b7f80a-95d5-4a83-ad44-b809997befed\PRUBETH_100_PERCENT_COMPLETION_REPORT.md"),
        ROOT_DIR / "README.md",
        ROOT_DIR / "ARCHITECTURE.md",
        ROOT_DIR / "CHANGELOG.md",
        ROOT_DIR / "INSTALL.md",
        ROOT_DIR / "LICENSE"
    ]

    for rf in report_files:
        if rf.exists():
            dest1 = REPORTS_DIR / rf.name
            shutil.copy2(rf, dest1)
            manifest_entries.append(f"REPORT: {dest1} ({dest1.stat().st_size / 1024:.1f} KB)")
            # Also copy to root of TARGET_BASE for immediate access
            dest2 = TARGET_BASE / rf.name
            shutil.copy2(rf, dest2)
            print(f"    [+] Saved report: {rf.name}")

    # 2. Copy Release Package (Setup.exe, portable zip, app_payload.zip)
    print("[*] Copying Distributable Installers and Archives...")
    release_files = [
        ROOT_DIR / "dist" / "PrubethIDE-v3.0.0-Setup.exe",
        ROOT_DIR / "dist" / "setup.exe",
        ROOT_DIR / "dist" / "PrubethIDE-v3.0.0-Universal-Portable.zip",
        ROOT_DIR / "installer" / "app_payload.zip",
        ROOT_DIR / "dist" / "SukhiIDE-v3.0.0-Setup.exe",
        ROOT_DIR / "dist" / "SoNaive-v3.0.0-Setup.exe"
    ]

    for rf in release_files:
        if rf.exists():
            dest1 = RELEASE_DIR / rf.name
            shutil.copy2(rf, dest1)
            manifest_entries.append(f"PACKAGE: {dest1} ({dest1.stat().st_size / (1024*1024):.2f} MB)")
            # Also copy flagship installer and portable zip to root of TARGET_BASE
            dest2 = TARGET_BASE / rf.name
            shutil.copy2(rf, dest2)
            print(f"    [+] Saved release file: {rf.name} ({dest1.stat().st_size / (1024*1024):.2f} MB)")

    # 3. Copy Brand Assets
    print("[*] Copying Brand Assets (Windmill emblems, logos, icons)...")
    for f in (ROOT_DIR / "assets").glob("*"):
        if f.is_file():
            dest = ASSETS_DIR / f.name
            shutil.copy2(f, dest)
            manifest_entries.append(f"ASSET: {dest} ({dest.stat().st_size / 1024:.1f} KB)")
            print(f"    [+] Saved asset: {f.name}")

    # 4. Copy Full Project Source Tree (excluding .venv, .git, __pycache__)
    print("[*] Copying Full Project Source Tree...")
    exclude_dirs = {".venv", ".git", "__pycache__", ".pytest_cache", "build", "dist"}
    copied_count = 0

    for root, dirs, files in os.walk(ROOT_DIR):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        rel_root = Path(root).relative_to(ROOT_DIR)

        dest_folder = SOURCE_DIR / rel_root
        dest_folder.mkdir(parents=True, exist_ok=True)

        for f in files:
            if f.endswith(".pyc") or f == ".DS_Store":
                continue
            src_file = Path(root) / f
            dest_file = dest_folder / f
            try:
                shutil.copy2(src_file, dest_file)
                copied_count += 1
            except Exception as ex:
                print(f"    [!] Error copying {src_file}: {ex}")

    print(f"[+] Successfully copied {copied_count} project source files to {SOURCE_DIR}")

    # 5. Write Manifest and Quick Start Guide on Drive E
    manifest_file = TARGET_BASE / "MANIFEST.txt"
    with open(manifest_file, "w", encoding="utf-8") as mf:
        mf.write("===============================================================================\n")
        mf.write("  PRUBETH IDE — Horizon Edition v3.0.0 (Master Archive)\n")
        mf.write("  Saved to Local Disk E: " + str(TARGET_BASE) + "\n")
        mf.write("===============================================================================\n\n")
        mf.write("DIRECTORIES ON DRIVE E:\n")
        mf.write("  1. E:\\PRUBETH_IDE_V3\\Release_Package (Setup Wizard executables & zip archives)\n")
        mf.write("  2. E:\\PRUBETH_IDE_V3\\Reports_and_Documentation (PDF, HTML, and Markdown reports)\n")
        mf.write("  3. E:\\PRUBETH_IDE_V3\\Full_Project_Source (Complete clean repository tree)\n")
        mf.write("  4. E:\\PRUBETH_IDE_V3\\Brand_Assets (Windmill emblems, logos, icons)\n\n")
        mf.write("ROOT RELEASE ARTIFACTS:\n")
        for entry in manifest_entries:
            mf.write(f"  - {entry}\n")
        mf.write(f"\nTotal Project Source Files Copied: {copied_count}\n")

    # 6. Create Quick Launcher Batch on Drive E
    quick_launcher = TARGET_BASE / "RUN_PRUBETH_IDE.bat"
    quick_launcher_content = f"""@echo off
title Launch PRUBETH IDE
cd /d "%~dp0"
if exist "PrubethIDE-v3.0.0-Setup.exe" (
    echo Launching PRUBETH IDE Setup Wizard...
    start "" "PrubethIDE-v3.0.0-Setup.exe"
    exit /b 0
)
if exist "Full_Project_Source\\run_ide.bat" (
    cd /d "%~dp0Full_Project_Source"
    call run_ide.bat
    exit /b 0
)
pause
"""
    quick_launcher.write_text(quick_launcher_content, encoding="utf-8")

    print(f"\n[+] ALL FILES AND REPORTS SUCCESSFULLY SAVED TO LOCAL DISK E:")
    print(f"    -> Destination: {TARGET_BASE}")
    print(f"    -> Manifest: {manifest_file}")
    print(f"    -> Quick Launcher: {quick_launcher}")


if __name__ == "__main__":
    save_all_to_e()
