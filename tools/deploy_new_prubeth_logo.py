"""
Deploys the new official PRUBETH hexagonal neural processor logo across all targets,
generating multi-resolution RGBA PNGs, Windows multi-size ICOs, and vector SVGs.
"""
import os
import sys
import base64
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_IMAGE = Path(r"C:\Users\asus\.gemini\antigravity\brain\dc753c71-f989-4a43-96f6-48ca6e6fe02b\.user_uploaded\media_1792437643596_cbb85639.jpg")

print(f"Loading master source image: {SOURCE_IMAGE}")
if not SOURCE_IMAGE.exists():
    print(f"ERROR: Master image {SOURCE_IMAGE} not found!")
    sys.exit(1)

master_img = Image.open(SOURCE_IMAGE).convert("RGB")
w, h = master_img.size
print(f"Master image loaded: {w}x{h}")

# 1. Create transparent dark-mode logo (white emblem on transparent background)
# Use luminance threshold with smooth anti-aliased alpha ramp
gray = master_img.convert("L")
# Luminance: pixels < 25 are background (alpha = 0), > 100 are full foreground (alpha = 255)
alpha = gray.point(lambda p: 0 if p < 25 else (255 if p > 100 else int((p - 25) * 255 / 75)))

# Clean white emblem with original highlights
white_emblem = Image.new("RGBA", (w, h), (255, 255, 255, 0))
white_emblem.putalpha(alpha)

# Also create the original high-contrast RGBA emblem preserving subtle shading
r, g, b = master_img.split()
rgba_orig = Image.merge("RGBA", (r, g, b, alpha))

# 2. Create light-mode logo (dark obsidian #0A0D14 emblem on transparent background)
light_emblem = Image.new("RGBA", (w, h), (15, 23, 42, 0)) # Slate-900 obsidian
light_emblem.putalpha(alpha)

# 3. Create Solid Square Logo with dark background
solid_square = master_img.copy()

# 4. Save to assets/
assets_dir = REPO_ROOT / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)

logo_png = assets_dir / "logo.png"
logo_dark_png = assets_dir / "logo_dark.png"
logo_light_png = assets_dir / "logo_light.png"
icon_ico = assets_dir / "icon.ico"

# Save PNGs
rgba_orig.save(logo_png, format="PNG", optimize=True)
rgba_orig.save(logo_dark_png, format="PNG", optimize=True)
light_emblem.save(logo_light_png, format="PNG", optimize=True)
print(f"Saved: {logo_png}, {logo_dark_png}, {logo_light_png}")

# Generate multi-size Windows ICO (256, 128, 64, 48, 32, 16)
ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
ico_imgs = [rgba_orig.resize(sz, Image.Resampling.LANCZOS) for sz in ico_sizes]
ico_imgs[0].save(icon_ico, format="ICO", sizes=ico_sizes, append_images=ico_imgs[1:])
print(f"Saved multi-resolution ICO: {icon_ico}")

# 5. Convert to Base64 PNG for inline SVG embedding
with open(logo_png, "rb") as f:
    b64_dark = base64.b64encode(f.read()).decode("ascii")
with open(logo_light_png, "rb") as f:
    b64_light = base64.b64encode(f.read()).decode("ascii")

svg_dark_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <filter id="prubethGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#00F0FF" flood-opacity="0.45"/>
    </filter>
  </defs>
  <image href="data:image/png;base64,{b64_dark}" width="512" height="512" filter="url(#prubethGlow)"/>
</svg>'''

svg_light_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <filter id="prubethShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0F172A" flood-opacity="0.3"/>
    </filter>
  </defs>
  <image href="data:image/png;base64,{b64_light}" width="512" height="512" filter="url(#prubethShadow)"/>
</svg>'''

# Save SVGs
logo_svg = assets_dir / "logo.svg"
logo_svg.write_text(svg_dark_content, encoding="utf-8")
print(f"Saved: {logo_svg}")

# 6. Distribute across vscode source tree
vscode_dir = REPO_ROOT / "vscode"
code_ico_win = vscode_dir / "resources" / "win32" / "code.ico"
code_png_linux = vscode_dir / "resources" / "linux" / "code.png"
prubeth_svg_linux = vscode_dir / "resources" / "linux" / "prubeth.svg"
favicon_server = vscode_dir / "resources" / "server" / "favicon.ico"

