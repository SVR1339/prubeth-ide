"""
Generate iconic, ultra-crisp brand assets for SO NAIVE IDE:
- assets/logo.svg
- assets/logo.png (512x512)
- assets/icon.ico (Windows multi-res icon: 256, 128, 64, 48, 32, 16)
"""
import os
import sys
import struct
import io
from pathlib import Path
from PyQt5.QtCore import Qt, QPointF, QRectF, QBuffer, QIODevice
from PyQt5.QtGui import (
    QImage, QPainter, QColor, QRadialGradient, QLinearGradient,
    QPen, QPainterPath, QBrush
)
from PyQt5.QtWidgets import QApplication

def create_svg(assets_dir: Path):
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1e1b4b" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#0a0a0f" stop-opacity="1"/>
    </radialGradient>
    <linearGradient id="neonCyan" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F0FF"/>
      <stop offset="50%" stop-color="#7000FF"/>
      <stop offset="100%" stop-color="#FF007A"/>
    </linearGradient>
    <linearGradient id="coreGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#00F0FF"/>
    </linearGradient>
    <filter id="neonBlur" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="12" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Base Dark Canvas -->
  <rect width="512" height="512" rx="110" fill="url(#bgGlow)" stroke="#27273a" stroke-width="4"/>

  <!-- Subtle Cybernetic Grid Ring -->
  <circle cx="256" cy="256" r="180" fill="none" stroke="#2a2a40" stroke-width="2" stroke-dasharray="8 6"/>
  <circle cx="256" cy="256" r="140" fill="none" stroke="#333355" stroke-width="1.5"/>

  <!-- Outer Hexagonal Shroud -->
  <polygon points="256,90 395,170 395,330 256,410 117,330 117,170" 
           fill="none" stroke="url(#neonCyan)" stroke-width="10" stroke-linejoin="round" filter="url(#neonBlur)"/>

  <!-- Inner Diamond Core (The NAIVE Iris) -->
  <polygon points="256,130 366,256 256,382 146,256" 
           fill="#10101c" fill-opacity="0.9" stroke="#00F0FF" stroke-width="5" stroke-linejoin="round"/>

  <!-- The Blinking Eye / Neural Core -->
  <circle cx="256" cy="256" r="48" fill="url(#coreGlow)" filter="url(#neonBlur)"/>
  <circle cx="256" cy="256" r="22" fill="#0A0A14"/>
  <circle cx="264" cy="248" r="8" fill="#FFFFFF"/>

  <!-- Accent Nodes -->
  <circle cx="256" cy="90" r="8" fill="#00F0FF"/>
  <circle cx="395" cy="170" r="8" fill="#7000FF"/>
  <circle cx="395" cy="330" r="8" fill="#FF007A"/>
  <circle cx="256" cy="410" r="8" fill="#00F0FF"/>
  <circle cx="117" cy="330" r="8" fill="#7000FF"/>
  <circle cx="117" cy="170" r="8" fill="#FF007A"/>
