"""
SUKHI / PRUBETH IDE — Design System Governance (Theme & Design Tokens Engine)
Single source of truth for visual design tokens, typography, component styles,
color palettes, syntax highlighting, and theme variants across the entire workstation.

Enforces the Premium Dark Developer-Workstation aesthetic:
- App Background:       #15171D
- Panel Background:     #1D2028
- Elevated Surface:     #252934
- Border:               #343A49
- Primary Accent:       #9485FF
- Secondary Accent:     #62D4E5
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class DesignTokens:
    """Authoritative design tokens defining the visual language of the IDE."""

    # Core Palette
    app_background: str = "#15171D"
    panel_background: str = "#1D2028"
    elevated_surface: str = "#252934"
    border: str = "#343A49"
    input_background: str = "#191C23"
    terminal_background: str = "#111318"

    # Accents & Semantics
    primary_accent: str = "#9485FF"
    secondary_accent: str = "#62D4E5"
    success: str = "#70D6A0"
    warning: str = "#FFBF69"
    error: str = "#FF7D86"

    # Typography & Foreground
    text_primary: str = "#E8EAF0"
    text_secondary: str = "#A5ACBB"
    text_disabled: str = "#737B8C"

    # Focus & Selection
    editor_selection: str = "#383650"
    focus_outline: str = "#B4A9FF"

    # Code Editor Syntax Tokens
    syntax_keywords: str = "#C4A1FF"
    syntax_strings: str = "#9DD9A8"
    syntax_functions: str = "#83BDF5"
    syntax_comments: str = "#8995A7"
    syntax_numbers: str = "#F1C27D"
    syntax_errors: str = "#FF7D86"
    syntax_line_numbers: str = "#727B8D"

    # Typography Families & Scales
    font_family_ui: str = "'Segoe UI', 'Inter', -apple-system, sans-serif"
    font_family_mono: str = "'Cascadia Code', 'Consolas', 'Courier New', monospace"
    font_size_xs: str = "10px"
    font_size_sm: str = "11px"
    font_size_base: str = "12px"
    font_size_md: str = "13px"
    font_size_lg: str = "15px"
    font_size_xl: str = "18px"

    # Corner Radii
    radius_sm: str = "4px"
    radius_md: str = "6px"
    radius_lg: str = "8px"

    # Backwards-compatible string attributes for legacy callers & test suite
    CANVAS_BG: str = "#15171D"
    SURFACE_PANEL: str = "#1D2028"
    SURFACE_ELEVATED: str = "#252934"
    SURFACE_HOVER: str = "#2C313E"

    BORDER_SUBTLE: str = "#343A49"
    BORDER_FOCUS: str = "#B4A9FF"
    BORDER_MUTED: str = "#3D4455"

    TEXT_PRIMARY: str = "#E8EAF0"
    TEXT_SECONDARY: str = "#A5ACBB"
    TEXT_MUTED: str = "#A5ACBB"
    TEXT_DISABLED: str = "#737B8C"

    ACCENT_CYAN: str = "#62D4E5"
    ACCENT_CYAN_HOVER: str = "#7FE0EE"
    SUCCESS_GREEN: str = "#70D6A0"
    WARNING_AMBER: str = "#FFBF69"
    DANGER_RED: str = "#FF7D86"
    INFO_PURPLE: str = "#9485FF"

    FONT_FAMILY_UI: str = "'Segoe UI', 'Inter', -apple-system, sans-serif"
    FONT_FAMILY_MONO: str = "'Cascadia Code', 'Consolas', 'Courier New', monospace"
    FONT_SIZE_XS: str = "10px"
    FONT_SIZE_SM: str = "11px"
    FONT_SIZE_BASE: str = "12px"
    FONT_SIZE_MD: str = "13px"
    FONT_SIZE_LG: str = "15px"
    FONT_SIZE_XL: str = "18px"

    RADIUS_SM: str = "4px"
    RADIUS_MD: str = "6px"
    RADIUS_LG: str = "8px"


# Global Default Tokens Instance
DEFAULT_TOKENS = DesignTokens()


# Theme Variant Definitions
THEMES: Dict[str, DesignTokens] = {
    "dark": DEFAULT_TOKENS,
    "light": DesignTokens(
        app_background="#F4F6F9",
        panel_background="#FFFFFF",
        elevated_surface="#E8ECF2",
        border="#D1D7E0",
        input_background="#FFFFFF",
        terminal_background="#1A1D24",
        primary_accent="#7C3AED",
        secondary_accent="#0284C7",
        success="#10B981",
        warning="#F59E0B",
        error="#EF4444",
        text_primary="#1E293B",
        text_secondary="#475569",
        text_disabled="#94A3B8",
        editor_selection="#DDD6FE",
        focus_outline="#7C3AED",
        syntax_keywords="#7C3AED",
        syntax_strings="#059669",
        syntax_functions="#2563EB",
        syntax_comments="#64748B",
        syntax_numbers="#D97706",
        syntax_errors="#DC2626",
        syntax_line_numbers="#94A3B8",
    ),
    "high_contrast": DesignTokens(
        app_background="#000000",
        panel_background="#0A0A0A",
        elevated_surface="#141414",
        border="#FFFFFF",
        input_background="#000000",
        terminal_background="#000000",
        primary_accent="#00FFFF",
        secondary_accent="#FFFF00",
        success="#00FF00",
        warning="#FFA500",
        error="#FF0000",
        text_primary="#FFFFFF",
        text_secondary="#DDDDDD",
        text_disabled="#888888",
        editor_selection="#003366",
        focus_outline="#FFFF00",
        syntax_keywords="#FF00FF",
        syntax_strings="#00FF00",
        syntax_functions="#00FFFF",
        syntax_comments="#AAAAAA",
        syntax_numbers="#FFFF00",
        syntax_errors="#FF0000",
        syntax_line_numbers="#CCCCCC",
    ),
}


def get_theme(name: str = "dark", custom_accent: Optional[str] = None) -> DesignTokens:
    """Returns the DesignTokens for a requested theme, optionally applying a custom accent."""
    base = THEMES.get(name.lower(), DEFAULT_TOKENS)
    if custom_accent:
        return DesignTokens(
            app_background=base.app_background,
            panel_background=base.panel_background,
            elevated_surface=base.elevated_surface,
            border=base.border,
            input_background=base.input_background,
            terminal_background=base.terminal_background,
            primary_accent=custom_accent,
            secondary_accent=base.secondary_accent,
            success=base.success,
            warning=base.warning,
            error=base.error,
            text_primary=base.text_primary,
            text_secondary=base.text_secondary,
            text_disabled=base.text_disabled,
            editor_selection=base.editor_selection,
            focus_outline=custom_accent,
            syntax_keywords=custom_accent,
            syntax_strings=base.syntax_strings,
            syntax_functions=base.syntax_functions,
            syntax_comments=base.syntax_comments,
            syntax_numbers=base.syntax_numbers,
            syntax_errors=base.syntax_errors,
            syntax_line_numbers=base.syntax_line_numbers,
        )
    return base


def get_application_stylesheet(theme_name: str = "dark", custom_accent: Optional[str] = None) -> str:
    """Generates the unified, professional Qt stylesheet for the entire application."""
    t = get_theme(theme_name, custom_accent)
    return f"""
        /* === CORE APPLICATION CANVAS === */
        QMainWindow, QWidget {{
            background-color: {t.app_background};
            color: {t.text_primary};
            font-family: {t.font_family_ui};
            font-size: 10pt;
        }}

        /* === TOP MENUS & TOOLBARS === */
        QMenuBar {{
            background-color: {t.panel_background};
            color: {t.text_primary};
            border-bottom: 1px solid {t.border};
            padding: 2px 6px;
        }}
        QMenuBar::item {{
            padding: 6px 10px;
            border-radius: {t.radius_sm};
            background: transparent;
        }}
        QMenuBar::item:selected {{
            background-color: {t.elevated_surface};
            color: {t.primary_accent};
        }}

        QMenu {{
            background-color: {t.panel_background};
            color: {t.text_primary};
            border: 1px solid {t.border};
            padding: 4px;
            border-radius: {t.radius_md};
        }}
        QMenu::item {{
            padding: 6px 24px 6px 12px;
            border-radius: {t.radius_sm};
        }}
        QMenu::item:selected {{
            background-color: {t.elevated_surface};
            color: {t.primary_accent};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {t.border};
            margin: 4px 6px;
        }}

        QToolBar {{
            background-color: {t.panel_background};
            border-bottom: 1px solid {t.border};
            padding: 4px 8px;
            spacing: 6px;
        }}
        QToolButton {{
            background-color: {t.elevated_surface};
            color: {t.text_primary};
            border: 1px solid {t.border};
            padding: 5px 12px;
            border-radius: {t.radius_sm};
            font-weight: 600;
        }}
        QToolButton:hover {{
            background-color: {t.border};
            border-color: {t.primary_accent};
            color: {t.primary_accent};
        }}
        QToolButton:pressed {{
            background-color: {t.input_background};
        }}

        /* === PANELS, TABS & TREE VIEWS === */
        QTabWidget::pane {{
            border: 1px solid {t.border};
            background-color: {t.panel_background};
            border-radius: {t.radius_sm};
        }}
        QTabBar::tab {{
            background-color: {t.app_background};
            color: {t.text_secondary};
            border: 1px solid {t.border};
            border-bottom: none;
            padding: 6px 12px;
            margin-right: 2px;
            border-top-left-radius: {t.radius_sm};
            border-top-right-radius: {t.radius_sm};
            font-weight: 500;
        }}
        QTabBar::tab:selected {{
            background-color: {t.panel_background};
            color: {t.text_primary};
            border-bottom: 2px solid {t.primary_accent};
            font-weight: 600;
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {t.elevated_surface};
            color: {t.text_primary};
        }}

        QTreeView, QListView, QTableView {{
            background-color: {t.panel_background};
            color: {t.text_primary};
            border: 1px solid {t.border};
            border-radius: {t.radius_sm};
            selection-background-color: {t.editor_selection};
            selection-color: {t.text_primary};
            outline: none;
        }}
        QTreeView::item {{
            padding: 4px;
            border-radius: {t.radius_sm};
        }}
        QTreeView::item:hover {{
            background-color: {t.elevated_surface};
        }}
        QTreeView::item:selected {{
            background-color: {t.editor_selection};
            color: #FFFFFF;
        }}
        QHeaderView::section {{
            background-color: {t.elevated_surface};
            color: {t.text_secondary};
            border: 1px solid {t.border};
            padding: 6px;
            font-weight: 600;
            font-size: {t.font_size_sm};
        }}

        /* === BUTTONS & CONTROLS === */
        QPushButton {{
            background-color: {t.elevated_surface};
            color: {t.text_primary};
            border: 1px solid {t.border};
            padding: 6px 16px;
            border-radius: {t.radius_sm};
            font-weight: 600;
            font-size: {t.font_size_base};
        }}
        QPushButton:hover {{
            background-color: {t.border};
            border-color: {t.primary_accent};
            color: {t.primary_accent};
        }}
        QPushButton:pressed {{
            background-color: {t.input_background};
        }}
        QPushButton:disabled {{
            background-color: {t.app_background};
            color: {t.text_disabled};
            border-color: {t.border};
        }}

        /* === INPUTS & COMBOBOXES === */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {t.input_background};
            color: {t.text_primary};
            border: 1px solid {t.border};
            padding: 6px 10px;
            border-radius: {t.radius_sm};
            selection-background-color: {t.editor_selection};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {t.focus_outline};
        }}
        QLineEdit:disabled, QTextEdit:disabled {{
            color: {t.text_disabled};
            background-color: {t.app_background};
        }}

        QComboBox {{
            background-color: {t.input_background};
            color: {t.text_primary};
            border: 1px solid {t.border};
            padding: 5px 12px;
            border-radius: {t.radius_sm};
            min-width: 6em;
        }}
        QComboBox:hover {{
            border-color: {t.primary_accent};
        }}
        QComboBox:focus {{
            border-color: {t.focus_outline};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {t.panel_background};
            color: {t.text_primary};
            border: 1px solid {t.border};
            selection-background-color: {t.elevated_surface};
            selection-color: {t.primary_accent};
            outline: none;
        }}

        /* === CHECKBOXES & RADIO BUTTONS === */
        QCheckBox, QRadioButton {{
            color: {t.text_primary};
            spacing: 8px;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {t.border};
            background-color: {t.input_background};
            border-radius: 3px;
        }}
        QRadioButton::indicator {{
            border-radius: 8px;
        }}
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border-color: {t.primary_accent};
        }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {t.primary_accent};
            border-color: {t.primary_accent};
        }}

        /* === SCROLLBARS (Ultra-Sleek Modern Track) === */
        QScrollBar:vertical {{
            background: {t.app_background};
            width: 10px;
            margin: 0;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {t.border};
            min-height: 24px;
            border-radius: 5px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t.text_disabled};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {t.app_background};
            height: 10px;
            margin: 0;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: {t.border};
            min-width: 24px;
            border-radius: 5px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {t.text_disabled};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* === PROGRESS BARS === */
        QProgressBar {{
            background-color: {t.input_background};
            border: 1px solid {t.border};
            border-radius: {t.radius_sm};
            text-align: center;
            color: {t.text_primary};
            font-size: {t.font_size_xs};
            font-weight: bold;
            height: 16px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t.primary_accent}, stop:1 {t.secondary_accent});
            border-radius: 3px;
        }}

        /* === STATUS BAR & SPLITTERS === */
        QStatusBar {{
            background-color: {t.panel_background};
            color: {t.text_secondary};
            border-top: 1px solid {t.border};
            font-size: {t.font_size_sm};
        }}
        QSplitter::handle {{
            background-color: {t.border};
        }}
        QSplitter::handle:hover {{
            background-color: {t.primary_accent};
        }}

        /* === GROUP BOXES & FRAMES === */
        QGroupBox {{
            border: 1px solid {t.border};
            border-radius: {t.radius_md};
            margin-top: 12px;
            padding-top: 12px;
            font-weight: 600;
            color: {t.text_primary};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 4px;
            color: {t.primary_accent};
        }}

        /* === TOOLTIPS === */
        QToolTip {{
            background-color: {t.elevated_surface};
            color: {t.text_primary};
            border: 1px solid {t.border};
            padding: 4px 8px;
            border-radius: {t.radius_sm};
            font-size: {t.font_size_xs};
        }}

        /* === WIZARD & DIALOGS === */
        QDialog, QWizard {{
            background-color: {t.app_background};
            color: {t.text_primary};
        }}
        QWizardPage {{
            background-color: {t.app_background};
            color: {t.text_primary};
        }}
    """


class ComponentStyles:
    """Pre-compiled Qt stylesheets enforcing design system components."""

    @staticmethod
    def primary_button(custom_accent: Optional[str] = None) -> str:
        t = get_theme(custom_accent=custom_accent)
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
        t = DEFAULT_TOKENS
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
        t = DEFAULT_TOKENS
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
    def success_button() -> str:
        t = DEFAULT_TOKENS
        return f"""
            QPushButton {{
                background-color: #1A3828;
                color: {t.SUCCESS_GREEN};
                border: 1px solid #285A3E;
                border-radius: {t.RADIUS_SM};
                padding: 5px 12px;
                font-size: {t.FONT_SIZE_SM};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {t.SUCCESS_GREEN};
                color: #0F171D;
            }}
        """

    @staticmethod
    def card_frame() -> str:
        t = DEFAULT_TOKENS
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
        t = DEFAULT_TOKENS
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
        t = DEFAULT_TOKENS
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