code_ico_win.parent.mkdir(parents=True, exist_ok=True)
code_png_linux.parent.mkdir(parents=True, exist_ok=True)
favicon_server.parent.mkdir(parents=True, exist_ok=True)

ico_imgs[0].save(code_ico_win, format="ICO", sizes=ico_sizes, append_images=ico_imgs[1:])
rgba_orig.resize((512, 512), Image.Resampling.LANCZOS).save(code_png_linux, format="PNG")
prubeth_svg_linux.write_text(svg_dark_content, encoding="utf-8")
ico_imgs[0].save(favicon_server, format="ICO", sizes=[(32, 32), (16, 16)], append_images=[ico_imgs[-1]])
print("Saved VS Code source resources: code.ico, code.png, prubeth.svg, favicon.ico")

# Sessions media SVGs
for media_dir in [
    vscode_dir / "src" / "vs" / "sessions" / "browser" / "media",
    vscode_dir / "out" / "vs" / "sessions" / "browser" / "media",
]:
    if media_dir.exists():
        (media_dir / "sessions-logo-dark.svg").write_text(svg_dark_content, encoding="utf-8")
        (media_dir / "sessions-logo-light.svg").write_text(svg_light_content, encoding="utf-8")
        print(f"Saved sessions SVG to: {media_dir}")

# Theme extension icon
theme_icon = vscode_dir / "extensions" / "prubeth-theme" / "icon.png"
if theme_icon.parent.exists():
    rgba_orig.resize((128, 128), Image.Resampling.LANCZOS).save(theme_icon, format="PNG")
    print(f"Saved theme icon: {theme_icon}")

# 7. Distribute to installed target: C:\Users\asus\AppData\Local\Programs\PRUBETH IDE
installed_dir = Path(r"C:\Users\asus\AppData\Local\Programs\PRUBETH IDE")
if installed_dir.exists():
    inst_assets = installed_dir / "assets"
    inst_assets.mkdir(parents=True, exist_ok=True)
    rgba_orig.save(inst_assets / "logo.png", format="PNG")
    ico_imgs[0].save(inst_assets / "icon.ico", format="ICO", sizes=ico_sizes, append_images=ico_imgs[1:])
    (inst_assets / "logo.svg").write_text(svg_dark_content, encoding="utf-8")

    inst_win32_ico = installed_dir / "resources" / "app" / "resources" / "win32" / "code.ico"
    if inst_win32_ico.parent.exists():
        ico_imgs[0].save(inst_win32_ico, format="ICO", sizes=ico_sizes, append_images=ico_imgs[1:])

    inst_media = installed_dir / "resources" / "app" / "out" / "media"
    if inst_media.exists():
        (inst_media / "sessions-logo-dark.svg").write_text(svg_dark_content, encoding="utf-8")
        (inst_media / "sessions-logo-light.svg").write_text(svg_light_content, encoding="utf-8")

    inst_theme_icon = installed_dir / "resources" / "app" / "extensions" / "prubeth-theme" / "icon.png"
    if inst_theme_icon.parent.exists():
        rgba_orig.resize((128, 128), Image.Resampling.LANCZOS).save(inst_theme_icon, format="PNG")
    print("Deployed new logo to installed runtime: C:\\Users\\asus\\AppData\\Local\\Programs\\PRUBETH IDE")

# 8. Distribute to build tree: VSCode-win32-x64
build_tree = REPO_ROOT / "VSCode-win32-x64"
if build_tree.exists():
    b_win32_ico = build_tree / "resources" / "app" / "resources" / "win32" / "code.ico"
    if b_win32_ico.parent.exists():
        ico_imgs[0].save(b_win32_ico, format="ICO", sizes=ico_sizes, append_images=ico_imgs[1:])

    b_media = build_tree / "resources" / "app" / "out" / "media"
    if b_media.exists():
        (b_media / "sessions-logo-dark.svg").write_text(svg_dark_content, encoding="utf-8")
        (b_media / "sessions-logo-light.svg").write_text(svg_light_content, encoding="utf-8")

    b_theme_icon = build_tree / "resources" / "app" / "extensions" / "prubeth-theme" / "icon.png"
    if b_theme_icon.parent.exists():
        rgba_orig.resize((128, 128), Image.Resampling.LANCZOS).save(b_theme_icon, format="PNG")
    print("Deployed new logo to build tree: VSCode-win32-x64")

print("All PRUBETH logo assets successfully deployed across the entire platform!")
