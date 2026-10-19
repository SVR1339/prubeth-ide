"""
Build cross-platform release packages for Windows, Linux, and Apple macOS.
Generates:
  - Prubeth-v1.91.0-linux-x64.tar.gz
  - Prubeth-v1.91.0-darwin-universal.tar.gz
  - Prubeth-v1.91.0-Universal.zip
"""
import os
import tarfile
import zipfile
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
DIST_DIR.mkdir(parents=True, exist_ok=True)

VERSION = "1.91.0"

INCLUDE_FILES = [
    "local_ai_studio_pro.py",
    "install.sh",
    "install.ps1",
    "run_prubeth.sh",
    "prubeth.bat",
    "requirements.txt",
    "LICENSE",
    "README.md",
    "INSTALL.md",
    "DEVELOPER_EXTENSIONS_GUIDE.md",
    "ARCHITECTURE.md"
]

INCLUDE_DIRS = [
    "core",
    "ai",
    "ui",
    "assets",
    "code_oss",
    "installer",
    "language_services",
    "horizon_engine",
    "tools"
]

EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".venv",
    ".git",
    "*.log",
    "*.tmp",
    ".pytest_cache",
    "build_cache",
    "archive_zips"
]

def should_exclude(path_obj: Path) -> bool:
    for part in path_obj.parts:
        if part in ("__pycache__", ".venv", ".git", ".pytest_cache", "build_cache", "archive_zips", "dist"):
            return True
        if part.endswith(".pyc"):
            return True
    return False

def build_zip(target_path: Path):
    print(f"[*] Building ZIP: {target_path} ...")
    with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for fname in INCLUDE_FILES:
            fpath = ROOT_DIR / fname
            if fpath.exists():
                z.write(fpath, arcname=f"prubeth/{fname}")
        for dname in INCLUDE_DIRS:
            dpath = ROOT_DIR / dname
            if dpath.exists():
                for root, dirs, files in os.walk(dpath):
                    for file in files:
                        fp = Path(root) / file
                        if not should_exclude(fp):
                            rel = fp.relative_to(ROOT_DIR)
                            z.write(fp, arcname=f"prubeth/{rel.as_posix()}")
    print(f"[+] Created {target_path} ({target_path.stat().st_size:,} bytes)")

def build_tar_gz(target_path: Path):
    print(f"[*] Building TAR.GZ: {target_path} ...")
    with tarfile.open(target_path, "w:gz") as t:
        for fname in INCLUDE_FILES:
            fpath = ROOT_DIR / fname
            if fpath.exists():
                t.add(fpath, arcname=f"prubeth/{fname}")
        for dname in INCLUDE_DIRS:
            dpath = ROOT_DIR / dname
            if dpath.exists():
                for root, dirs, files in os.walk(dpath):
                    for file in files:
                        fp = Path(root) / file
                        if not should_exclude(fp):
                            rel = fp.relative_to(ROOT_DIR)
                            t.add(fp, arcname=f"prubeth/{rel.as_posix()}")
    print(f"[+] Created {target_path} ({target_path.stat().st_size:,} bytes)")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    linux_tar = DIST_DIR / f"Prubeth-v{VERSION}-linux-x64.tar.gz"
    darwin_tar = DIST_DIR / f"Prubeth-v{VERSION}-darwin-universal.tar.gz"
    universal_zip = DIST_DIR / f"Prubeth-v{VERSION}-Universal.zip"

    build_tar_gz(linux_tar)
    build_tar_gz(darwin_tar)
    build_zip(universal_zip)

    # Compute checksums
    sums_file = DIST_DIR / "release_v1.91.0" / "Prubeth-SHA256SUMS.txt"
    sums = {}
    if sums_file.exists():
        for line in sums_file.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                sums[parts[1]] = parts[0]

    for p in [linux_tar, darwin_tar, universal_zip]:
        digest = sha256_file(p)
        sums[p.name] = digest
        print(f"SHA-256 ({p.name}) = {digest}")

    # Write unified SHA256SUMS
    lines = [f"{digest}  {name}" for name, digest in sorted(sums.items())]
    sums_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[+] Updated {sums_file}")

if __name__ == "__main__":
    main()
