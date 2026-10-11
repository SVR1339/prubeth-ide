import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter, QFont, QColor
from PyQt5.QtCore import Qt

# Initialize headless Qt App for font rendering
app = QApplication.instance()
if not app:
    app = QApplication([sys.argv[0], "-platform", "offscreen"])

logo_path = Path("assets/logo.png")
if not logo_path.exists():
    print("[!] logo.png not found")
    sys.exit(1)

logo_img = QImage(str(logo_path))

# 1. Create Transparent Dark-Friendly Banner (1024 x 320)
banner = QImage(1024, 320, QImage.Format_ARGB32)
banner.fill(QColor(0, 0, 0, 0))

p = QPainter(banner)
p.setRenderHint(QPainter.Antialiasing)
p.setRenderHint(QPainter.TextAntialiasing)
p.setRenderHint(QPainter.SmoothPixmapTransform)

# Draw flower emblem on the left
flower_size = 230
scaled_flower = logo_img.scaled(flower_size, flower_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
p.drawImage(50, (320 - flower_size) // 2, scaled_flower)

# Text: PRUBETH IDE
f_title = QFont("Segoe UI", 42, QFont.Bold)
p.setFont(f_title)
p.setPen(QColor("#FFFFFF"))
p.drawText(330, 155, "PRUBETH IDE")

# Subtitle: Bloom, ideas unfolding
f_sub = QFont("Segoe UI", 18, QFont.Normal)
p.setFont(f_sub)
p.setPen(QColor("#A5ACBB"))
p.drawText(335, 205, "Bloom, ideas unfolding")

p.end()

out_p = Path("assets/brand_banner.png")
banner.save(str(out_p), "PNG")
print(f"[+] Successfully generated: {out_p} ({banner.width()}x{banner.height()})")

# 2. Also save JPG with #15171D background for universal renderers
banner_jpg = QImage(1024, 320, QImage.Format_RGB32)
banner_jpg.fill(QColor("#15171D"))
p_jpg = QPainter(banner_jpg)
p_jpg.drawImage(0, 0, banner)
p_jpg.end()
out_jpg = Path("assets/brand_banner.jpg")
banner_jpg.save(str(out_jpg), "JPEG", 95)
print(f"[+] Successfully generated: {out_jpg} ({banner_jpg.width()}x{banner_jpg.height()})")
