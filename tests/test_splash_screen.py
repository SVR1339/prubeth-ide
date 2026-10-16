"""
PRUBETH IDE — Splash Screen & Loading Page Verification Tests
=============================================================
Tests the visual rendering, fallback generation, dynamic progress bar,
status messaging, and headless safety of PrubethSplashScreen.
"""

import os
import pytest

# Ensure offscreen Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPaintEvent
from PyQt5.QtCore import QRect

from core.splash_screen import PrubethSplashScreen


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_splash_screen_initialization(qapp):
    splash = PrubethSplashScreen(target_width=640, target_height=426)
    assert splash.target_width == 640
    assert splash.target_height == 426
    assert splash.width() == 640
    assert splash.height() == 426
    assert splash.progress_value == 0
    assert "INITIALIZING" in splash.status_message


def test_splash_screen_fallback_pixmap(qapp):
    # Pass a non-existent file to test procedural fallback
    splash = PrubethSplashScreen(image_path="non_existent_splash_artwork_xyz.png")
    assert splash.pixmap() is not None
    assert not splash.pixmap().isNull()


def test_splash_screen_progress_and_status(qapp):
    splash = PrubethSplashScreen()

    splash.set_progress(45, "Loading Language Server Protocol...")
    assert splash.progress_value == 45
    assert splash.status_message == "LOADING LANGUAGE SERVER PROTOCOL..."

    # Test clamping
    splash.set_progress(120)
    assert splash.progress_value == 100

    splash.set_progress(-15)
    assert splash.progress_value == 0


def test_splash_screen_startup_sequence_headless(qapp):
    splash = PrubethSplashScreen()
    completed = []

    def on_complete():
        completed.append(True)

    # In headless/CI mode, startup sequence dispatches immediately
    splash.run_startup_sequence(on_complete, fast_mode=True)
    assert len(completed) == 1
    assert splash.progress_value == 100
    assert "PRUBETH IDE READY" in splash.status_message


def test_splash_screen_paint_event_safety(qapp):
    splash = PrubethSplashScreen()
    splash.set_progress(60, "Rendering Test Stage")

    # Invoke paint event directly to verify QPainter logic
    event = QPaintEvent(QRect(0, 0, splash.width(), splash.height()))
    splash.paintEvent(event)
