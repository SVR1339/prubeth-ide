"""
PRUBETH IDE -- Master Build & Installer Orchestration Script
============================================================
Builds PRUBETH IDE from the VS Code (microsoft/vscode) source code and packages
a complete Windows installer using Inno Setup 6.

Build Pipeline:
  Stage 0: Verify prerequisites (Node 24+, npm, Inno Setup 6)
  Stage 1: Apply PRUBETH branding to vscode source
  Stage 2: npm install (install all VS Code dependencies)
  Stage 3: Gulp compile (build Electron app from TypeScript source)
  Stage 4: Gulp package (create prubeth-build/ directory with final app)
  Stage 5: Deploy PRUBETH icons over VS Code icons in final build
  Stage 6: Run Inno Setup -> produce dist/PrubethIDE-vX.X.X-Setup.exe
  Stage 7: Print release summary
"""
import os
import sys

# Fix Unicode output on Windows CP1252 consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import json
import shutil
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
VSCODE_DIR = ROOT / "vscode"
ASSETS_DIR = ROOT / "assets"
DIST_DIR = ROOT / "dist"
BUILD_OUT = ROOT / "prubeth-build"

ISCC = Path(r"C:\Users\asus\AppData\Local\Programs\Inno Setup 6\ISCC.exe")
ISS_SCRIPT = VSCODE_DIR / "build" / "win32" / "prubeth.iss"

APP_VERSION = "1.89.0"
APP_NAME = "PRUBETH IDE"
PUBLISHER = "BSVR Technologies"


def banner(msg: str):
    pad = "=" * (len(msg) + 4)
    print(f"\n+{pad}+")
    print(f"|  {msg}  |")
    print(f"+{pad}+\n")


def run(cmd, cwd=None, env=None, check=True):
    """Run a shell command, streaming output live."""
    print(f"  >> {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        [str(c) for c in cmd],
        cwd=str(cwd or ROOT),
        env=env or os.environ,
        check=check
    )
    return result


# ── Stage 0: Verify Prerequisites ────────────────────────────────────────────
def stage0_verify():
    banner("STAGE 0 — Verifying Prerequisites")
    errors = []

    # Node.js
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True)
        node_ver = r.stdout.strip()
        major = int(node_ver.lstrip("v").split(".")[0])
        if major < 24:
            errors.append(f"Node.js v24+ required, found {node_ver}")
        else:
            print(f"  ✓ Node.js {node_ver}")
    except FileNotFoundError:
        errors.append("Node.js not found in PATH")

    # npm
    try:
        r = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        print(f"  ✓ npm {r.stdout.strip()}")
    except FileNotFoundError:
        errors.append("npm not found in PATH")

    # Inno Setup
    if ISCC.exists():
        print(f"  ✓ Inno Setup 6: {ISCC}")
    else:
        errors.append(f"Inno Setup 6 ISCC.exe not found at: {ISCC}")

    # vscode directory
    if VSCODE_DIR.exists():
        print(f"  ✓ VS Code source: {VSCODE_DIR}")
    else:
        errors.append(f"VS Code source not found. Run: git clone --depth 1 https://github.com/microsoft/vscode.git vscode")

    if errors:
        print("\n  [FAIL] PREREQUISITE FAILURES:")
        for e in errors:
            print(f"    • {e}")
        sys.exit(1)

    print("\n  ✓ All prerequisites satisfied.")


# ── Stage 1: Apply PRUBETH Branding ──────────────────────────────────────────
def stage1_brand():
    banner("STAGE 1 — Applying PRUBETH Branding")

    # Already applied: product.json was written by build script runner
    # Verify it's branded
    product_json = VSCODE_DIR / "product.json"
    data = json.loads(product_json.read_text(encoding="utf-8"))
    assert data.get("nameShort") == "PRUBETH", "product.json not branded!"
    print(f"  ✓ product.json → nameShort='{data['nameShort']}', nameLong='{data['nameLong']}'")

    # Overwrite Win32 code.ico with PRUBETH icon
    src_ico = ASSETS_DIR / "icon.ico"
    dst_ico = VSCODE_DIR / "resources" / "win32" / "code.ico"
    if src_ico.exists():
        shutil.copy2(src_ico, dst_ico)
        print(f"  ✓ Win32 icon: {dst_ico.name} ({src_ico.stat().st_size // 1024} KB)")

    # Overwrite Linux PNG icon
    src_png = ASSETS_DIR / "logo.png"
    dst_png = VSCODE_DIR / "resources" / "linux" / "code.png"
    if src_png.exists():
        shutil.copy2(src_png, dst_png)
        print(f"  ✓ Linux icon: {dst_png.name}")

    # Overwrite darwin icns with our logo.png (best-effort; macOS not target)
    dst_icns = VSCODE_DIR / "resources" / "darwin" / "code.icns"
    print(f"  [WARN] Darwin .icns not converted (Windows target only); keeping original.")

    print("\n  ✓ Branding applied.")


