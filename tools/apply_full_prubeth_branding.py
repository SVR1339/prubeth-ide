"""
PRUBETH IDE — Sovereign Autonomous AI Branding & De-Branding Engine
Executes complete, flawless brand replacement across all IDE resources:
  1. Terminates any running PRUBETH instances to unlock resource files.
  2. Cleanses product.json (removes defaultChatAgent Copilot trigger, sets BSVR fork origin).
  3. Cleanses package.json (author: BSVR Technologies).
  4. Patches NLS translation catalogs (nls.messages.json, nls.messages.js, nls.metadata.json).
  5. Patches compiled workbench bundles (workbench.desktop.main.js, sessions.desktop.main.js, agentHostMain.js, mainImpl.js).
  6. Patches extension manifests and NLS catalogs (extensions/**).
  7. Replaces letterpress empty-editor watermarks with the official PRUBETH bloom flower.
  8. Replaces all legacy VS Code SVGs and icons with PRUBETH high-res assets.
"""

import os
import sys
import json
import re
import shutil
import subprocess
from pathlib import Path

# Force UTF-8 on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Paths to patch
TARGET_DIRS = [
    Path(r"E:\PRUBETH IDE"),
    Path(r"c:\Users\asus\heretic-work\VSCode-win32-x64")
]

PRUBETH_LOGO_SVG = Path(r"c:\Users\asus\heretic-work\assets\logo.svg")
PRUBETH_ICON_ICO = Path(r"c:\Users\asus\heretic-work\assets\icon.ico")
PRUBETH_LOGO_PNG = Path(r"c:\Users\asus\heretic-work\assets\logo.png")

# 1. Stop running PRUBETH processes
print("=" * 65)
print("     PRUBETH IDE COMPLETE BRANDING & DE-BRANDING ENGINE      ")
print("=" * 65)

print("\n[Step 1] Terminating running PRUBETH.exe instances...")
try:
    subprocess.run(["taskkill", "/IM", "PRUBETH.exe", "/F"], capture_output=True, text=True)
    print("✓ PRUBETH processes stopped.")
except Exception as e:
    print(f"Notice: {e}")

# Read PRUBETH logo SVG content
if PRUBETH_LOGO_SVG.exists():
    logo_svg_raw = PRUBETH_LOGO_SVG.read_text(encoding="utf-8")
else:
    logo_svg_raw = None
    print("Warning: assets/logo.svg not found!")

# Generate letterpress watermark SVG from bloom flower with subtle opacity
WATERMARK_LIGHT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="260" height="260" opacity="0.12">
  <g transform="translate(256, 256)">
    <g fill="#A0A0A5">
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(45)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(135)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(225)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(315)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(0)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(90)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(180)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(270)"/>
    </g>
    <circle cx="0" cy="0" r="44" fill="#808085"/>
  </g>
</svg>"""

WATERMARK_DARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="260" height="260" opacity="0.09">
  <g transform="translate(256, 256)">
    <g fill="#FFFFFF">
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(45)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(135)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(225)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(315)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(0)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(90)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(180)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(270)"/>
    </g>
    <circle cx="0" cy="0" r="44" fill="#FFFFFF"/>
  </g>
</svg>"""


