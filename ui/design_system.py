"""
PRUBETH IDE — Design System Governance (Pillar 4)
Single source of truth for visual design tokens, typography, component styles,
and visual regression standards across the entire application.
Enforces the Obsidian Slate aesthetic (#0B0D13, #141824, #00F0FF) consistently.
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class DesignTokens:
    """Immutable design tokens defining the visual language of PRUBETH IDE."""

    # Color Palette — Obsidian Slate & Electric Cyan
    CANVAS_BG: str = "#0B0D13"
    SURFACE_PANEL: str = "#141824"
    SURFACE_ELEVATED: str = "#161722"
    SURFACE_HOVER: str = "#1F2233"
    
    BORDER_SUBTLE: str = "#1E202C"
    BORDER_FOCUS: str = "#00F0FF"
    BORDER_MUTED: str = "#282A3A"

    TEXT_PRIMARY: str = "#FFFFFF"
    TEXT_SECONDARY: str = "#E0E0E0"
    TEXT_MUTED: str = "#8F93A2"
    TEXT_DISABLED: str = "#555A68"

    ACCENT_CYAN: str = "#00F0FF"
    ACCENT_CYAN_HOVER: str = "#33F3FF"
    SUCCESS_GREEN: str = "#00FF88"
    WARNING_AMBER: str = "#FFCC00"
    DANGER_RED: str = "#FF4466"
    INFO_PURPLE: str = "#D946EF"

    # Typography
    FONT_FAMILY_UI: str = "'Segoe UI', 'Inter', -apple-system, sans-serif"
    FONT_FAMILY_MONO: str = "'Cascadia Code', 'Consolas', 'Courier New', monospace"
    FONT_SIZE_XS: str = "10px"
    FONT_SIZE_SM: str = "11px"
    FONT_SIZE_BASE: str = "12px"
    FONT_SIZE_MD: str = "13px"
    FONT_SIZE_LG: str = "15px"
    FONT_SIZE_XL: str = "18px"

    # Corner Radii
    RADIUS_SM: str = "4px"
    RADIUS_MD: str = "6px"
    RADIUS_LG: str = "8px"


class ComponentStyles:
    """Pre-compiled Qt stylesheets enforcing design system components."""

    @staticmethod
    def primary_button() -> str:
        t = DesignTokens
        return f"""
            QPushButton {{
                background-color: {t.ACCENT_CYAN};
                color: {t.CANVAS_BG};
                border: none;
                border-radius: {t.RADIUS_SM};
                padding: 6px 14px;
                font-weight: bold;
                font-size: {t.FONT_SIZE_BASE};
                font-family: {t.FONT_FAMILY_UI};
            }}
            QPushButton:hover {{
                background-color: {t.ACCENT_CYAN_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #00B4CC;
            }}
        """

    @staticmethod
    def secondary_button() -> str:
        t = DesignTokens
        return f"""
            QPushButton {{
                background-color: {t.SURFACE_ELEVATED};
                color: {t.TEXT_PRIMARY};
                border: 1px solid {t.BORDER_MUTED};
                border-radius: {t.RADIUS_SM};
                padding: 6px 12px;
                font-size: {t.FONT_SIZE_BASE};
                font-family: {t.FONT_FAMILY_UI};
            }}
            QPushButton:hover {{
                background-color: {t.SURFACE_HOVER};
                border-color: {t.ACCENT_CYAN};
                color: {t.ACCENT_CYAN};
            }}
        """

    @staticmethod
    def danger_button() -> str:
        t = DesignTokens
        return f"""
            QPushButton {{
                background-color: #331A20;
                color: {t.DANGER_RED};
                border: 1px solid #55222E;
                border-radius: {t.RADIUS_SM};
                padding: 4px 10px;
                font-size: {t.FONT_SIZE_SM};
                font-family: {t.FONT_FAMILY_UI};
            }}
            QPushButton:hover {{
                background-color: {t.DANGER_RED};
                color: {t.TEXT_PRIMARY};
            }}
        """

    @staticmethod
    def card_frame() -> str:
        t = DesignTokens
        return f"""
            QFrame {{
                background-color: {t.SURFACE_PANEL};
                border: 1px solid {t.BORDER_SUBTLE};
                border-radius: {t.RADIUS_MD};
                padding: 8px;
            }}
        """

    @staticmethod
    def input_field() -> str:
        t = DesignTokens
        return f"""
            QLineEdit, QTextEdit {{
                background-color: {t.SURFACE_ELEVATED};
                color: {t.TEXT_PRIMARY};
                border: 1px solid {t.BORDER_MUTED};
                border-radius: {t.RADIUS_SM};
                padding: 6px;
                font-size: {t.FONT_SIZE_BASE};
                font-family: {t.FONT_FAMILY_UI};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {t.BORDER_FOCUS};
            }}
        """

    @staticmethod
    def table_view() -> str:
        t = DesignTokens
        return f"""
            QTableWidget {{
                background-color: {t.CANVAS_BG};
                gridline-color: {t.BORDER_SUBTLE};
                color: {t.TEXT_PRIMARY};
                border: 1px solid {t.BORDER_SUBTLE};
                border-radius: {t.RADIUS_SM};
            }}
            QHeaderView::section {{
                background-color: {t.SURFACE_ELEVATED};
                color: {t.TEXT_MUTED};
                border: 1px solid {t.BORDER_SUBTLE};
                padding: 6px;
                font-weight: bold;
                font-size: {t.FONT_SIZE_SM};
            }}
            QTableWidget::item:selected {{
                background-color: {t.SURFACE_HOVER};
                color: {t.ACCENT_CYAN};
            }}
        """