# ── Stage 2: npm install ─────────────────────────────────────────────────────
def stage2_npm_install():
    banner("STAGE 2 — Installing VS Code Dependencies (npm install)")
    env = os.environ.copy()
    # Skip node version check since we match exactly
    env["VSCODE_SKIP_NODE_VERSION_CHECK"] = "1"
    run(["npm", "install", "--legacy-peer-deps"], cwd=VSCODE_DIR, env=env)
    print("\n  ✓ npm install complete.")


# ── Stage 3: Compile TypeScript sources ─────────────────────────────────────
def stage3_compile():
    banner("STAGE 3 — Compiling PRUBETH IDE from Source (Gulp → Electron)")
    env = os.environ.copy()
    env["VSCODE_SKIP_NODE_VERSION_CHECK"] = "1"
    # Use VS Code's gulp compile-client target
    run(["node", "node_modules/gulp/bin/gulp.js", "compile-client"], cwd=VSCODE_DIR, env=env)
    print("\n  ✓ TypeScript compilation complete.")


# ── Stage 4: Build the Electron package (vscode-win32-x64) ──────────────────
def stage4_package():
    banner("STAGE 4 — Packaging PRUBETH IDE (Gulp → win32-x64 package)")
    env = os.environ.copy()
    env["VSCODE_SKIP_NODE_VERSION_CHECK"] = "1"
    BUILD_OUT.mkdir(parents=True, exist_ok=True)
    # This builds vscode-win32-x64 folder
    run(
        ["node", "node_modules/gulp/bin/gulp.js", "vscode-win32-x64"],
        cwd=VSCODE_DIR, env=env
    )
    # The gulp task outputs to ../VSCode-win32-x64 relative to vscode dir
    gulp_out = VSCODE_DIR.parent / "VSCode-win32-x64"
    if gulp_out.exists():
        if BUILD_OUT.exists():
            shutil.rmtree(BUILD_OUT)
        shutil.copytree(gulp_out, BUILD_OUT)
        print(f"\n  ✓ Package output: {BUILD_OUT}")
    else:
        print(f"  [WARN] Expected output at {gulp_out}, check gulp task name for this VS Code version.")
    print("\n  ✓ Packaging complete.")


# ── Stage 5: Deploy PRUBETH Icons into Final Build ───────────────────────────
def stage5_deploy_icons():
    banner("STAGE 5 — Deploying PRUBETH Branding into Final Build")
    if not BUILD_OUT.exists():
        print(f"  [WARN] Build output {BUILD_OUT} not found — skipping icon deployment (check Stage 4).")
        return

    # Replace app icon
    for exe_ico in BUILD_OUT.rglob("*.ico"):
        shutil.copy2(ASSETS_DIR / "icon.ico", exe_ico)
        print(f"  ✓ Replaced icon: {exe_ico.relative_to(BUILD_OUT)}")

    # Replace product.json in final build
    final_product = BUILD_OUT / "resources" / "app" / "product.json"
    if final_product.exists():
        shutil.copy2(VSCODE_DIR / "product.json", final_product)
        print(f"  ✓ Deployed product.json to final build")

    # Write PRUBETH assets folder inside build
    assets_dest = BUILD_OUT / "assets"
    assets_dest.mkdir(exist_ok=True)
    for f in ASSETS_DIR.iterdir():
        shutil.copy2(f, assets_dest / f.name)
    print(f"  ✓ Brand assets deployed to {assets_dest}")
    print("\n  ✓ Icon & brand deployment complete.")


