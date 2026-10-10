#!/usr/bin/env python3
"""
SUKHI IDE — Reproducible Line Count & Software Metrics Analyzer
Measures raw lines, blank lines, comments, and non-blank/non-comment SLOC
across Production Source, Tests, Tooling, Documentation, and Configurations.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    "build", "dist", "scratch", "node_modules", ".idea", ".vscode"
}

SOURCE_EXTENSIONS = {
    ".py", ".pyw", ".js", ".ts", ".jsx", ".tsx",
    ".c", ".cpp", ".cc", ".h", ".hpp", ".rs", ".go",
    ".html", ".css", ".qss", ".bat", ".sh", ".ps1", ".sql"
}

BINARY_EXTENSIONS = {
    ".zip", ".ico", ".png", ".jpg", ".jpeg", ".gif",
    ".exe", ".dll", ".pyd", ".pyc", ".spec", ".pdf"
}

DOC_EXTENSIONS = {".md", ".txt", ".rst"}
CONFIG_EXTENSIONS = {".toml", ".json", ".yaml", ".yml", ".iss", ".ini", ".cfg", ".gitignore", ".env"}


def classify_file(rel_path: Path) -> str:
    if rel_path.suffix.lower() in BINARY_EXTENSIONS:
        return "Binary (Excluded)"

    parts = rel_path.parts
    first_dir = parts[0] if len(parts) > 1 else ""

    if first_dir in ("tests", "testing"):
        return "Tests"
    elif first_dir in ("docs", "documentation") or rel_path.suffix in DOC_EXTENSIONS:
        return "Documentation"
    elif first_dir in ("scripts",) or rel_path.name.startswith("build_") or rel_path.name.startswith("generate_"):
        return "Tooling & Scripts"
    elif rel_path.suffix in CONFIG_EXTENSIONS or rel_path.name in ("requirements.txt", "LICENSE"):
        return "Config & Metadata"
    elif rel_path.suffix in SOURCE_EXTENSIONS:
        return "Production Source"
    return "Other"


def count_file_lines(file_path: Path) -> Tuple[int, int, int, int]:
    raw = 0
    blank = 0
    comments = 0
    sloc = 0
    in_multiline_py = False
    in_multiline_c = False

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0, 0, 0, 0

    lines = content.splitlines()
    raw = len(lines)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
            continue

        # Multiline comment handling
        if file_path.suffix in (".py", ".pyw"):
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if (stripped.count('"""') % 2 == 1) or (stripped.count("'''") % 2 == 1):
                    in_multiline_py = not in_multiline_py
                comments += 1
                continue
            elif in_multiline_py:
                comments += 1
                if '"""' in stripped or "'''" in stripped:
                    in_multiline_py = False
                continue
            elif stripped.startswith("#"):
                comments += 1
                continue

        elif file_path.suffix in (".js", ".ts", ".c", ".cpp", ".h", ".rs", ".go", ".css", ".qss"):
            if stripped.startswith("/*"):
                if not stripped.endswith("*/"):
                    in_multiline_c = True
                comments += 1
                continue
            elif in_multiline_c:
                comments += 1
                if "*/" in stripped:
                    in_multiline_c = False
                continue
            elif stripped.startswith("//"):
                comments += 1
                continue

        elif file_path.suffix in (".bat", ".cmd"):
            if stripped.lower().startswith("rem ") or stripped.startswith("::"):
                comments += 1
                continue

        elif file_path.suffix in (".sh", ".bash", ".ps1"):
            if stripped.startswith("#"):
                comments += 1
                continue

        sloc += 1

    return raw, blank, comments, sloc


def analyze_repository(root: Path) -> Dict[str, Any]:
    categories = {
        "Production Source": {"files": 0, "raw": 0, "blank": 0, "comments": 0, "sloc": 0},
        "Tests": {"files": 0, "raw": 0, "blank": 0, "comments": 0, "sloc": 0},
        "Tooling & Scripts": {"files": 0, "raw": 0, "blank": 0, "comments": 0, "sloc": 0},
        "Documentation": {"files": 0, "raw": 0, "blank": 0, "comments": 0, "sloc": 0},
        "Config & Metadata": {"files": 0, "raw": 0, "blank": 0, "comments": 0, "sloc": 0},
        "Other": {"files": 0, "raw": 0, "blank": 0, "comments": 0, "sloc": 0},
    }

    file_details = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories immediately to avoid recursing into .venv or .git
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]

        for fname in sorted(filenames):
            path = Path(dirpath) / fname
            rel = path.relative_to(root)

            category = classify_file(rel)
            if category.startswith("Binary"):
                continue

            raw, blank, comments, sloc = count_file_lines(path)

            categories[category]["files"] += 1
            categories[category]["raw"] += raw
            categories[category]["blank"] += blank
            categories[category]["comments"] += comments
            categories[category]["sloc"] += sloc

            file_details.append({
                "path": str(rel).replace("\\", "/"),
                "category": category,
                "raw": raw,
                "blank": blank,
                "comments": comments,
                "sloc": sloc
            })

    total_raw = sum(c["raw"] for c in categories.values())
    total_sloc = sum(c["sloc"] for c in categories.values())
    total_files = sum(c["files"] for c in categories.values())

    return {
        "root": str(root),
        "total_files": total_files,
        "total_raw_lines": total_raw,
        "total_sloc": total_sloc,
        "categories": categories,
        "files": file_details
    }


def print_report(data: Dict[str, Any]):
    print("=" * 80)
    print(" SUKHI IDE — REPRODUCIBLE SOURCE METRICS REPORT")
    print("=" * 80)
    print(f"{'Category':<24} | {'Files':>6} | {'Raw Lines':>10} | {'Comments':>9} | {'SLOC':>9}")
    print("-" * 80)

    for cat, metrics in data["categories"].items():
        if metrics["files"] > 0:
            print(f"{cat:<24} | {metrics['files']:>6} | {metrics['raw']:>10} | {metrics['comments']:>9} | {metrics['sloc']:>9}")

    print("-" * 80)
    prod_sloc = data["categories"]["Production Source"]["sloc"]
    test_sloc = data["categories"]["Tests"]["sloc"]
    core_executable = prod_sloc + test_sloc
    print(f"{'CORE EXECUTABLE (Prod+Test)':<24} | {data['categories']['Production Source']['files'] + data['categories']['Tests']['files']:>6} | {data['categories']['Production Source']['raw'] + data['categories']['Tests']['raw']:>10} | {data['categories']['Production Source']['comments'] + data['categories']['Tests']['comments']:>9} | {core_executable:>9}")
    print(f"{'TOTAL REPOSITORY':<24} | {data['total_files']:>6} | {data['total_raw_lines']:>10} | {sum(c['comments'] for c in data['categories'].values()):>9} | {data['total_sloc']:>9}")
    print("=" * 80)


if __name__ == "__main__":
    report = analyze_repository(ROOT_DIR)
    print_report(report)

    if "--json" in sys.argv:
        json_out = ROOT_DIR / "docs" / "engineering" / "metrics_latest.json"
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[+] Exported JSON metrics to: {json_out}")
