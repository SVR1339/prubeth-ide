"""
Reorganize development artifacts and obsolete files into developments_stack/.
Preserves all historical files safely while leaving the main root folder clean.
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEV_STACK = ROOT / "developments_stack"

DIRS_TO_CREATE = [
    DEV_STACK / "legacy_scripts",
    DEV_STACK / "scratch",
    DEV_STACK / "reports_and_docs",
    DEV_STACK / "specs",
    DEV_STACK / "archive_zips",
    DEV_STACK / "website",
    DEV_STACK / "build_cache",
]

for d in DIRS_TO_CREATE:
    d.mkdir(parents=True, exist_ok=True)

FILE_MOVES = [
    # Legacy standalone scripts -> legacy_scripts
    ("local_ai_studio.py", DEV_STACK / "legacy_scripts" / "local_ai_studio.py"),
    ("ollama_gui.py", DEV_STACK / "legacy_scripts" / "ollama_gui.py"),
    ("test_ollama.py", DEV_STACK / "legacy_scripts" / "test_ollama.py"),
    ("generate_assets.py", DEV_STACK / "legacy_scripts" / "generate_assets.py"),
    ("run_ide.bat", DEV_STACK / "legacy_scripts" / "run_ide.bat"),
    ("run_ide.sh", DEV_STACK / "legacy_scripts" / "run_ide.sh"),

    # Historical reports and guides -> reports_and_docs
    ("PRUBETH_IDE_V3_FULL_DEVELOPMENT_REPORT.html", DEV_STACK / "reports_and_docs" / "PRUBETH_IDE_V3_FULL_DEVELOPMENT_REPORT.html"),
    ("PRUBETH_IDE_V3_FULL_DEVELOPMENT_REPORT.pdf", DEV_STACK / "reports_and_docs" / "PRUBETH_IDE_V3_FULL_DEVELOPMENT_REPORT.pdf"),
    ("SUKHI_IDE_V3_FULL_DEVELOPMENT_REPORT.html", DEV_STACK / "reports_and_docs" / "SUKHI_IDE_V3_FULL_DEVELOPMENT_REPORT.html"),
    ("SUKHI_IDE_V3_FULL_DEVELOPMENT_REPORT.pdf", DEV_STACK / "reports_and_docs" / "SUKHI_IDE_V3_FULL_DEVELOPMENT_REPORT.pdf"),
    ("CONTACT_UPDATE_GUIDE.md", DEV_STACK / "reports_and_docs" / "CONTACT_UPDATE_GUIDE.md"),
    ("SELF_TESTS.md", DEV_STACK / "reports_and_docs" / "SELF_TESTS.md"),

    # Old PyInstaller specs -> specs
    ("PrubethIDE.spec", DEV_STACK / "specs" / "PrubethIDE.spec"),
    ("PrubethIDE-v3.0.0-Setup.spec", DEV_STACK / "specs" / "PrubethIDE-v3.0.0-Setup.spec"),
    ("SoNaive-v3.0.0-Setup.spec", DEV_STACK / "specs" / "SoNaive-v3.0.0-Setup.spec"),
    ("SukhiIDE-v3.0.0-Setup.spec", DEV_STACK / "specs" / "SukhiIDE-v3.0.0-Setup.spec"),

    # Root zip archives -> archive_zips
    ("PrubethIDE-v3.0.0-Universal-Portable.zip", DEV_STACK / "archive_zips" / "PrubethIDE-v3.0.0-Universal-Portable.zip"),
    ("SoNaive-v3.0.0-Universal-Portable.zip", DEV_STACK / "archive_zips" / "SoNaive-v3.0.0-Universal-Portable.zip"),
    ("SukhiIDE-v3.0.0-Universal-Portable.zip", DEV_STACK / "archive_zips" / "SukhiIDE-v3.0.0-Universal-Portable.zip"),
]

DIR_MOVES = [
    (".prubeth_scratch", DEV_STACK / "scratch" / ".prubeth_scratch"),
    ("scratch", DEV_STACK / "scratch" / "scratch"),
    (".horizon", DEV_STACK / "scratch" / ".horizon"),
    ("website", DEV_STACK / "website" / "website"),
    ("build", DEV_STACK / "build_cache" / "build"),
]

for src_name, dst_path in FILE_MOVES:
    src_path = ROOT / src_name
    if src_path.exists():
        if dst_path.exists():
            dst_path.unlink()
        shutil.move(str(src_path), str(dst_path))
        print(f"[+] Moved file: {src_name} -> {dst_path.relative_to(ROOT)}")

for src_name, dst_path in DIR_MOVES:
    src_path = ROOT / src_name
    if src_path.exists():
        if dst_path.exists():
            shutil.rmtree(str(dst_path), ignore_errors=True)
        shutil.move(str(src_path), str(dst_path))
        print(f"[+] Moved directory: {src_name} -> {dst_path.relative_to(ROOT)}")

readme_content = """# Developments Stack Directory

This directory contains development artifacts, historical documentation, prototype scripts, and build caches archived from the main project root to maintain a clean, production-ready workspace.

## Structure:
- `legacy_scripts/`: Early prototype tools and standalone scripts (`local_ai_studio.py`, `ollama_gui.py`, `test_ollama.py`, asset generators, legacy runners).
- `scratch/`: Scratch workspaces, temporary cache folders, and experimental files.
- `reports_and_docs/`: Historical development reports (HTML/PDF), contact update guides, and self-test docs.
- `specs/`: Historical PyInstaller spec files.
- `archive_zips/`: Historical portable zip archives.
- `website/`: Website assets and landing page source code.
- `build_cache/`: Temporary compiler intermediate build files.

All active production code, tests, and authoritative launchers reside in the root directory and standard package folders (`core/`, `ui/`, `ai/`, `horizon_engine/`, `security_research/`, etc.).
"""
(DEV_STACK / "README.md").write_text(readme_content, encoding="utf-8")
print("[+] Created developments_stack/README.md")