# ── Stage 6: Run Inno Setup → produce Setup.exe ──────────────────────────────
def stage6_inno_setup():
    banner("STAGE 6 — Building Windows Installer (Inno Setup 6)")
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    if not ISCC.exists():
        print(f"  [FAIL] Inno Setup not found at {ISCC}")
        sys.exit(1)

    # Generate wizard images from our logo.png programmatically (BMP conversion)
    _generate_wizard_bmps()

    iss = ISS_SCRIPT
    if not iss.exists():
        print(f"  [FAIL] ISS script not found: {iss}")
        sys.exit(1)

    run([str(ISCC), str(iss)], cwd=iss.parent)
    print("\n  ✓ Inno Setup installer built successfully.")


def _generate_wizard_bmps():
    """Generate wizard BMP images for Inno Setup from PRUBETH logo using Pillow/fallback."""
    wizard_big_path = ISS_SCRIPT.parent / "prubeth-wizard-big.bmp"
    wizard_small_path = ISS_SCRIPT.parent / "prubeth-wizard-small.bmp"
    logo_src = ASSETS_DIR / "logo.png"

    if wizard_big_path.exists() and wizard_small_path.exists():
        print("  ✓ Wizard BMPs already exist, skipping generation.")
        return

    try:
        from PIL import Image
        img = Image.open(logo_src).convert("RGB")

        # Big wizard: 164×314 px (Inno Setup 100% DPI)
        big = img.resize((164, 314), Image.LANCZOS)
        big.save(str(wizard_big_path), "BMP")

        # Small wizard: 55×55 px
        small = img.resize((55, 55), Image.LANCZOS)
        small.save(str(wizard_small_path), "BMP")

        print(f"  ✓ Wizard BMP images generated: {wizard_big_path.name}, {wizard_small_path.name}")
    except ImportError:
        # Fallback: copy VS Code's existing wizard images and tint them
        for src_name, dst in [
            ("inno-big-100.bmp", wizard_big_path),
            ("inno-small-100.bmp", wizard_small_path)
        ]:
            src = ISS_SCRIPT.parent / src_name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
        print("  [WARN] Pillow not available; using VS Code wizard images as fallback.")


# ── Stage 7: Release Summary ─────────────────────────────────────────────────
def stage7_summary():
    banner("STAGE 7 — Release Summary")
    output_exe = DIST_DIR / f"PrubethIDE-v{APP_VERSION}-Setup.exe"
    if output_exe.exists():
        size_mb = output_exe.stat().st_size / (1024 * 1024)
        sha256 = hashlib.sha256(output_exe.read_bytes()).hexdigest()
        print(f"  ✓ Installer: {output_exe.name}")
        print(f"  ✓ Size:      {size_mb:.1f} MiB")
        print(f"  ✓ SHA-256:   {sha256}")
        print(f"  ✓ Path:      {output_exe}")
    else:
        # Scan dist/ for any newly created exe
        exes = sorted(DIST_DIR.glob("Prubeth*.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
        if exes:
            newest = exes[0]
            size_mb = newest.stat().st_size / (1024 * 1024)
            print(f"  ✓ Installer: {newest.name} ({size_mb:.1f} MiB)")
            print(f"  ✓ Path:      {newest}")
        else:
            print(f"  [WARN] No installer found in {DIST_DIR}. Check build logs above.")

    print(f"\n  Built: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Publisher: {PUBLISHER}")
    print(f"  Website: https://www.bsvr.work/\n")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PRUBETH IDE Build Orchestrator")
    parser.add_argument("--stage", type=int, default=0,
                        help="Start from stage N (0=all, 1=brand, 2=npm, 3=compile, 4=package, 5=icons, 6=inno, 7=summary)")
    parser.add_argument("--only-stage", type=int, default=None,
                        help="Run only this specific stage")
    parser.add_argument("--skip-compile", action="store_true",
                        help="Skip stages 3 & 4 (use existing prubeth-build/)")
    args = parser.parse_args()

    stages = [
        stage0_verify,
        stage1_brand,
        stage2_npm_install,
        stage3_compile,
        stage4_package,
        stage5_deploy_icons,
        stage6_inno_setup,
        stage7_summary,
    ]

    if args.only_stage is not None:
        stages[args.only_stage]()
    elif args.skip_compile:
        for fn in [stage0_verify, stage1_brand, stage5_deploy_icons, stage6_inno_setup, stage7_summary]:
            fn()
    else:
        for i, fn in enumerate(stages):
            if i >= args.stage:
                fn()