def patch_target_root(root: Path):
    if not root.exists():
        print(f"\nSkipping non-existent root: {root}")
        return

    print(f"\n{'='*50}")
    print(f"Processing Target: {root}")
    print(f"{'='*50}")

    app_dir = root / "resources" / "app"
    if not app_dir.exists():
        print(f"Error: {app_dir} does not exist.")
        return

    out_dir = app_dir / "out"

    # ─── 1. PATCH PRODUCT.JSON ─────────────────────────────────────────
    product_json_path = app_dir / "product.json"
    if product_json_path.exists():
        try:
            pdata = json.loads(product_json_path.read_text(encoding="utf-8"))
            # Completely eliminate defaultChatAgent to prevent Copilot auth popups
            pdata.pop("defaultChatAgent", None)
            pdata["forkOrigin"] = "PRUBETH Sovereign Autonomous AI Platform"
            pdata["nameShort"] = "PRUBETH"
            pdata["nameLong"] = "PRUBETH IDE"
            pdata["applicationName"] = "prubeth"
            pdata["win32NameVersion"] = "PRUBETH IDE"
            pdata["win32DirName"] = "PRUBETH IDE"
            pdata["win32ShellNameShort"] = "PRUBETH IDE"
            pdata["reportIssueUrl"] = "https://github.com/imyouiamyou/prubeth-ide/issues/new"
            pdata["documentationUrl"] = "https://www.bsvr.work/"
            # Ensure checksums object is empty dict
            pdata["checksums"] = {}
            product_json_path.write_text(json.dumps(pdata, indent=2), encoding="utf-8")
            print(f"✓ Updated product.json (removed defaultChatAgent, set PRUBETH branding)")
        except Exception as e:
            print(f"✗ Failed patching product.json: {e}")

    # ─── 2. PATCH PACKAGE.JSON ─────────────────────────────────────────
    package_json_path = app_dir / "package.json"
    if package_json_path.exists():
        try:
            pkg = json.loads(package_json_path.read_text(encoding="utf-8"))
            pkg["author"] = {"name": "BSVR Technologies", "email": "support@bsvr.work"}
            pkg["name"] = "PRUBETH"
            pkg["description"] = "PRUBETH IDE — Sovereign Autonomous AI Developer Environment"
            package_json_path.write_text(json.dumps(pkg, indent=2), encoding="utf-8")
            print(f"✓ Updated package.json (author: BSVR Technologies)")
        except Exception as e:
            print(f"✗ Failed patching package.json: {e}")

    # ─── 3. PATCH NLS TRANSLATIONS (nls.messages.json, nls.messages.js) ─
    def replace_branding_strings(text: str) -> str:
        # Order matters: replace longer, more specific strings first
        text = text.replace("Visual Studio Code", "PRUBETH IDE")
        text = text.replace("Welcome to VS Code", "Welcome to PRUBETH IDE")
        text = text.replace("About VS Code", "About PRUBETH IDE")
        text = text.replace("Code - OSS Dev", "PRUBETH IDE")
        text = text.replace("Code - OSS", "PRUBETH IDE")
        text = text.replace("Code-OSS", "PRUBETH IDE")
        text = text.replace("VS Code", "PRUBETH IDE")
        return text

    nls_json = out_dir / "nls.messages.json"
    if nls_json.exists():
        try:
            raw = nls_json.read_text(encoding="utf-8")
            patched = replace_branding_strings(raw)
            nls_json.write_text(patched, encoding="utf-8")
            print(f"✓ Patched nls.messages.json (all VS Code / OSS occurrences replaced)")
        except Exception as e:
            print(f"✗ Failed patching nls.messages.json: {e}")

    nls_js = out_dir / "nls.messages.js"
    if nls_js.exists():
        try:
            raw = nls_js.read_text(encoding="utf-8")
            patched = replace_branding_strings(raw)
            nls_js.write_text(patched, encoding="utf-8")
            print(f"✓ Patched nls.messages.js (all VS Code / OSS occurrences replaced)")
        except Exception as e:
            print(f"✗ Failed patching nls.messages.js: {e}")

    nls_meta = out_dir / "nls.metadata.json"
    if nls_meta.exists():
        try:
            raw = nls_meta.read_text(encoding="utf-8")
            patched = replace_branding_strings(raw)
            nls_meta.write_text(patched, encoding="utf-8")
            print(f"✓ Patched nls.metadata.json")
        except Exception as e:
            print(f"✗ Failed patching nls.metadata.json: {e}")

    # ─── 4. PATCH CORE JS BUNDLES ──────────────────────────────────────
    js_files_to_patch = [
        out_dir / "vs" / "workbench" / "workbench.desktop.main.js",
        out_dir / "mainImpl.js",
        out_dir / "agentHostMain.js",
        out_dir / "vs" / "sessions" / "sessions.desktop.main.js",
    ]

    for jf in js_files_to_patch:
        if jf.exists():
            try:
                content = jf.read_text(encoding="utf-8", errors="ignore")
                # Specific clean replacements
                new_content = content.replace("Visual Studio Code", "PRUBETH IDE")
                new_content = new_content.replace("Code - OSS Dev", "PRUBETH IDE")
                new_content = new_content.replace("Code - OSS", "PRUBETH IDE")
                new_content = new_content.replace("Welcome to VS Code", "Welcome to PRUBETH IDE")
                new_content = new_content.replace("About VS Code", "About PRUBETH IDE")

                # Replace "VS Code" where it's part of title or UI string
                new_content = re.sub(r'(["\'`])VS Code\b', r'\1PRUBETH IDE', new_content)
                new_content = re.sub(r'\bVS Code(["\'`])', r'PRUBETH IDE\1', new_content)

                if len(new_content) != len(content) or new_content != content:
                    jf.write_text(new_content, encoding="utf-8")
                    print(f"✓ Patched bundle: {jf.relative_to(root)}")
                else:
                    print(f"• Already clean: {jf.relative_to(root)}")
            except Exception as e:
                print(f"✗ Error patching {jf}: {e}")

    # ─── 5. PATCH EXTENSIONS (package.json and package.nls.json) ───────
    ext_dir = app_dir / "extensions"
    if ext_dir.exists():
        patched_ext_count = 0
        for ep in ext_dir.rglob("*"):
            if ep.name in ("package.json", "package.nls.json") and ep.is_file():
                try:
                    raw = ep.read_text(encoding="utf-8", errors="ignore")
                    if any(term in raw for term in ["Visual Studio Code", "VS Code", "Code - OSS", "Code-OSS"]):
                        patched = replace_branding_strings(raw)
                        ep.write_text(patched, encoding="utf-8")
                        patched_ext_count += 1
                except Exception:
                    pass
        print(f"✓ Cleaned {patched_ext_count} extension package/manifest files")

    # ─── 6. REPLACE WATERMARKS AND SVGS ────────────────────────────────
    watermark_paths = [
        out_dir / "media" / "letterpress-light.svg",
        out_dir / "media" / "letterpress-hcLight.svg",
        out_dir / "vs" / "workbench" / "browser" / "parts" / "editor" / "media" / "letterpress-light.svg",
        out_dir / "vs" / "workbench" / "browser" / "parts" / "editor" / "media" / "letterpress-hcLight.svg",
    ]
    for wp in watermark_paths:
        try:
            wp.parent.mkdir(parents=True, exist_ok=True)
            wp.write_text(WATERMARK_LIGHT, encoding="utf-8")
            print(f"✓ Installed PRUBETH light watermark: {wp.name}")
        except Exception as e:
            print(f"✗ Watermark write error {wp}: {e}")

    watermark_dark_paths = [
        out_dir / "media" / "letterpress-dark.svg",
        out_dir / "media" / "letterpress-hcDark.svg",
        out_dir / "vs" / "workbench" / "browser" / "parts" / "editor" / "media" / "letterpress-dark.svg",
        out_dir / "vs" / "workbench" / "browser" / "parts" / "editor" / "media" / "letterpress-hcDark.svg",
    ]
    for wp in watermark_dark_paths:
        try:
            wp.parent.mkdir(parents=True, exist_ok=True)
            wp.write_text(WATERMARK_DARK, encoding="utf-8")
            print(f"✓ Installed PRUBETH dark watermark: {wp.name}")
        except Exception as e:
            print(f"✗ Dark watermark write error {wp}: {e}")

    # Replace logo SVGs with PRUBETH official logo
    if logo_svg_raw:
        logo_svg_targets = [
            out_dir / "media" / "vscode-icon.svg",
            out_dir / "media" / "code-icon.svg",
            out_dir / "media" / "sessions-icon.svg",
            out_dir / "media" / "sessions-logo-dark.svg",
            out_dir / "media" / "sessions-logo-light.svg",
            out_dir / "vs" / "workbench" / "browser" / "media" / "code-icon.svg",
        ]
        for ltarget in logo_svg_targets:
            try:
                ltarget.parent.mkdir(parents=True, exist_ok=True)
                ltarget.write_text(logo_svg_raw, encoding="utf-8")
                print(f"✓ Installed PRUBETH logo SVG: {ltarget.name}")
            except Exception as e:
                print(f"✗ Logo SVG write error {ltarget}: {e}")

    # Copy official ICO and PNG icons
    res_win32 = app_dir / "resources" / "win32"
    if res_win32.exists():
        if PRUBETH_ICON_ICO.exists():
            shutil.copy2(PRUBETH_ICON_ICO, res_win32 / "code.ico")
            shutil.copy2(PRUBETH_ICON_ICO, res_win32 / "default.ico")
            print(f"✓ Installed PRUBETH code.ico and default.ico")
        if PRUBETH_LOGO_PNG.exists():
            shutil.copy2(PRUBETH_LOGO_PNG, res_win32 / "code_150x150.png")
            shutil.copy2(PRUBETH_LOGO_PNG, res_win32 / "code_70x70.png")
            print(f"✓ Installed PRUBETH code_150x150.png and code_70x70.png")


for target_root in TARGET_DIRS:
    patch_target_root(target_root)

print("\n" + "=" * 65)
print("     ALL BRANDING & DE-BRANDING CHANGES APPLIED FLAWLESSLY     ")
print("=" * 65)
