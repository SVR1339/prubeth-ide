"""
Unit tests for ui/design_system.py (Pillars 4 & 6: Design System & Quality Engineering)
Verifies immutability, color token format, and CSS stylesheet compilation.
"""
import re
import pytest
from dataclasses import FrozenInstanceError
from ui.design_system import DesignTokens, ComponentStyles


def test_design_tokens_immutability():
    """Verify that DesignTokens is frozen and cannot be mutated at runtime."""
    tokens = DesignTokens()
    with pytest.raises((FrozenInstanceError, AttributeError)):
        tokens.CANVAS_BG = "#000000"


def test_design_tokens_color_formats():
    """Verify that all color tokens follow valid 7-character hex format (#RRGGBB)."""
    hex_pattern = re.compile(r"^#[0-9a-fA-F]{6}$")
    color_attributes = [
        "CANVAS_BG", "SURFACE_PANEL", "SURFACE_ELEVATED", "SURFACE_HOVER",
        "BORDER_SUBTLE", "BORDER_FOCUS", "BORDER_MUTED",
        "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_MUTED", "TEXT_DISABLED",
        "ACCENT_CYAN", "ACCENT_CYAN_HOVER", "SUCCESS_GREEN", "WARNING_AMBER",
        "DANGER_RED", "INFO_PURPLE"
    ]
    for attr in color_attributes:
        val = getattr(DesignTokens, attr)
        assert hex_pattern.match(val), f"Token {attr}={val} does not match #RRGGBB format"


def test_design_tokens_typography_and_radii():
    """Verify typography and radius definitions exist and are properly structured."""
    assert "Segoe UI" in DesignTokens.FONT_FAMILY_UI
    assert "Cascadia Code" in DesignTokens.FONT_FAMILY_MONO
    assert DesignTokens.FONT_SIZE_BASE.endswith("px")
    assert DesignTokens.RADIUS_SM.endswith("px")


def test_component_styles_primary_button():
    """Verify primary button stylesheet contains accent cyan and canvas background."""
    style = ComponentStyles.primary_button()
    assert DesignTokens.ACCENT_CYAN in style
    assert DesignTokens.CANVAS_BG in style
    assert "QPushButton" in style


def test_component_styles_secondary_button():
    """Verify secondary button stylesheet contains surface and border styling."""
    style = ComponentStyles.secondary_button()
    assert DesignTokens.SURFACE_ELEVATED in style
    assert DesignTokens.TEXT_PRIMARY in style
    assert "QPushButton:hover" in style


def test_component_styles_danger_button():
    """Verify danger button stylesheet incorporates danger red."""
    style = ComponentStyles.danger_button()
    assert DesignTokens.DANGER_RED in style


def test_component_styles_card_frame():
    """Verify card frame stylesheet generates valid border and surface panel."""
    style = ComponentStyles.card_frame()
    assert DesignTokens.SURFACE_PANEL in style
    assert DesignTokens.BORDER_SUBTLE in style


def test_component_styles_input_field():
    """Verify input field stylesheet styles QLineEdit and QTextEdit with focus."""
    style = ComponentStyles.input_field()
    assert "QLineEdit" in style
    assert "QTextEdit" in style
    assert DesignTokens.BORDER_FOCUS in style


def test_component_styles_table_view():
    """Verify table view stylesheet styles QTableWidget and QHeaderView."""
    style = ComponentStyles.table_view()
    assert "QTableWidget" in style
    assert "QHeaderView::section" in style
    assert DesignTokens.CANVAS_BG in style