</svg>'''
    svg_path = assets_dir / "logo.svg"
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"Created {svg_path}")

def render_bitmaps(assets_dir: Path):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    size = 512
    img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)

    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)

    # 1. Background Rounded Tile
    bg_grad = QRadialGradient(256, 256, 256)
    bg_grad.setColorAt(0.0, QColor("#1e1b4b"))
    bg_grad.setColorAt(0.7, QColor("#11111e"))
    bg_grad.setColorAt(1.0, QColor("#09090f"))
    p.setBrush(QBrush(bg_grad))
    p.setPen(QPen(QColor("#2d2d48"), 4))
    p.drawRoundedRect(QRectF(16, 16, 480, 480), 96, 96)

    # 2. Orbital Cyber Rings
    p.setBrush(Qt.NoBrush)
    ring_pen = QPen(QColor(80, 80, 130, 120), 2, Qt.DashLine)
    p.setPen(ring_pen)
    p.drawEllipse(QPointF(256, 256), 180, 180)
    p.setPen(QPen(QColor(100, 100, 160, 80), 1.5))
    p.drawEllipse(QPointF(256, 256), 140, 140)

    # 3. Outer Hexagon
    hex_path = QPainterPath()
    hex_points = [
        QPointF(256, 96),
        QPointF(395, 176),
        QPointF(395, 336),
        QPointF(256, 416),
        QPointF(117, 336),
        QPointF(117, 176)
    ]
    hex_path.moveTo(hex_points[0])
    for pt in hex_points[1:]:
        hex_path.lineTo(pt)
    hex_path.closeSubpath()

    hex_grad = QLinearGradient(117, 96, 395, 416)
    hex_grad.setColorAt(0.0, QColor("#00F0FF"))
    hex_grad.setColorAt(0.5, QColor("#8A2BE2"))
    hex_grad.setColorAt(1.0, QColor("#FF007A"))

    # Outer Hex Glow
    glow_pen = QPen(QColor(0, 240, 255, 60), 22)
    p.setPen(glow_pen)
    p.drawPath(hex_path)

    p.setPen(QPen(QBrush(hex_grad), 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPath(hex_path)

    # 4. Inner Diamond Core
    diamond_path = QPainterPath()
    diamond_path.moveTo(256, 135)
    diamond_path.lineTo(365, 256)
    diamond_path.lineTo(256, 377)
    diamond_path.lineTo(147, 256)
    diamond_path.closeSubpath()

    p.setBrush(QColor(16, 16, 28, 230))
    p.setPen(QPen(QColor("#00F0FF"), 5))
    p.drawPath(diamond_path)

    # 5. Core Blinking Iris
    iris_grad = QRadialGradient(256, 256, 52)
    iris_grad.setColorAt(0.0, QColor("#FFFFFF"))
    iris_grad.setColorAt(0.5, QColor("#00F0FF"))
    iris_grad.setColorAt(1.0, QColor("#7000FF"))

    # Iris Glow
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 240, 255, 100))
    p.drawEllipse(QPointF(256, 256), 64, 64)

    p.setBrush(QBrush(iris_grad))
    p.drawEllipse(QPointF(256, 256), 46, 46)

    # Pupil
    p.setBrush(QColor("#0A0A14"))
    p.drawEllipse(QPointF(256, 256), 22, 22)

    # Glint
    p.setBrush(QColor("#FFFFFF"))
    p.drawEllipse(QPointF(265, 247), 8, 8)

    # 6. Nodes on Hexagon
    node_colors = [
        QColor("#00F0FF"), QColor("#8A2BE2"), QColor("#FF007A"),
        QColor("#00F0FF"), QColor("#8A2BE2"), QColor("#FF007A")
    ]
    for pt, col in zip(hex_points, node_colors):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawEllipse(pt, 9, 9)
        p.setBrush(col)
        p.drawEllipse(pt, 6, 6)

    p.end()

    png_path = assets_dir / "logo.png"
    img.save(str(png_path), "PNG")
    print(f"Created {png_path} ({size}x{size})")

    # Generate multi-resolution ICO (256, 128, 64, 48, 32, 16)
    sizes = [256, 128, 64, 48, 32, 16]
    png_buffers = []
    for s in sizes:
        scaled = img.scaled(s, s, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        scaled.save(buf, "PNG")
        png_data = bytes(buf.data())
        buf.close()
        png_buffers.append((s, png_data))

    # Build ICO file binary
    ico_path = assets_dir / "icon.ico"
    with open(ico_path, "wb") as f:
        # Header: Reserved (2), Type=1 (2), Count (2)
        f.write(struct.pack("<HHH", 0, 1, len(png_buffers)))
        
        offset = 6 + (16 * len(png_buffers))
        entries = []
        for s, data in png_buffers:
            width_byte = 0 if s == 256 else s
            height_byte = 0 if s == 256 else s
            length = len(data)
            # Entry: Width(1), Height(1), Colors(1), Reserved(1), Planes(2), BPP(2), Bytes(4), Offset(4)
            entries.append((width_byte, height_byte, 0, 0, 1, 32, length, offset))
            offset += length

        for entry in entries:
            f.write(struct.pack("<BBBBHHII", *entry))

        for _, data in png_buffers:
            f.write(data)

    print(f"Created {ico_path} with sizes: {sizes}")

if __name__ == "__main__":
    assets = Path("assets")
    assets.mkdir(parents=True, exist_ok=True)
    create_svg(assets)
    render_bitmaps(assets)
