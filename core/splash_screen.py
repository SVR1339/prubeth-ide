"""
PRUBETH IDE — Loading Screen & Splash Engine
=============================================
Renders the high-fidelity PRUBETH IDE branded startup splash screen
with interactive progress feedback, dynamic subsystem initialization
telemetry, and automated headless detection.

Design Spec:
- 3D Blossom Motif with Cyan Energy Core
- Brand: PRUBETH IDE ("HIRE ROBOTS FOR USING NOT DECORATE !")
- Dynamic Gradient Progress Bar (Cyan -> Purple Gradient)
- Subsystem Initialization Telemetry
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtCore import QEventLoop, QPoint, QRect, QRectF, QSize, Qt, QTimer
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt5.QtWidgets import QApplication, QLabel, QProgressBar, QSplashScreen, QWidget

logger = logging.getLogger("prubeth.splash")


class PrubethSplashScreen(QSplashScreen):
    """
    Splash screen for PRUBETH IDE featuring high-res brand artwork,
    smooth progress interpolation, and graceful headless fallback.
    """

    DEFAULT_SPLASH_PATH = Path(__file__).resolve().parent.parent / "assets" / "splash_loading.png"
    FALLBACK_ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "prubeth_flower_icon.png"

    INITIALIZATION_STEPS = [
        (15, "INITIALIZING MATHEMATICAL RESILIENCE ENGINE..."),
        (35, "LOADING ERROR VAULT & ISO/IEC SAFE HARBORS..."),
        (55, "CONNECTING TO OPEN VSX EXTENSIONS REGISTRY..."),
        (75, "VERIFYING POLYGLOT TOOLCHAINS & LSP SERVERS..."),
        (90, "INITIALIZING WORKSPACE & AI AGENT GATEWAY..."),
        (100, "PRUBETH IDE READY — LAUNCHING STUDIO..."),
    ]

    def __init__(
        self,
        image_path: Optional[str] = None,
        target_width: int = 860,
        target_height: int = 573,
    ):
        self.target_width = target_width
        self.target_height = target_height
        self.progress_value = 0
        self.status_message = "INITIALIZING PRUBETH IDE..."

        # Coordinate scale factors based on canonical 1024x682 artwork
        self.scale_x = self.target_width / 1024.0
        self.scale_y = self.target_height / 682.0

        # Determine asset path
        chosen_path = Path(image_path) if image_path else self.DEFAULT_SPLASH_PATH
        self.pixmap_loaded = False

        if chosen_path.exists():
            base_pixmap = QPixmap(str(chosen_path))
            if not base_pixmap.isNull():
                self.scaled_pixmap = base_pixmap.scaled(
                    self.target_width,
                    self.target_height,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
                super().__init__(self.scaled_pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
                self.pixmap_loaded = True
            else:
                self.scaled_pixmap = self._create_fallback_pixmap()
                super().__init__(self.scaled_pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        else:
            self.scaled_pixmap = self._create_fallback_pixmap()
            super().__init__(self.scaled_pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        self.setFixedSize(self.target_width, self.target_height)
        self._center_on_screen()

    def _create_fallback_pixmap(self) -> QPixmap:
        """Procedurally paints an elegant fallback splash if assets are missing."""
        pix = QPixmap(self.target_width, self.target_height)
        pix.fill(QColor("#FFFFFF"))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)

        # Soft pastel ribbon
        path = QPainterPath()
        path.moveTo(0, self.target_height * 0.7)
        path.cubicTo(
            self.target_width * 0.3,
            self.target_height * 0.55,
            self.target_width * 0.7,
            self.target_height * 0.85,
            self.target_width,
            self.target_height * 0.7,
        )
        path.lineTo(self.target_width, self.target_height)
        path.lineTo(0, self.target_height)
        path.closeSubpath()

        ribbon_grad = QLinearGradient(0, self.target_height * 0.5, self.target_width, self.target_height)
        ribbon_grad.setColorAt(0.0, QColor(0, 229, 255, 35))
        ribbon_grad.setColorAt(0.5, QColor(124, 77, 255, 30))
        ribbon_grad.setColorAt(1.0, QColor(255, 171, 145, 45))
        painter.fillPath(path, ribbon_grad)

        # Title
        painter.setPen(QColor("#0F172A"))
        title_font = QFont("Segoe UI", 26, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(
            QRect(0, int(self.target_height * 0.38), self.target_width, 50),
            Qt.AlignCenter,
            "PRUBETH IDE",
        )

        # Slogan
        painter.setPen(QColor("#334155"))
        slogan_font = QFont("Segoe UI", 11, QFont.DemiBold)
        slogan_font.setLetterSpacing(QFont.AbsoluteSpacing, 1.5)
        painter.setFont(slogan_font)
        painter.drawText(
            QRect(0, int(self.target_height * 0.46), self.target_width, 30),
            Qt.AlignCenter,
            "HIRE ROBOTS FOR USING NOT DECORATE !",
        )

        painter.end()
        return pix

    def _center_on_screen(self):
        """Centers the splash screen on the current active desktop."""
        try:
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    geo = screen.geometry()
                    x = (geo.width() - self.target_width) // 2
                    y = (geo.height() - self.target_height) // 2
                    self.move(x, y)
        except Exception:
            pass

    def set_progress(self, percent: int, message: Optional[str] = None):
        """
        Updates the progress percentage (0 - 100) and displays the current
        subsystem initialization status string.
        """
        self.progress_value = max(0, min(100, int(percent)))
        if message:
            self.status_message = message.upper()
        self.update()
        app = QApplication.instance()
        if app:
            app.processEvents()

    def paintEvent(self, event):
        """
        Paints the dynamic progress bar with sub-millimeter precision over the artwork.
        """
        # First draw the base pixmap
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Pixel-perfect coordinates mapped from canonical 1024x682
        bar_x = int(341 * self.scale_x)
        bar_y = int(500 * self.scale_y)
        bar_width = int(341 * self.scale_x)
        bar_height = max(10, int(13 * self.scale_y))
        radius = bar_height / 2.0

        # 1. Background Pill Track (covers static initial bar in the image)
        track_rect = QRectF(bar_x, bar_y, bar_width, bar_height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#EEF0F2"))  # Clean soft gray track matching artwork
        painter.drawRoundedRect(track_rect, radius, radius)

        # 2. Filled Dynamic Gradient Bar
        if self.progress_value > 0:
            fill_width = max(radius * 2, (bar_width * self.progress_value) / 100.0)
            fill_rect = QRectF(bar_x, bar_y, fill_width, bar_height)

            grad = QLinearGradient(bar_x, bar_y, bar_x + bar_width, bar_y)
            grad.setColorAt(0.0, QColor("#00E5FF"))  # Electric Cyan
            grad.setColorAt(0.5, QColor("#7C4DFF"))  # Electric Purple
            grad.setColorAt(1.0, QColor("#A855F7"))  # Radiant Violet

            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(fill_rect, radius, radius)

        painter.end()

    def run_startup_sequence(self, on_complete: Callable[[], None], fast_mode: bool = False):
        """
        Executes the initialization step sequence. In headless/CI mode or fast_mode,
        it resolves instantly so tests and automated flows are never stalled.
        """
        is_headless = os.environ.get("QT_QPA_PLATFORM") == "offscreen" or fast_mode

        if is_headless:
            # Immediate dispatch for tests and headless environments
            for step_val, step_msg in self.INITIALIZATION_STEPS:
                self.progress_value = step_val
                self.status_message = step_msg
            on_complete()
            return

        # Interactive smooth progression for live desktop runs
        step_idx = 0

        def advance():
            nonlocal step_idx
            if step_idx < len(self.INITIALIZATION_STEPS):
                val, msg = self.INITIALIZATION_STEPS[step_idx]
                self.set_progress(val, msg)
                step_idx += 1
                # 130ms per step = ~800ms total smooth splash experience
                QTimer.singleShot(130, advance)
            else:
                # Brief pause at 100% then finish
                QTimer.singleShot(90, on_complete)

        advance()
