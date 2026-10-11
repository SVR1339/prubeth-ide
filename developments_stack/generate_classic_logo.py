import os
import sys
from pathlib import Path
from PyQt5.QtCore import QByteArray, QSize, Qt
from PyQt5.QtGui import QImage, QPainter, QIcon, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication

# Initialize headless Qt Application if needed
app = QApplication.instance()
if not app:
    app = QApplication([sys.argv[0], "-platform", "offscreen"])

ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Classic White and Silver Architectural Vector Logo
SVG_CONTENT = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Specular White-Silver Linear Gradient -->
    <linearGradient id="silverGleam" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="25%" stop-color="#F8FAFC"/>
      <stop offset="50%" stop-color="#E2E8F0"/>
      <stop offset="75%" stop-color="#CBD5E1"/>
      <stop offset="100%" stop-color="#94A3B8"/>
    </linearGradient>

    <!-- Brushed Platinum Linear Gradient (Reverse) -->
    <linearGradient id="platinumLuster" x1="100%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="30%" stop-color="#F1F5F9"/>
      <stop offset="70%" stop-color="#CBD5E1"/>
      <stop offset="100%" stop-color="#64748B"/>
    </linearGradient>

    <!-- Deep Titanium Shadow Gradient -->
    <linearGradient id="titaniumShadow" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0F172A"/>
      <stop offset="40%" stop-color="#1E293B"/>
      <stop offset="80%" stop-color="#475569"/>
      <stop offset="100%" stop-color="#94A3B8"/>
    </linearGradient>

    <!-- High-Reflective Chrome Specular -->
    <linearGradient id="chromeSpecular" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.95"/>
      <stop offset="35%" stop-color="#E2E8F0" stop-opacity="0.7"/>
      <stop offset="65%" stop-color="#94A3B8" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0.8"/>
    </linearGradient>

    <!-- Subtle Violet Core Gleam -->
    <linearGradient id="coreViolet" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#B4A9FF"/>
      <stop offset="50%" stop-color="#9485FF"/>
      <stop offset="100%" stop-color="#62D4E5"/>
    </linearGradient>

    <!-- Radial Silver Sheen -->
    <radialGradient id="radialSheen" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.25"/>
      <stop offset="60%" stop-color="#CBD5E1" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>

    <!-- Drop Shadow Filter for Facet Depth -->
    <filter id="facetDepth" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#000000" flood-opacity="0.45"/>
    </filter>

    <filter id="ambientGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="12" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- Ambient Light Reflection -->
  <circle cx="256" cy="240" r="210" fill="url(#radialSheen)"/>

  <!-- Main Geometric Chiseled Emblem Group -->
  <g filter="url(#facetDepth)">
    <!-- Outer Precision Diamond Bezel -->
    <path d="M 256,36 L 440,220 L 256,404 L 72,220 Z" 
          fill="none" 
          stroke="url(#silverGleam)" 
          stroke-width="3" 
          stroke-linecap="round" 
          stroke-linejoin="round" 
          opacity="0.7"/>

    <!-- Subtle Secondary Geometric Framing Orbit -->
    <circle cx="256" cy="220" r="150" 
            fill="none" 
            stroke="url(#platinumLuster)" 
            stroke-width="1.5" 
            stroke-dasharray="8 6" 
            opacity="0.4"/>

    <!-- NORTH FACET: Chiseled Ascendant Blade (Polished Silver) -->
    <path d="M 256,56 L 256,220 L 196,160 Z" 
          fill="url(#silverGleam)"/>
    <path d="M 256,56 L 316,160 L 256,220 Z" 
          fill="url(#titaniumShadow)"/>

    <!-- SOUTH FACET: Chiseled Descendant Blade (Polished Platinum) -->
    <path d="M 256,384 L 256,220 L 316,280 Z" 
          fill="url(#silverGleam)"/>
    <path d="M 256,384 L 196,280 L 256,220 Z" 
          fill="url(#titaniumShadow)"/>

    <!-- EAST FACET: Chiseled Lateral Blade (Bright Sterling) -->
    <path d="M 420,220 L 256,220 L 316,160 Z" 
          fill="url(#platinumLuster)"/>
    <path d="M 420,220 L 316,280 L 256,220 Z" 
          fill="url(#titaniumShadow)"/>

    <!-- WEST FACET: Chiseled Lateral Blade (Deep Shadowed Platinum) -->
    <path d="M 92,220 L 256,220 L 196,280 Z" 
          fill="url(#platinumLuster)"/>
    <path d="M 92,220 L 196,160 L 256,220 Z" 
          fill="url(#titaniumShadow)"/>

    <!-- SPECULAR CHROME RIDGES (Specular Edge Highlights) -->
    <line x1="256" y1="56" x2="256" y2="384" stroke="url(#chromeSpecular)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="92" y1="220" x2="420" y2="220" stroke="url(#chromeSpecular)" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="196" y1="160" x2="316" y2="280" stroke="#FFFFFF" stroke-width="1.5" opacity="0.8"/>
    <line x1="196" y1="280" x2="316" y2="160" stroke="#CBD5E1" stroke-width="1.5" opacity="0.8"/>

    <!-- CENTRAL NUCLEUS: Floating Diamond Prism -->
    <path d="M 256,186 L 290,220 L 256,254 L 222,220 Z" 
          fill="url(#silverGleam)" 
          stroke="url(#coreViolet)" 
          stroke-width="2.5"/>

    <!-- Inner Core Cyber-Gleam Dot -->
    <circle cx="256" cy="220" r="8" fill="url(#coreViolet)"/>
    <circle cx="256" cy="220" r="3" fill="#FFFFFF"/>
  </g>

  <!-- Precision Silver Coordinates & Accents -->
  <circle cx="256" cy="56" r="4" fill="#FFFFFF"/>
  <circle cx="420" cy="220" r="4" fill="#FFFFFF"/>
  <circle cx="256" cy="384" r="4" fill="#FFFFFF"/>
  <circle cx="92" cy="220" r="4" fill="#FFFFFF"/>

  <!-- High-End Classic Typography -->
  <text x="256" y="446" 
        font-family="'Segoe UI', 'Cinzel', 'Trajan Pro', 'Helvetica Neue', sans-serif" 
        font-size="36" 
        font-weight="700" 
        fill="#FFFFFF" 
        text-anchor="middle" 
        letter-spacing="14">PRUBETH</text>
  <text x="256" y="474" 
        font-family="'Segoe UI', -apple-system, sans-serif" 
        font-size="12" 
        font-weight="600" 
        fill="#94A3B8" 
        text-anchor="middle" 
        letter-spacing="6">STUDIO WORKSTATION</text>
</svg>'''

def generate_assets():
    # 1. Save SVG
    svg_path = ASSETS_DIR / "logo.svg"
    svg_path.write_text(SVG_CONTENT, encoding="utf-8")
    print(f"[+] Written vector: {svg_path}")

    # 2. Render High-Res PNGs using QSvgRenderer
    renderer = QSvgRenderer(QByteArray(SVG_CONTENT.encode("utf-8")))

    # 512x512 Master Logo PNG
    img_512 = QImage(512, 512, QImage.Format_ARGB32_Premultiplied)
    img_512.fill(Qt.transparent)
    p = QPainter(img_512)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    renderer.render(p)
    p.end()

    png_path = ASSETS_DIR / "logo.png"
    img_512.save(str(png_path), "PNG")
    print(f"[+] Generated: {png_path} ({img_512.width()}x{img_512.height()})")

    dark_path = ASSETS_DIR / "logo_dark.png"
    img_512.save(str(dark_path), "PNG")
    print(f"[+] Generated: {dark_path}")

    # Light Variant with slight dark contrast backing if needed, or pure transparent
    light_path = ASSETS_DIR / "logo_light.png"
    img_512.save(str(light_path), "PNG")
    print(f"[+] Generated: {light_path}")

    # 3. Generate multi-resolution icon.ico
    # We can use Pillow to combine multiple sizes into one true Windows .ico
    from PIL import Image
    import io

    # Save 512 to PIL Image
    pil_master = Image.open(str(png_path))
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    ico_path = ASSETS_DIR / "icon.ico"
    pil_master.save(str(ico_path), format="ICO", sizes=ico_sizes)
    print(f"[+] Generated multi-resolution Windows icon: {ico_path} with sizes: {ico_sizes}")

if __name__ == "__main__":
    generate_assets()
