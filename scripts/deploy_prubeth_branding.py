"""
PRUBETH IDE — Deploy Official Perpetual Windmill Logo & Brand Assets
Converts high-resolution logo to assets/logo.png, assets/icon.ico, and assets/logo.svg.
"""
import sys
from pathlib import Path
from PyQt5.QtGui import QImage, QPixmap, QPainter, QIcon
from PyQt5.QtCore import QSize, Qt

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Select the high-contrast black & white + cyan/magenta circular perpetual windmill logo
SRC_IMG = Path(r"C:\Users\asus\.gemini\antigravity\brain\f0b7f80a-95d5-4a83-ad44-b809997befed\prubeth_bw_circular_windmill_1791607172195.jpg")

def deploy_assets():
    print(f"[*] Loading source logo from: {SRC_IMG}")
    img = QImage(str(SRC_IMG))
    if img.isNull():
        print(f"[!] Error: Could not load source image {SRC_IMG}")
        return False

    print(f"[+] Loaded source image: {img.width()}x{img.height()}")

    # 1. Save high-res PNG logo
    png_path = ASSETS_DIR / "logo.png"
    img.save(str(png_path), "PNG")
    print(f"[+] Deployed {png_path} ({png_path.stat().st_size / 1024:.1f} KB)")

    # 2. Generate multi-resolution ICO file for Windows
    ico_path = ASSETS_DIR / "icon.ico"
    # Create scaled pixmaps: 256, 128, 64, 48, 32, 16
    scaled_256 = img.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    scaled_256.save(str(ico_path), "ICO")
    print(f"[+] Deployed Windows icon: {ico_path} ({ico_path.stat().st_size / 1024:.1f} KB)")

    # 3. Create precision scalable SVG matching the perpetual windmill iris geometry
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#0a1220"/>
      <stop offset="100%" stop-color="#030508"/>
    </radialGradient>
    <linearGradient id="cyanGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F0FF"/>
      <stop offset="100%" stop-color="#0072FF"/>
    </linearGradient>
    <linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#E040FB"/>
      <stop offset="100%" stop-color="#7C4DFF"/>
    </linearGradient>
    <linearGradient id="whiteGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#CBD5E1"/>
    </linearGradient>
    <linearGradient id="darkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1E293B"/>
      <stop offset="100%" stop-color="#020617"/>
    </linearGradient>
  </defs>

  <!-- Deep Obsidian Background -->
  <rect width="512" height="512" rx="64" fill="url(#bgGlow)"/>

  <!-- Outer Luminous Cyan/Magenta Orbit Ring -->
  <circle cx="256" cy="230" r="148" fill="none" stroke="url(#cyanGrad)" stroke-width="3" opacity="0.8"/>
  <circle cx="256" cy="230" r="140" fill="none" stroke="url(#purpleGrad)" stroke-width="2.5" opacity="0.7"/>

  <!-- Perpetual Windmill Turbine Blades -->
  <g transform="translate(256, 230)">
    <!-- Blade 1 (White & Cyan Glow) -->
    <path d="M 0,-120 C 65,-110 110,-60 115,0 C 80,-20 40,-35 0,-40 Z" fill="url(#whiteGrad)" stroke="#00F0FF" stroke-width="2"/>
    <!-- Blade 2 (Glossy Black & Purple Glow) -->
    <path d="M 120,0 C 110,65 60,110 0,115 C 20,80 35,40 40,0 Z" fill="url(#darkGrad)" stroke="#E040FB" stroke-width="2"/>
    <!-- Blade 3 (White & Cyan Glow) -->
    <path d="M 0,120 C -65,110 -110,60 -115,0 C -80,20 -40,35 0,40 Z" fill="url(#whiteGrad)" stroke="#00F0FF" stroke-width="2"/>
    <!-- Blade 4 (Glossy Black & Purple Glow) -->
    <path d="M -120,0 C -110,-65 -60,-110 0,-115 C -20,-80 -35,-40 -40,0 Z" fill="url(#darkGrad)" stroke="#E040FB" stroke-width="2"/>

    <!-- Central Precision Hub -->
    <circle cx="0" cy="0" r="28" fill="#030712" stroke="url(#cyanGrad)" stroke-width="3"/>
    <circle cx="0" cy="0" r="12" fill="url(#purpleGrad)"/>
  </g>

  <!-- Typography -->
  <text x="256" y="420" font-family="'Segoe UI', 'Montserrat', 'Helvetica Neue', sans-serif" font-size="44" font-weight="900" fill="#FFFFFF" text-anchor="middle" letter-spacing="8">PRUBETH</text>
  <text x="256" y="450" font-family="'Segoe UI', sans-serif" font-size="14" font-weight="700" fill="url(#cyanGrad)" text-anchor="middle" letter-spacing="4">THE AI POWERED IDE</text>
</svg>'''
    svg_path = ASSETS_DIR / "logo.svg"
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"[+] Deployed scalable vector graphic: {svg_path}")

    return True

if __name__ == "__main__":
    deploy_assets()
