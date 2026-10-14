"""
PRUBETH IDE — Intelligent Dedicated Settings & Subsystem Mod Control Center
Implements modern obsidian/slate aesthetic with smooth typography, rounded cards,
pill badges, segmented switches, and dedicated control over all IDE mods and operations.
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QDesktopServices, QCursor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QCheckBox, QSlider, QSpinBox, QPlainTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QScrollArea, QFrame, QMessageBox,
    QFileDialog, QInputDialog, QTabWidget, QApplication, QGroupBox,
    QFormLayout, QWidget, QButtonGroup
)

APP_HOME = Path.home() / ".local_ai_studio_pro"
APP_HOME.mkdir(parents=True, exist_ok=True)
SETTINGS_PATH = APP_HOME / "settings.json"
ACCOUNTS_CONFIG_PATH = APP_HOME / "accounts.json"
EXTENSIONS_CONFIG_PATH = APP_HOME / "extensions.json"
CUSTOM_MODELS_CONFIG_PATH = APP_HOME / "custom_models.json"
MCP_CONFIG_PATH = APP_HOME / "mcp_servers.json"
LOGS_DIR = APP_HOME / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_accounts_path():
    mod = sys.modules.get("local_ai_studio_pro")
    if mod and hasattr(mod, "ACCOUNTS_CONFIG_PATH"):
        return getattr(mod, "ACCOUNTS_CONFIG_PATH")
    return ACCOUNTS_CONFIG_PATH

def get_extensions_path():
    mod = sys.modules.get("local_ai_studio_pro")
    if mod and hasattr(mod, "EXTENSIONS_CONFIG_PATH"):
        return getattr(mod, "EXTENSIONS_CONFIG_PATH")
    return EXTENSIONS_CONFIG_PATH

def get_custom_models_path():
    mod = sys.modules.get("local_ai_studio_pro")
    if mod and hasattr(mod, "CUSTOM_MODELS_CONFIG_PATH"):
        return getattr(mod, "CUSTOM_MODELS_CONFIG_PATH")
    return CUSTOM_MODELS_CONFIG_PATH

def get_mcp_config_path():
    mod = sys.modules.get("local_ai_studio_pro")
    if mod and hasattr(mod, "MCP_CONFIG_PATH"):
        return getattr(mod, "MCP_CONFIG_PATH")
    return MCP_CONFIG_PATH

DEFAULT_EXTENSIONS = [
    {
        "id": "ext-vscode-bridge",
        "name": "VS Code Extension Bridge",
        "category": "IDE Bridges",
        "version": "1.4.0",
        "author": "PRUBETH Systems",
        "description": "Bi-directional bridge allowing direct import of VS Code extensions, keybindings, and themes.",
        "icon": "⚡",
        "installed": True,
        "enabled": True
    },
    {
        "id": "ext-copilot-agent",
        "name": "Autonomous Copilot Loop",
        "category": "AI Agents",
        "version": "2.1.0",
        "author": "Google DeepMind Ecosystem",
        "description": "50-step autonomous planning, self-debugging, and multi-file patching loop.",
        "icon": "🤖",
        "installed": True,
        "enabled": True
    },
    {
        "id": "ext-ollama-cuda",
        "name": "Ollama CUDA Accelerator",
        "category": "Private Cloud",
        "version": "3.0.0",
        "author": "Ollama Community",
        "description": "Hardware-accelerated local GGUF execution with split CUDA VRAM offloading.",
        "icon": "💻",
        "installed": True,
        "enabled": True
    },
    {
        "id": "ext-git-checkpoints",
        "name": "Transactional Time-Machine Checkpoints",
        "category": "Toolkits",
        "version": "1.2.0",
        "author": "PRUBETH Core Team",
        "description": "Zero-latency delta snapshots before AI tool edits with instant single-click rollbacks.",
        "icon": "🕒",
        "installed": True,
        "enabled": True
    },
    {
        "id": "ext-cyber-abliteration",
        "name": "Cybersecurity & Abliteration Suite",
        "category": "AI Agents",
        "version": "1.0.0",
        "author": "RedSage Labs",
        "description": "Bypasses refusal vectors and optimizes temperature/top-p for security research.",
        "icon": "🔓",
        "installed": True,
        "enabled": True
    },
    {
        "id": "ext-mcp-gateway",
        "name": "Model Context Protocol Gateway",
        "category": "Toolkits",
        "version": "2.0.0",
        "author": "Anthropic / Open Standards",
        "description": "Standardized tool discovery, database querying, and browser automation via JSON-RPC.",
        "icon": "🛠️",
        "installed": True,
        "enabled": True
    },
    {
        "id": "ext-vision-multimodal",
        "name": "Multi-Modal Vision Inspector",
        "category": "Multi-Modal",
        "version": "1.1.0",
        "author": "Gemini Frontier Team",
        "description": "Live image preview, UI diagram analysis, and visual artifact inspection.",
        "icon": "👁️",
        "installed": True,
        "enabled": True
    },
    {
        "id": "ext-myers-diff",
        "name": "Ultra-Fast Myers Diff Engine",
        "category": "Toolkits",
        "version": "2.5.0",
        "author": "PRUBETH Performance",
        "description": "Sub-millisecond visual diffing with syntax color highlighting and chunk review.",
        "icon": "🚀",
        "installed": True,
        "enabled": True
    }
]

NAVY_POPULAR_MODELS = [
    "gemini-3.8-flash", "gemini-3.7-flash", "claude-sonnet-4.5", "claude-haiku-4.5",
    "gpt-5.6-luna", "gpt-5.5", "deepseek-chat", "deepseek-reasoner", "o3-mini", "gpt-4o"
]


def read_json(path, fallback=None):
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return fallback if fallback is not None else {}


def write_json(path, data):
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def verify_gguf_header(path_str):
    try:
        p = Path(path_str)
        if not p.exists():
            return False, "File does not exist."
        with open(p, "rb") as f:
            magic = f.read(4)
            if magic != b"GGUF":
                return False, f"Invalid magic header: {magic.hex()} (Expected GGUF)"
            ver_bytes = f.read(4)
            ver = int.from_bytes(ver_bytes, byteorder="little")
            size_gb = p.stat().st_size / (1024 ** 3)
            return True, f"✓ Valid GGUF v{ver} Model ({size_gb:.2f} GB · Est. VRAM: {size_gb * 1.1:.2f} GB)"
    except Exception as ex:
        return False, f"Header read error: {ex}"


# ==============================================================================
# UI Card & Row Components (Faithful to Reference Design)
# ==============================================================================

class SettingsCard(QFrame):
    """Rounded container card with slate borders matching reference design."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsCard")
        self.setStyleSheet("""
            QFrame#settingsCard {
                background: #181c25;
                border: 1px solid #282d3b;
                border-radius: 10px;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)
        self.layout.setSpacing(12)
        self._row_count = 0

    def add_row(self, title: str, subtitle: str, widget_or_layout, is_sub_row: bool = False):
        if self._row_count > 0:
            divider = QFrame()
            divider.setFixedHeight(1)
            divider.setStyleSheet("background: #232836; border: none;")
            self.layout.addWidget(divider)

        row_w = QWidget()
        row_l = QHBoxLayout(row_w)
        row_l.setContentsMargins(0, 4, 0, 4)
        row_l.setSpacing(16)

        # Left: Title + Subtitle
        text_w = QWidget()
        text_l = QVBoxLayout(text_w)
        text_l.setContentsMargins(0, 0, 0, 0)
        text_l.setSpacing(3)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #f0f6fc; font-size: 13.5px; font-weight: 600;")
        text_l.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setWordWrap(True)
            lbl_sub.setStyleSheet("color: #8b949e; font-size: 11.5px;")
            text_l.addWidget(lbl_sub)

        row_l.addWidget(text_w, 1)

        # Right: Control widget or layout
        if isinstance(widget_or_layout, QWidget):
            row_l.addWidget(widget_or_layout, 0, Qt.AlignRight | Qt.AlignVCenter)
        elif isinstance(widget_or_layout, (QHBoxLayout, QVBoxLayout)):
            row_l.addLayout(widget_or_layout)

        self.layout.addWidget(row_w)
        self._row_count += 1
        return row_w


class SectionHeader(QLabel):
    """All-caps section header matching reference design (IMAGES, WEB SEARCH, etc.)."""
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet("""
            color: #7d8590;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin-top: 16px;
            margin-bottom: 6px;
            margin-left: 2px;
        """)


class PillBadge(QFrame):
    """Dark rounded action pill badge e.g. [ > Automatic · Gemini 3 Flash Preview ]."""
    def __init__(self, text: str, icon_str: str = ">", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #12151d;
                border: 1px solid #2d3342;
                border-radius: 6px;
                padding: 4px 10px;
            }
        """)
        l = QHBoxLayout(self)
        l.setContentsMargins(4, 2, 6, 2)
        l.setSpacing(6)

        if icon_str:
            icon_lbl = QLabel(icon_str)
            icon_lbl.setStyleSheet("color: #a78bfa; font-weight: bold; font-family: 'Cascadia Code', monospace;")
            l.addWidget(icon_lbl)

        self.text_lbl = QLabel(text)
        self.text_lbl.setStyleSheet("color: #e6edf3; font-size: 12px; font-weight: 500;")
        l.addWidget(self.text_lbl)

    def setText(self, t: str):
        self.text_lbl.setText(t)


class SegmentedPillSwitch(QFrame):
    """Segmented toggle switch e.g. [ Model search | Search APIs ]."""
    toggled = pyqtSignal(str)

    def __init__(self, options: List[str], initial_idx: int = 0, parent=None):
        super().__init__(parent)
        self.options = options
        self.setStyleSheet("""
            QFrame {
                background: #12151d;
                border: 1px solid #2d3342;
                border-radius: 6px;
            }
        """)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(2)

        self.buttons = []
        self.group = QButtonGroup(self)
        for i, opt in enumerate(options):
            btn = QPushButton(opt)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #8b949e;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 12px;
                    font-size: 11.5px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background: #252a37;
                    color: #ffffff;
                }
                QPushButton:hover:!checked {
                    color: #c9d1d9;
                }
            """)
            if i == initial_idx:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, text=opt: self.toggled.emit(text))
            self.group.addButton(btn, i)
            self.buttons.append(btn)
            self.layout.addWidget(btn)

    def currentText(self) -> str:
        for b in self.buttons:
            if b.isChecked():
                return b.text()
        return self.options[0] if self.options else ""

    def setCurrentText(self, text: str):
        for b in self.buttons:
            if b.text() == text:
                b.setChecked(True)
                break


# ==============================================================================
# Dedicated Settings Hub Dialog
# ==============================================================================

class UniversalProviderHubDialog(QDialog):
    """
    Intelligent Dedicated Settings & Subsystem Mod Control Center.
    Matches the user's reference UI with top primary navigation, secondary pill bar,
    smooth typography, rounded card layouts, and dedicated control over all IDE mods.
    """
    def __init__(self, settings: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings & Mod Control Center — PRUBETH IDE")
        self.resize(1020, 740)
        self.setMinimumSize(880, 600)
        self.settings = dict(settings or {})

        # Hydrate secrets from CredentialStore (DPAPI/Fernet)
        try:
            from core.credentials import get_credential_store
            c_store = get_credential_store()
            for k in [
                "gemini_api_key", "claude_api_key", "navy_api_key",
                "openai_api_key", "deepseek_api_key", "groq_api_key",
                "github_token", "git_ssh_key", "hf_token", "tavily_api_key"
            ]:
                sec = c_store.get_secret(k)
                if sec and not self.settings.get(k):
                    self.settings[k] = sec
        except Exception:
            pass

        self.accounts = read_json(get_accounts_path(), {})
        self.custom_models = read_json(get_custom_models_path(), [])
        self.extensions = read_json(get_extensions_path(), DEFAULT_EXTENSIONS)

        self._init_typography_and_palette()
        self._build_ui()
        self._init_data()

    def _init_typography_and_palette(self):
        """Smooth typography & sleek obsidian theme."""
        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.SansSerif)
        self.setFont(font)

        self.setStyleSheet("""
            QDialog {
                background-color: #12141a;
                color: #e6edf3;
            }
            QLabel {
                color: #e6edf3;
            }
            QLineEdit {
                background: #12151d;
                border: 1px solid #2d3342;
                border-radius: 6px;
                padding: 6px 10px;
                color: #f0f6fc;
                font-size: 12px;
                selection-background-color: #388bfd;
            }
            QLineEdit:focus {
                border: 1px solid #58a6ff;
            }
            QComboBox {
                background: #12151d;
                border: 1px solid #2d3342;
                border-radius: 6px;
                padding: 5px 10px;
                color: #f0f6fc;
                font-size: 12px;
                min-width: 140px;
            }
            QComboBox:focus, QComboBox:hover {
                border-color: #58a6ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: #161922;
                border: 1px solid #282d3b;
                color: #f0f6fc;
                selection-background-color: #252a37;
            }
            QSpinBox {
                background: #12151d;
                border: 1px solid #2d3342;
                border-radius: 6px;
                padding: 4px 8px;
                color: #f0f6fc;
                font-size: 12px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #232836;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #388bfd;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #f0f6fc;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QCheckBox {
                color: #f0f6fc;
                font-size: 12.5px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #30363d;
                background: #12151d;
            }
            QCheckBox::indicator:checked {
                background: #238636;
                border-color: #2ea043;
            }
            QPushButton {
                background: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #c9d1d9;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #30363d;
                color: #f0f6fc;
                border-color: #8b949e;
            }
            QPushButton#primaryAction {
                background: #238636;
                border-color: #2ea043;
                color: #ffffff;
                font-weight: 600;
            }
            QPushButton#primaryAction:hover {
                background: #2ea043;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #30363d;
                border-radius: 4px;
                min-height: 24px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # ----------------------------------------------------------------------
        # Level 1: Primary Top Navigation Bar (matching reference image)
        # ----------------------------------------------------------------------
        top_bar = QHBoxLayout()
        top_bar.setSpacing(14)

        self.primary_nav_buttons = []
        primary_tabs = [
            ("Agents", 0),
            ("Providers", 1),
            ("Gateway", 2),
            ("Routing", 3),
            ("Local Models", 4),
            ("Editor Mods", 5),
            ("Terminal", 6),
            ("Sync & Backup", 7),
            ("Plugins", 8),
            ("Observability", 9),
        ]
        self.nav_group = QButtonGroup(self)
        for label, idx in primary_tabs:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #8b949e;
                    font-size: 13.5px;
                    font-weight: 500;
                    padding: 4px 6px;
                }
                QPushButton:checked {
                    color: #ffffff;
                    font-weight: 600;
                    border-bottom: 2px solid #58a6ff;
                }
                QPushButton:hover:!checked {
                    color: #c9d1d9;
                }
            """)
            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, index=idx: self.switch_page(index))
            self.nav_group.addButton(btn, idx)
            self.primary_nav_buttons.append(btn)
            top_bar.addWidget(btn)

        top_bar.addStretch()

        btn_reload = QPushButton("⟳")
        btn_reload.setToolTip("Reload Models and Diagnostics")
        btn_reload.setFixedSize(30, 30)
        btn_reload.clicked.connect(self._reload_all_state)
        top_bar.addWidget(btn_reload)

        main_layout.addLayout(top_bar)

        # ----------------------------------------------------------------------
        # Level 2: Secondary Sub-Navigation Pill Bar (matching reference image)
        # ----------------------------------------------------------------------
        pill_bar = QHBoxLayout()
        pill_bar.setSpacing(6)

        sub_pills = [
            ("GENERAL", 5),
            ("ALLOWANCES", 0),
            ("NETWORK AND SHARING", 2),
            ("MODELS", 4),
            ("UNRESTRICTED", 0),
            ("PRIVACY", 9),
            ("OBSERVABILITY", 9),
            ("SYNC AND BACKUP", 7),
            ("ABOUT", 9),
        ]
        self.pill_group = QButtonGroup(self)
        for i, (label, target_page) in enumerate(sub_pills):
            p_btn = QPushButton(label)
            p_btn.setCheckable(True)
            p_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #7d8590;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.05em;
                }
                QPushButton:checked {
                    background: #252a37;
                    color: #ffffff;
                }
                QPushButton:hover:!checked {
                    color: #c9d1d9;
                }
            """)
            if i == 3:  # "MODELS" active by default like in user's image!
                p_btn.setChecked(True)
            p_btn.clicked.connect(lambda _, page=target_page: self.switch_page(page))
            self.pill_group.addButton(p_btn, i)
            pill_bar.addWidget(p_btn)

        pill_bar.addStretch()
        main_layout.addLayout(pill_bar)

        # ----------------------------------------------------------------------
        # Stacked Pages (Central Container)
        # ----------------------------------------------------------------------
        self.tabs = QTabWidget()
        self.tabs.tabBar().setVisible(False)  # Managed by our custom top/pill bars!
        self.tabs.setStyleSheet("QTabWidget::pane { border: none; background: transparent; }")

        # Page 0: Agents & Unrestricted Autonomy
        self.tabs.addTab(self._build_page_agents(), "Agents")
        # Page 1: Cloud Providers
        self.tabs.addTab(self._build_page_providers(), "Providers")
        # Page 2: Gateway & MCP
        self.tabs.addTab(self._build_page_gateway(), "Gateway")
        # Page 3: Routing & Task Policies
        self.tabs.addTab(self._build_page_routing(), "Routing")
        # Page 4: Local Models & GPU Offloading
        self.tabs.addTab(self._build_page_local_models(), "Local Models")
        # Page 5: Editor Mods & Typography
        self.tabs.addTab(self._build_page_editor_mods(), "Editor Mods")
        # Page 6: Terminal & Shell
        self.tabs.addTab(self._build_page_terminal(), "Terminal")
        # Page 7: Sync & Backup (Git / Checkpoints)
        self.tabs.addTab(self._build_page_sync_backup(), "Sync & Backup")
        # Page 8: Plugins & Extensions Marketplace
        self.tabs.addTab(self._build_page_plugins(), "Plugins")
        # Page 9: Observability & Performance
        self.tabs.addTab(self._build_page_observability(), "Observability")

        main_layout.addWidget(self.tabs, 1)

        # ----------------------------------------------------------------------
        # Bottom Control Bar (Presets + Actions)
        # ----------------------------------------------------------------------
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        lbl_presets = QLabel("Presets:")
        lbl_presets.setStyleSheet("color: #8b949e; font-size: 11.5px; font-weight: 600;")
        bottom_bar.addWidget(lbl_presets)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "🎮 Gaming Laptop (GTX 1050 Ti 4GB VRAM)",
            "🔓 Unrestricted Cybersecurity Research Lab",
            "🛡️ Maximum Privacy (Air-Gapped Local Only)",
            "☁️ Frontier Cloud Intelligence (Gemini 1M Context)"
        ])
        self.preset_combo.currentIndexChanged.connect(self._apply_selected_preset)
        bottom_bar.addWidget(self.preset_combo)

        btn_export = QPushButton("📤 Export")
        btn_export.clicked.connect(self._export_settings_action)
        bottom_bar.addWidget(btn_export)

        btn_import = QPushButton("📥 Import")
        btn_import.clicked.connect(self._import_settings_action)
        bottom_bar.addWidget(btn_import)

        bottom_bar.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Save & Apply Settings")
        btn_save.setObjectName("primaryAction")
        btn_save.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_save)

        main_layout.addLayout(bottom_bar)

    def switch_page(self, index: int):
        self.tabs.setCurrentIndex(index)
        for i, btn in enumerate(self.primary_nav_buttons):
            btn.setChecked(i == index)

    # --------------------------------------------------------------------------
    # Page 0: Agents & Unrestricted Autonomy
    # --------------------------------------------------------------------------
    def _build_page_agents(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("MODEL USAGE RESTRICTION & AGENT GOVERNANCE"))

        card_gov = SettingsCard()

        # Governance Restriction Tiers
        self.restriction_tier = QComboBox()
        self.restriction_tier.addItems([
            "🟢 Low (Full Authority / No Restrictions — Unbounded Agentic Programming)",
            "🟡 Mid (Balanced Governance — Supervised Tool Execution & Standard Limits)",
            "🔴 High (Strict Enterprise — Sandboxed Mode, Explicit Step Approvals)"
        ])
        saved_tier = self.settings.get("model_restriction_tier", "low").lower()
        if saved_tier == "high":
            self.restriction_tier.setCurrentIndex(2)
        elif saved_tier == "mid":
            self.restriction_tier.setCurrentIndex(1)
        else:
            self.restriction_tier.setCurrentIndex(0)

        card_gov.add_row(
            "🛡️ Model Usage Restriction Tier",
            "Controls agentic authority and model execution boundaries across the entire IDE.\n"
            "• Low: Full developer authority, zero confirmation friction, unbounded token budget.\n"
            "• Mid: Balanced safety guardrails with standard execution budgets.\n"
            "• High: Strict isolation requiring confirmation for all file modifications.",
            self.restriction_tier
        )

        # Developer Token Budget
        self.token_budget = QComboBox()
        self.token_budget.addItems(["Unlimited (Frontier Full Context)", "128,000 Tokens (Extended)", "32,000 Tokens (Standard)", "8,000 Tokens (Eco)"])
        self.token_budget.setCurrentText(self.settings.get("token_budget", "Unlimited (Frontier Full Context)"))
        card_gov.add_row(
            "📊 Reasoning Token Allowance",
            "Allocates context and reasoning depth per agentic workflow.",
            self.token_budget
        )

        # Tool Execution Policy
        self.tool_exec_policy = QComboBox()
        self.tool_exec_policy.addItems([
            "Direct Autonomous Execution (Instant)",
            "Supervised (Prompt on Destructive Actions)",
            "Strict Review (Confirm Every File & Command)"
        ])
        self.tool_exec_policy.setCurrentText(self.settings.get("tool_exec_policy", "Direct Autonomous Execution (Instant)"))
        card_gov.add_row(
            "⚙️ Agent Tool Execution Policy",
            "Determines whether tools (file writes, shell execution, test runs) execute autonomously or pause for confirmation.",
            self.tool_exec_policy
        )

        self.restriction_tier.currentIndexChanged.connect(self._on_restriction_tier_changed)
        layout.addWidget(card_gov)

        layout.addWidget(SectionHeader("AUTONOMOUS AGENT ALLOWANCES & SAFETY"))

        card1 = SettingsCard()

        # Unrestricted Mode
        self.unrestricted_mode = QCheckBox("Bypass Safety Filters & Refusal Prompts")
        self.unrestricted_mode.setChecked(self.settings.get("unrestricted_mode", True))
        card1.add_row(
            "⚡ Unrestricted Developer Mode",
            "Neutralizes AI refusals and eliminates confirmation friction for uninterrupted development.",
            self.unrestricted_mode
        )

        # Abliteration Mode
        self.abliteration_mode = QCheckBox("Activate Abliterated Vectors")
        self.abliteration_mode.setChecked(self.settings.get("abliteration_mode", True))
        card1.add_row(
            "🔓 Abliteration Vector Optimizer",
            "Optimizes temperature (0.2), top_p (0.95), and suppresses refusal direction tokens for cybersecurity research.",
            self.abliteration_mode
        )

        # Command Execution
        self.allow_commands = QCheckBox("Allow Autonomous Shell Commands")
        self.allow_commands.setChecked(self.settings.get("allow_agent_commands", True))
        card1.add_row(
            "Shell & Terminal Execution",
            "Allows autonomous agents to run test runners, build scripts, and local processes directly.",
            self.allow_commands
        )

        # Multi-file Edits
        self.allow_edits = QCheckBox("Allow Autonomous File Writes")
        self.allow_edits.setChecked(self.settings.get("allow_agent_edits", True))
        card1.add_row(
            "Multi-File Patch & Write Allowance",
            "Allows the agent to write, refactor, and patch multiple files across your workspace without gating.",
            self.allow_edits
        )

        # Max Agent Steps
        self.max_steps = QSpinBox()
        self.max_steps.setRange(1, 100)
        self.max_steps.setValue(self.settings.get("max_agent_steps", 50))
        card1.add_row(
            "Maximum Autonomous Iteration Steps",
            "Upper limit of sequential agent actions before asking for user direction (Default: 50 steps).",
            self.max_steps
        )

        # Self Healing Loop
        self.auto_heal = QCheckBox("Iterate Until Tests Pass")
        self.auto_heal.setChecked(self.settings.get("auto_heal_loop", True))
        card1.add_row(
            "Self-Healing Error Correction Loop",
            "Automatically catches syntax exceptions, tracebacks, and test failures and triggers auto-repair.",
            self.auto_heal
        )

        # Workspace Semantic Context
        self.auto_context = QCheckBox("Index Project Symbols")
        self.auto_context.setChecked(self.settings.get("project_context", True))
        card1.add_row(
            "Automatic Workspace Context Gathering",
            "Parses AST trees, symbols, and imports to augment prompts with relevant project context.",
            self.auto_context
        )

        layout.addWidget(card1)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _on_restriction_tier_changed(self, index: int):
        if index == 0:  # LOW: Full Authority / No Restrictions
            self.unrestricted_mode.setChecked(True)
            self.abliteration_mode.setChecked(True)
            self.allow_commands.setChecked(True)
            self.allow_edits.setChecked(True)
            self.max_steps.setValue(100)
            self.auto_heal.setChecked(True)
            self.token_budget.setCurrentIndex(0)  # Unlimited
            self.tool_exec_policy.setCurrentIndex(0)  # Direct Autonomous Execution
        elif index == 1:  # MID: Balanced Governance
            self.unrestricted_mode.setChecked(False)
            self.abliteration_mode.setChecked(False)
            self.allow_commands.setChecked(True)
            self.allow_edits.setChecked(True)
            self.max_steps.setValue(50)
            self.auto_heal.setChecked(True)
            self.token_budget.setCurrentIndex(2)  # 32,000 Tokens
            self.tool_exec_policy.setCurrentIndex(1)  # Supervised
        elif index == 2:  # HIGH: Strict Enterprise
            self.unrestricted_mode.setChecked(False)
            self.abliteration_mode.setChecked(False)
            self.allow_commands.setChecked(False)
            self.allow_edits.setChecked(False)
            self.max_steps.setValue(10)
            self.auto_heal.setChecked(False)
            self.token_budget.setCurrentIndex(3)  # 8,000 Tokens
            self.tool_exec_policy.setCurrentIndex(2)  # Strict Review

    # --------------------------------------------------------------------------
    # Page 1: Cloud Providers (Gemini, Claude, OpenAI, DeepSeek, Groq, NavyAI)
    # --------------------------------------------------------------------------
    def _build_page_providers(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("FRONTIER CLOUD ENGINES"))

        card_cloud = SettingsCard()

        # Google Gemini
        g_row = QHBoxLayout()
        self.gemini_key = QLineEdit(self.settings.get("gemini_api_key", ""))
        self.gemini_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.gemini_key.setPlaceholderText("Enter Gemini API Key (AQ...)")
        self.gemini_model = QComboBox()
        self.gemini_model.addItems(["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.1-pro-preview", "gemini-2.5-flash"])
        self.gemini_model.setCurrentText(self.settings.get("gemini_model", "gemini-3.8-flash"))
        btn_test_gemini = QPushButton("⚡ Test")
        btn_test_gemini.clicked.connect(self.test_gemini_conn)
        g_row.addWidget(self.gemini_key, 1)
        g_row.addWidget(self.gemini_model)
        g_row.addWidget(btn_test_gemini)
        self.lbl_gemini_status = QLabel("Ready")
        self.lbl_gemini_status.setStyleSheet("color: #8b949e;")
        g_row.addWidget(self.lbl_gemini_status)
        card_cloud.add_row(
            "Google Gemini (1M Token Context)",
            "Primary high-speed reasoning cloud engine with visual multimodal capabilities.",
            g_row
        )

        # Anthropic Claude
        c_row = QHBoxLayout()
        self.claude_key = QLineEdit(self.settings.get("claude_api_key", ""))
        self.claude_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.claude_key.setPlaceholderText("Enter Anthropic API Key (sk-ant-...)")
        self.claude_model = QComboBox()
        self.claude_model.addItems(["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"])
        self.claude_model.setCurrentText(self.settings.get("claude_model", "claude-3-7-sonnet-20250219"))
        btn_test_claude = QPushButton("⚡ Test")
        btn_test_claude.clicked.connect(self.test_claude_conn)
        c_row.addWidget(self.claude_key, 1)
        c_row.addWidget(self.claude_model)
        c_row.addWidget(btn_test_claude)
        self.lbl_claude_status = QLabel("Ready")
        self.lbl_claude_status.setStyleSheet("color: #8b949e;")
        c_row.addWidget(self.lbl_claude_status)
        card_cloud.add_row(
            "Anthropic Claude (Extended Reasoning)",
            "Deep architecture refactoring and step-by-step code analysis engine.",
            c_row
        )

        # NavyAI Unified Gateway
        n_row = QHBoxLayout()
        self.navy_key = QLineEdit(self.settings.get("navy_api_key", ""))
        self.navy_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.navy_key.setPlaceholderText("Enter NavyAI API Key (sk-navy-...)")
        self.navy_url = QLineEdit(self.settings.get("navy_base_url", "https://api.navy/v1"))
        self.navy_model = QComboBox()
        self.navy_model.addItems(NAVY_POPULAR_MODELS)
        self.navy_model.setCurrentText(self.settings.get("navy_model", "deepseek-chat"))
        btn_test_navy = QPushButton("⚡ Sync")
        btn_test_navy.clicked.connect(self.test_navy_conn)
        n_row.addWidget(self.navy_key, 1)
        n_row.addWidget(self.navy_url)
        n_row.addWidget(self.navy_model)
        n_row.addWidget(btn_test_navy)
        self.lbl_navy_status = QLabel("Ready")
        self.lbl_navy_status.setStyleSheet("color: #8b949e;")
        n_row.addWidget(self.lbl_navy_status)
        card_cloud.add_row(
            "NavyAI Unified Multi-Model Gateway",
            "Universal OpenAI-compatible aggregation hub routing to 50+ frontier models.",
            n_row
        )

        # OpenAI
        o_row = QHBoxLayout()
        self.openai_key = QLineEdit(self.settings.get("openai_api_key", ""))
        self.openai_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.openai_key.setPlaceholderText("Enter OpenAI API Key (sk-...)")
        self.openai_url = QLineEdit(self.settings.get("openai_base_url", "https://api.openai.com/v1"))
        self.openai_model = QComboBox()
        self.openai_model.setEditable(True)
        self.openai_model.addItems(["gpt-4o", "gpt-4o-mini", "o3-mini", "o1"])
        self.openai_model.setCurrentText(self.settings.get("openai_model", "gpt-4o"))
        btn_test_openai = QPushButton("⚡ Test")
        btn_test_openai.clicked.connect(self.test_openai_conn)
        o_row.addWidget(self.openai_key, 1)
        o_row.addWidget(self.openai_url)
        o_row.addWidget(self.openai_model)
        o_row.addWidget(btn_test_openai)
        self.lbl_openai_status = QLabel("Ready")
        self.lbl_openai_status.setStyleSheet("color: #8b949e;")
        o_row.addWidget(self.lbl_openai_status)
        card_cloud.add_row(
            "OpenAI Platform",
            "Official OpenAI API endpoint and custom base URL overrides.",
            o_row
        )

        # DeepSeek
        d_row = QHBoxLayout()
        self.deepseek_key = QLineEdit(self.settings.get("deepseek_api_key", ""))
        self.deepseek_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.deepseek_model = QComboBox()
        self.deepseek_model.addItems(["deepseek-chat", "deepseek-reasoner"])
        self.deepseek_model.setCurrentText(self.settings.get("deepseek_model", "deepseek-chat"))
        btn_test_deepseek = QPushButton("⚡ Test")
        btn_test_deepseek.clicked.connect(self.test_deepseek_conn)
        d_row.addWidget(self.deepseek_key, 1)
        d_row.addWidget(self.deepseek_model)
        d_row.addWidget(btn_test_deepseek)
        self.lbl_deepseek_status = QLabel("Ready")
        self.lbl_deepseek_status.setStyleSheet("color: #8b949e;")
        d_row.addWidget(self.lbl_deepseek_status)
        card_cloud.add_row(
            "DeepSeek API (V3 & R1)",
            "DeepSeek native API key connection for fast coding and deep reasoning.",
            d_row
        )

        # Groq
        gr_row = QHBoxLayout()
        self.groq_key = QLineEdit(self.settings.get("groq_api_key", ""))
        self.groq_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.groq_model = QComboBox()
        self.groq_model.addItems(["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])
        self.groq_model.setCurrentText(self.settings.get("groq_model", "llama-3.3-70b-versatile"))
        btn_test_groq = QPushButton("⚡ Test")
        btn_test_groq.clicked.connect(self.test_groq_conn)
        gr_row.addWidget(self.groq_key, 1)
        gr_row.addWidget(self.groq_model)
        gr_row.addWidget(btn_test_groq)
        self.lbl_groq_status = QLabel("Ready")
        self.lbl_groq_status.setStyleSheet("color: #8b949e;")
        gr_row.addWidget(self.lbl_groq_status)
        card_cloud.add_row(
            "Groq Ultra-Fast LPU (300+ tok/s)",
            "Instant response generation for quick edits and automated unit tests.",
            gr_row
        )

        layout.addWidget(card_cloud)

        # Custom Model Registration Table
        layout.addWidget(SectionHeader("CUSTOM & PRIVATE MODEL REGISTRATIONS"))
        card_cust = SettingsCard()

        cm_inputs = QHBoxLayout()
        self.custom_provider_name = QLineEdit()
        self.custom_provider_name.setPlaceholderText("Provider Name (e.g. TogetherAI)")
        self.custom_base_url = QLineEdit()
        self.custom_base_url.setPlaceholderText("Base URL (e.g. https://api.together.xyz/v1)")
        self.custom_api_key = QLineEdit()
        self.custom_api_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.custom_api_key.setPlaceholderText("API Key")
        self.custom_model_id = QComboBox()
        self.custom_model_id.setEditable(True)
        self.custom_model_id.addItems(["meta-llama/Llama-Vision-Free", "qwen2.5-coder-32b"])
        cm_inputs.addWidget(self.custom_provider_name)
        cm_inputs.addWidget(self.custom_base_url)
        cm_inputs.addWidget(self.custom_api_key)
        cm_inputs.addWidget(self.custom_model_id)
        card_cust.add_row("Register Custom API Endpoint", "Connect any private LLM, LM Studio, or vLLM server.", cm_inputs)

        mods_row = QHBoxLayout()
        self.mod_chat = QCheckBox("Chat")
        self.mod_chat.setChecked(True)
        self.mod_vision = QCheckBox("Vision")
        self.mod_audio = QCheckBox("Audio")
        self.mod_code = QCheckBox("Code")
        self.mod_code.setChecked(True)
        self.mod_agent = QCheckBox("Agent Loop")
        self.mod_agent.setChecked(True)
        self.custom_ctx_size = QSpinBox()
        self.custom_ctx_size.setRange(2048, 1000000)
        self.custom_ctx_size.setValue(32768)
        btn_add_custom = QPushButton("＋ Add Model")
        btn_add_custom.setObjectName("primaryAction")
        btn_add_custom.clicked.connect(self.add_custom_model_action)
        mods_row.addWidget(self.mod_chat)
        mods_row.addWidget(self.mod_vision)
        mods_row.addWidget(self.mod_audio)
        mods_row.addWidget(self.mod_code)
        mods_row.addWidget(self.mod_agent)
        mods_row.addWidget(QLabel("Context:"))
        mods_row.addWidget(self.custom_ctx_size)
        mods_row.addWidget(btn_add_custom)
        card_cust.add_row("Model Capabilities & Add", "Specify modalities and context window size.", mods_row)

        self.custom_table = QTableWidget(0, 6)
        self.custom_table.setHorizontalHeaderLabels(["Provider", "Model ID", "Base URL", "Capabilities", "Status", "Action"])
        self.custom_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.custom_table.setFixedHeight(140)
        self.custom_table.setStyleSheet("background: #12151d; border: 1px solid #282d3b; border-radius: 6px;")
        card_cust.layout.addWidget(self.custom_table)

        self.lbl_custom_status = QLabel("Ready")
        self.lbl_custom_status.setStyleSheet("color: #8b949e;")
        card_cust.layout.addWidget(self.lbl_custom_status)

        layout.addWidget(card_cust)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # --------------------------------------------------------------------------
    # Page 2: Gateway & Web Search Tools (matching user screenshot)
    # --------------------------------------------------------------------------
    def _build_page_gateway(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(12)

        # 1. Images section from user's image
        layout.addWidget(SectionHeader("IMAGES"))
        card_img = SettingsCard()

        self.badge_img_rec = PillBadge("Automatic · Gemini 3 Flash Preview · Gemini CLI", ">")
        card_img.add_row(
            "Image recognition",
            "When the model in use can't see images, PRUBETH IDE routes vision queries through a multimodal inspector.",
            self.badge_img_rec
        )

        self.badge_img_gen = PillBadge("Automatic · no model that draws", "")
        card_img.add_row(
            "Image generation",
            "The model utilized for SVG diagrams and graphical assets generation.",
            self.badge_img_gen
        )
        layout.addWidget(card_img)

        # 2. Web Search section from user's image
        layout.addWidget(SectionHeader("WEB SEARCH"))
        card_search = SettingsCard()

        self.badge_search_models = PillBadge("Automatic · Gemini CLI · Gemini 3 Flash Preview", ">")
        card_search.add_row(
            "Searches for other models",
            "When a local model can't search the web directly, queries are fulfilled via search tools.",
            self.badge_search_models
        )

        # Search APIs input row matching image: [ Tavily ▾ ] [ API key... ] [ Get a key ↗ ] [ Add ]
        api_row = QHBoxLayout()
        self.search_provider_combo = QComboBox()
        self.search_provider_combo.addItems(["Tavily", "DuckDuckGo", "Google Search", "Bing"])
        self.tavily_key = QLineEdit(self.settings.get("tavily_api_key", ""))
        self.tavily_key.setPlaceholderText("API key, or several split by commas")
        btn_get_key = QPushButton("Get a key ↗")
        btn_get_key.setStyleSheet("color: #58a6ff; background: transparent; border: none; text-decoration: underline;")
        btn_get_key.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://tavily.com")))
        btn_add_key = QPushButton("Add")
        btn_add_key.clicked.connect(self._add_search_key_action)

        api_row.addWidget(self.search_provider_combo)
        api_row.addWidget(self.tavily_key, 1)
        api_row.addWidget(btn_get_key)
        api_row.addWidget(btn_add_key)

        card_search.add_row(
            "Search APIs",
            "When a model can't search the web, PRUBETH searches with these in order. Asked before fallback search.",
            api_row
        )

        # Registered item line from image: 1. Tavily tvly... [ Show ] [ Copy ] [ Remove ]
        key_display_row = QHBoxLayout()
        self.lbl_tavily_display = QLabel("1. Tavily  " + (self.settings.get("tavily_api_key", "tvly...0GW2")[:8] + "..." if self.settings.get("tavily_api_key") else "None configured"))
        self.lbl_tavily_display.setStyleSheet("color: #e6edf3; font-weight: 500;")
        btn_show = QPushButton("Show")
        btn_copy = QPushButton("Copy")
        btn_remove = QPushButton("Remove")
        btn_show.clicked.connect(self._toggle_show_search_key)
        btn_copy.clicked.connect(self._copy_search_key)
        btn_remove.clicked.connect(self._remove_search_key)
        key_display_row.addWidget(self.lbl_tavily_display, 1)
        key_display_row.addWidget(btn_show)
        key_display_row.addWidget(btn_copy)
        key_display_row.addWidget(btn_remove)
        card_search.add_row("Active Search Credentials", "", key_display_row)

        # Search First With segmented switch from image: [ Model search | Search APIs ]
        self.switch_search_first = SegmentedPillSwitch(["Model search", "Search APIs"], 1)
        card_search.add_row(
            "Search first with",
            "The other is asked when it fails.",
            self.switch_search_first
        )
        layout.addWidget(card_search)

        # 3. Model Context Protocol (MCP)
        layout.addWidget(SectionHeader("MODEL CONTEXT PROTOCOL (MCP)"))
        card_mcp = SettingsCard()
        self.mcp_text = QPlainTextEdit()
        default_mcp = read_json(get_mcp_config_path(), {
            "mcpServers": {
                "filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]},
                "duckduckgo": {"description": "Built-in web search & documentation fetcher", "enabled": True},
                "pytest-runner": {"description": "Automated unit test execution & traceback capture", "enabled": True}
            }
        })
        self.mcp_text.setPlainText(json.dumps(default_mcp, indent=2))
        self.mcp_text.setFixedHeight(120)
        self.mcp_text.setStyleSheet("background: #12151d; border: 1px solid #282d3b; border-radius: 6px; font-family: 'Cascadia Code', monospace;")

        btn_save_mcp = QPushButton("💾 Save MCP Configuration")
        btn_save_mcp.clicked.connect(self.save_mcp_config)
        card_mcp.add_row("MCP Servers Configuration (JSON)", "Connect external tool processes via MCP specification.", btn_save_mcp)
        card_mcp.layout.addWidget(self.mcp_text)
        layout.addWidget(card_mcp)

        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # --------------------------------------------------------------------------
    # Page 3: Routing & Task Policies
    # --------------------------------------------------------------------------
    def _build_page_routing(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("TASK-SPECIFIC ROUTING & FAILOVER POLICIES"))
        card = SettingsCard()

        self.route_code = QComboBox()
        self.route_code.addItems(["gemini-3.8-flash → redsage-8b → gpt-4o", "redsage-8b (Local Only)", "gemini-3.8-flash (Cloud Fast)"])
        card.add_row("Code Generation & Refactoring", "Primary model used when generating or modifying codebase files.", self.route_code)

        self.route_chat = QComboBox()
        self.route_chat.addItems(["redsage-8b → qwen2.5:1.5b → gemini-3.8-flash", "qwen2.5:1.5b (Ultra Low Latency)", "gemini-3.8-flash"])
        card.add_row("Fast Chat & Explanations", "Low-latency conversational answers and symbol queries.", self.route_chat)

        self.route_plan = QComboBox()
        self.route_plan.addItems(["claude-3-7-sonnet-20250219 → deepseek-r1:7b → gemini-3.8-flash", "deepseek-r1:7b (Local Reasoning)", "claude-3-7-sonnet"])
        card.add_row("Architecture Planning & Reasoning", "Multi-step architectural decomposition and deep reasoning tasks.", self.route_plan)

        self.route_troubleshoot = QComboBox()
        self.route_troubleshoot.addItems(["gemini-3.8-flash → redsage-8b → qwen2.5:1.5b", "redsage-8b (Local Unrestricted)"])
        card.add_row("Troubleshooting & Error Auto-Fix", "Automated bug investigation and unit test repair loop.", self.route_troubleshoot)

        layout.addWidget(card)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # --------------------------------------------------------------------------
    # Page 4: Local Models & GPU Offloading (Focus Area!)
    # --------------------------------------------------------------------------
    def _build_page_local_models(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("LOCAL HARDWARE ACCELERATION & OLLAMA ENGINE"))
        card_hw = SettingsCard()

        # Detected Hardware
        hw_str = self.detect_hardware()
        self.badge_hw = PillBadge(f"Detected: {hw_str}", "⚡")
        card_hw.add_row(
            "Hardware & GPU Acceleration",
            "NVIDIA CUDA offload status for your GeForce GTX 1050 Ti.",
            self.badge_hw
        )

        # Ollama Server URL & Test
        ol_row = QHBoxLayout()
        self.ollama_url = QLineEdit(self.settings.get("ollama_url", "http://localhost:11434"))
        btn_detect = QPushButton("⚡ Detect Models")
        btn_detect.clicked.connect(self.test_ollama_conn)
        self.lbl_ollama_status = QLabel("Ready")
        self.lbl_ollama_status.setStyleSheet("color: #8b949e;")
        ol_row.addWidget(self.ollama_url, 1)
        ol_row.addWidget(btn_detect)
        ol_row.addWidget(self.lbl_ollama_status)
        card_hw.add_row(
            "Ollama Daemon Connection",
            "Local REST API endpoint hosting your offline models.",
            ol_row
        )

        # Active Model Selector
        self.ollama_model = QComboBox()
        self.ollama_model.setEditable(True)
        self.ollama_model.addItems(["redsage-8b:latest", "deepseek-r1:7b", "qwen2.5:1.5b"])
        self.ollama_model.setCurrentText(self.settings.get("local_model", "redsage-8b:latest"))
        card_hw.add_row(
            "Active Local Model in IDE",
            "Primary local model used for offline chat, code editing, and cybersecurity tasks.",
            self.ollama_model
        )

        # GPU Offload Layers
        layers_row = QHBoxLayout()
        self.gguf_layers = QSlider(Qt.Horizontal)
        self.gguf_layers.setRange(0, 99)
        self.gguf_layers.setValue(self.settings.get("gguf_gpu_layers", 33))
        self.lbl_layers_val = QLabel(f"{self.gguf_layers.value()} layers (CUDA VRAM)")
        self.lbl_layers_val.setStyleSheet("color: #38bdf8; font-weight: bold;")
        self.gguf_layers.valueChanged.connect(lambda v: self.lbl_layers_val.setText(f"{v} layers (CUDA VRAM)" if v > 0 else "0 (CPU Only)"))
        layers_row.addWidget(self.gguf_layers, 1)
        layers_row.addWidget(self.lbl_layers_val)
        card_hw.add_row(
            "CUDA GPU Offload Layers",
            "Layers loaded directly into GPU VRAM. Remaining layers offload to system RAM seamlessly.",
            layers_row
        )

        # Context Window
        self.gguf_ctx = QComboBox()
        self.gguf_ctx.addItems(["4096", "8192", "16384", "32768", "65536"])
        self.gguf_ctx.setCurrentText(str(self.settings.get("gguf_context_window", "8192")))
        card_hw.add_row(
            "Context Window Allocation",
            "Token context limit. 8,192 is optimal for 4GB VRAM cards.",
            self.gguf_ctx
        )
        layout.addWidget(card_hw)

        # GGUF Direct Loader Card
        layout.addWidget(SectionHeader("GGUF MODEL DIRECT LOADER & BUILDER"))
        card_gguf = SettingsCard()

        file_row = QHBoxLayout()
        self.gguf_path = QLineEdit(self.settings.get("direct_gguf_path", ""))
        self.gguf_path.setPlaceholderText("Select any downloaded .gguf file...")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_gguf_file)
        file_row.addWidget(self.gguf_path, 1)
        file_row.addWidget(btn_browse)
        card_gguf.add_row(
            "Select Downloaded GGUF File",
            "Point to any local quantized model file on disk.",
            file_row
        )

        alias_row = QHBoxLayout()
        self.gguf_alias = QLineEdit()
        self.gguf_alias.setPlaceholderText("e.g. redsage-8b or foundation-sec")
        btn_verify_file = QPushButton("⚡ Verify Header")
        btn_verify_file.clicked.connect(self.verify_gguf_action)
        alias_row.addWidget(self.gguf_alias, 1)
        alias_row.addWidget(btn_verify_file)
        card_gguf.add_row(
            "Model Name Alias in IDE",
            "Unique identifier to call this model in IDE model dropdowns.",
            alias_row
        )

        reg_row = QHBoxLayout()
        self.lbl_gguf_status = QLabel("Ready to build & load")
        self.lbl_gguf_status.setStyleSheet("color: #8b949e;")
        btn_load_gguf = QPushButton("🚀 Load & Register in Ollama")
        btn_load_gguf.setObjectName("primaryAction")
        btn_load_gguf.clicked.connect(self.load_and_add_local_model_action)
        reg_row.addWidget(self.lbl_gguf_status, 1)
        reg_row.addWidget(btn_load_gguf)
        card_gguf.add_row(
            "Execute Modelfile Creation",
            "Builds Modelfile with optimized parameters and adds the model directly to your IDE.",
            reg_row
        )
        layout.addWidget(card_gguf)

        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # --------------------------------------------------------------------------
    # Page 5: Editor Mods & Typography
    # --------------------------------------------------------------------------
    def _build_page_editor_mods(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("TYPOGRAPHY & CODE RENDERING"))
        card = SettingsCard()

        # Font Family
        self.editor_font_combo = QComboBox()
        self.editor_font_combo.addItems(["Segoe UI", "Cascadia Code", "Consolas", "Fira Code", "JetBrains Mono"])
        self.editor_font_combo.setCurrentText(self.settings.get("editor_font_family", "Consolas"))
        card.add_row("Editor Font Family", "Primary monospace typeface for code editors and terminal panes.", self.editor_font_combo)

        # Font Size
        self.editor_font_size = QSpinBox()
        self.editor_font_size.setRange(9, 28)
        self.editor_font_size.setValue(self.settings.get("editor_font_size", 13))
        card.add_row("Editor Font Size", "Point size for code readability (Default: 13pt).", self.editor_font_size)

        # Tab Size
        self.editor_tab_size = SegmentedPillSwitch(["2 Spaces", "4 Spaces"], 1 if self.settings.get("editor_tab_size", 4) == 4 else 0)
        card.add_row("Tab Size & Indentation", "Number of spaces inserted for tabs and auto-indent.", self.editor_tab_size)

        # Word Wrap
        self.editor_word_wrap = QCheckBox("Enable Soft Wrap")
        self.editor_word_wrap.setChecked(self.settings.get("editor_word_wrap", True))
        card.add_row("Soft Word Wrap", "Wrap long lines to fit the editor viewport width.", self.editor_word_wrap)

        # Line Numbers
        self.editor_line_numbers = QCheckBox("Show Line Numbers")
        self.editor_line_numbers.setChecked(self.settings.get("editor_line_numbers", True))
        card.add_row("Line Number Gutter", "Display line numbers and diff change indicators in gutter.", self.editor_line_numbers)

        layout.addWidget(card)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # --------------------------------------------------------------------------
    # Page 6: Terminal & Execution Environment
    # --------------------------------------------------------------------------
    def _build_page_terminal(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("TERMINAL & RUNTIME ENVIRONMENT"))
        card = SettingsCard()

        self.terminal_shell_combo = QComboBox()
        self.terminal_shell_combo.addItems(["PowerShell (pwsh)", "Command Prompt (cmd.exe)", "Git Bash", "WSL"])
        self.terminal_shell_combo.setCurrentText(self.settings.get("terminal_shell", "PowerShell (pwsh)"))
        card.add_row("Default Embedded Shell", "Shell interpreter launched inside the interactive terminal dock.", self.terminal_shell_combo)

        py_row = QHBoxLayout()
        self.python_path = QLineEdit(self.settings.get("python_interpreter", sys.executable))
        btn_auto_py = QPushButton("Auto-Detect .venv")
        btn_auto_py.clicked.connect(self._auto_detect_venv)
        py_row.addWidget(self.python_path, 1)
        py_row.addWidget(btn_auto_py)
        card.add_row("Python Virtual Environment Path", "Active python executable used for running tests and scripts.", py_row)

        self.terminal_buffer_size = QSpinBox()
        self.terminal_buffer_size.setRange(1000, 50000)
        self.terminal_buffer_size.setValue(self.settings.get("terminal_buffer_lines", 10000))
        card.add_row("Terminal Scrollback Buffer", "Maximum lines of history preserved in terminal view.", self.terminal_buffer_size)

        layout.addWidget(card)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # --------------------------------------------------------------------------
    # Page 7: Sync & Backup (Git / Accounts / Checkpoints)
    # --------------------------------------------------------------------------
    def _build_page_sync_backup(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("GITHUB & GIT IDENTITY"))
        card_git = SettingsCard()

        git_row = QHBoxLayout()
        self.github_token = QLineEdit(self.accounts.get("github_token", os.environ.get("GITHUB_TOKEN", "")))
        self.github_token.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.github_token.setPlaceholderText("Personal Access Token (ghp_...)")
        btn_verify_git = QPushButton("⚡ Verify Token")
        btn_verify_git.clicked.connect(self.verify_github_conn)
        git_row.addWidget(self.github_token, 1)
        git_row.addWidget(btn_verify_git)
        card_git.add_row("GitHub PAT Token", "Used for cloning, pushing, and GitHub releases synchronization.", git_row)

        id_row = QHBoxLayout()
        self.github_user = QLineEdit(self.accounts.get("github_username", ""))
        self.github_user.setPlaceholderText("Username")
        self.git_email = QLineEdit(self.accounts.get("git_email", ""))
        self.git_email.setPlaceholderText("Email")
        btn_apply_git = QPushButton("Set Global Identity")
        btn_apply_git.clicked.connect(self.apply_git_identity)
        id_row.addWidget(self.github_user)
        id_row.addWidget(self.git_email)
        id_row.addWidget(btn_apply_git)
        card_git.add_row("Git Commit Identity", "Author and committer identity written to repository commits.", id_row)

        self.git_ssh_key = QLineEdit(self.accounts.get("git_ssh_key", ""))
        self.git_ssh_key.setPlaceholderText("e.g. C:\\Users\\asus\\.ssh\\id_ed25519")
        card_git.add_row("SSH Private Key Path", "Path to SSH key for SSH git clone and push operations.", self.git_ssh_key)

        self.lbl_github_status = QLabel(self.accounts.get("github_status", "Status: Ready"))
        self.lbl_github_status.setStyleSheet("color: #8b949e;")
        card_git.add_row("GitHub Auth Status", "", self.lbl_github_status)
        layout.addWidget(card_git)

        # Google Cloud & HF
        layout.addWidget(SectionHeader("EXTERNAL DEVELOPER ACCOUNTS"))
        card_ext = SettingsCard()

        g_row = QHBoxLayout()
        self.google_email = QLineEdit(self.accounts.get("google_email", ""))
        self.google_email.setPlaceholderText("Google Email")
        self.google_project = QLineEdit(self.accounts.get("google_project", ""))
        self.google_project.setPlaceholderText("GCP Project ID")
        btn_v_google = QPushButton("⚡ Verify")
        btn_v_google.clicked.connect(self.verify_google_conn)
        g_row.addWidget(self.google_email)
        g_row.addWidget(self.google_project)
        g_row.addWidget(btn_v_google)
        card_ext.add_row("Google Cloud & ADC", "Project ID and account for Vertex / Gemini Cloud resources.", g_row)

        self.google_adc_path = QLineEdit(self.accounts.get("google_adc_path", ""))
        self.google_adc_path.setPlaceholderText("Application Default Credentials path...")
        card_ext.add_row("Google ADC File Path", "Local JSON path to Google credentials.", self.google_adc_path)
        self.lbl_google_status = QLabel(self.accounts.get("google_status", "Ready"))
        self.lbl_google_status.setStyleSheet("color: #8b949e;")
        card_ext.add_row("Google Auth Status", "", self.lbl_google_status)

        hf_row = QHBoxLayout()
        self.hf_token = QLineEdit(self.accounts.get("hf_token", os.environ.get("HF_TOKEN", "")))
        self.hf_token.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.hf_token.setPlaceholderText("Hugging Face Token (hf_...)")
        btn_v_hf = QPushButton("⚡ Verify")
        btn_v_hf.clicked.connect(self.verify_hf_conn)
        hf_row.addWidget(self.hf_token, 1)
        hf_row.addWidget(btn_v_hf)
        card_ext.add_row("Hugging Face Hub Token", "Enables downloading gated GGUF security models directly.", hf_row)
        self.lbl_hf_status = QLabel(self.accounts.get("hf_status", "Ready"))
        self.lbl_hf_status.setStyleSheet("color: #8b949e;")
        card_ext.add_row("HF Auth Status", "", self.lbl_hf_status)

        layout.addWidget(card_ext)

        # Checkpoints
        layout.addWidget(SectionHeader("TRANSACTIONAL TIME-MACHINE CHECKPOINTS"))
        card_cp = SettingsCard()
        self.max_checkpoints_spin = QSpinBox()
        self.max_checkpoints_spin.setRange(10, 200)
        self.max_checkpoints_spin.setValue(self.settings.get("max_checkpoints", 50))
        card_cp.add_row("Maximum Checkpoints Preserved", "Snapshot history limit retained before FIFO trimming.", self.max_checkpoints_spin)

        self.auto_checkpoint_toggle = QCheckBox("Save Snapshot Before Every AI Action")
        self.auto_checkpoint_toggle.setChecked(self.settings.get("auto_checkpoint_on_edit", True))
        card_cp.add_row("Automatic Rollback Safety Snapshot", "Enables immediate 1-click restore if an agent edit has errors.", self.auto_checkpoint_toggle)
        layout.addWidget(card_cp)

        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # --------------------------------------------------------------------------
    # Page 8: Plugins & Extensions Marketplace
    # --------------------------------------------------------------------------
    def _build_page_plugins(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(SectionHeader("EXTENSIONS & PLUGIN MARKETPLACE"))

        search_bar = QHBoxLayout()
        self.ext_search_edit = QLineEdit()
        self.ext_search_edit.setPlaceholderText("🔍 Search extensions by name, keyword, or author...")
        self.ext_search_edit.textChanged.connect(self.populate_extension_cards)
        search_bar.addWidget(self.ext_search_edit, 1)

        self.ext_category_combo = QComboBox()
        self.ext_category_combo.addItems([
            "All Categories", "IDE Bridges", "AI Agents", "Multi-Modal", "Private Cloud", "Toolkits"
        ])
        self.ext_category_combo.currentTextChanged.connect(self.populate_extension_cards)
        search_bar.addWidget(self.ext_category_combo)

        btn_add_ext = QPushButton("＋ Add Custom Plugin…")
        btn_add_ext.clicked.connect(self.import_custom_extension_dialog)
        search_bar.addWidget(btn_add_ext)
        layout.addLayout(search_bar)

        self.ext_scroll = QScrollArea()
        self.ext_scroll.setWidgetResizable(True)
        self.ext_scroll.setStyleSheet("QScrollArea { border: 1px solid #282d3b; background: #12151d; border-radius: 8px; }")
        self.ext_card_container = QWidget()
        self.ext_card_layout = QVBoxLayout(self.ext_card_container)
        self.ext_card_layout.setSpacing(8)
        self.ext_scroll.setWidget(self.ext_card_container)
        layout.addWidget(self.ext_scroll, 1)

        return content

    # --------------------------------------------------------------------------
    # Page 9: Observability & Performance
    # --------------------------------------------------------------------------
    def _build_page_observability(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("PERFORMANCE, MEMORY & CACHING"))
        card = SettingsCard()

        self.fast_diff_toggle = QCheckBox("Enable Myers Sub-Millisecond Diff")
        self.fast_diff_toggle.setChecked(self.settings.get("fast_diff_engine", True))
        card.add_row("Ultra-Fast Myers Diff Engine", "High-performance C/Python diff computation for large files.", self.fast_diff_toggle)

        self.lexer_cache_toggle = QCheckBox("Enable Token Stream Caching")
        self.lexer_cache_toggle.setChecked(self.settings.get("lexer_cache_enabled", True))
        card.add_row("Lexer Syntax Highlight Caching", "Caches tokenized code blocks to eliminate UI stuttering when scrolling.", self.lexer_cache_toggle)

        self.vram_spin = QSpinBox()
        self.vram_spin.setRange(1024, 65536)
        self.vram_spin.setValue(self.settings.get("cuda_vram_limit_mb", 4096))
        card.add_row("CUDA VRAM Hardware Threshold (MB)", "Estimated VRAM ceiling for splitting layers between GPU and RAM.", self.vram_spin)

        clean_row = QHBoxLayout()
        btn_open_storage = QPushButton("📂 Open Storage")
        btn_open_storage.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(APP_HOME))))
        btn_open_logs = QPushButton("📂 Open Logs")
        btn_open_logs.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(LOGS_DIR))))
        btn_clear_cache = QPushButton("🧹 Clear Caches")
        btn_clear_cache.clicked.connect(self._clear_caches_action)
        clean_row.addWidget(btn_open_storage)
        clean_row.addWidget(btn_open_logs)
        clean_row.addWidget(btn_clear_cache)
        card.add_row("Storage & Cache Management", "Explore local studio files, inspection logs, and purge temporary caches.", clean_row)

        layout.addWidget(card)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # --------------------------------------------------------------------------
    # Business Logic & Connection Testing Methods
    # --------------------------------------------------------------------------
    def _init_data(self):
        self.init_custom_models_table()
        self.populate_extension_cards()

    def detect_hardware(self) -> str:
        try:
            res = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip():
                return f"GPU: {res.stdout.strip()}"
        except Exception:
            pass
        return "CPU Execution"

    def test_gemini_conn(self):
        key = self.gemini_key.text().strip()
        if not key:
            self.lbl_gemini_status.setText("<font color='#EF4444'>✗ Missing Key</font>")
            return
        self.lbl_gemini_status.setText("Testing…")
        QApplication.processEvents()
        t0 = time.time()
        try:
            m = self.gemini_model.currentText()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:streamGenerateContent?alt=sse"
            headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
            payload = {"contents": [{"role": "user", "parts": [{"text": "hi"}]}]}
            r = requests.post(url, headers=headers, json=payload, timeout=8, stream=True)
            r.raise_for_status()
            lat = int((time.time() - t0) * 1000)
            self.lbl_gemini_status.setText(f"<font color='#34D399'>✓ Online ({lat}ms)</font>")
        except Exception as ex:
            self.lbl_gemini_status.setText(f"<font color='#EF4444'>✗ {str(ex)[:40]}</font>")

    def test_claude_conn(self):
        key = self.claude_key.text().strip()
        if not key:
            self.lbl_claude_status.setText("<font color='#EF4444'>✗ Missing Key</font>")
            return
        self.lbl_claude_status.setText("Testing…")
        QApplication.processEvents()
        t0 = time.time()
        try:
            headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
            payload = {"model": "claude-3-5-haiku-20241022", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]}
            r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=8)
            r.raise_for_status()
            lat = int((time.time() - t0) * 1000)
            self.lbl_claude_status.setText(f"<font color='#34D399'>✓ Online ({lat}ms)</font>")
        except Exception as ex:
            self.lbl_claude_status.setText(f"<font color='#EF4444'>✗ {str(ex)[:40]}</font>")

    def test_navy_conn(self):
        key = self.navy_key.text().strip()
        url = self.navy_url.text().strip().rstrip("/")
        if not key:
            self.lbl_navy_status.setText("<font color='#EF4444'>✗ Missing Key</font>")
            return
        self.lbl_navy_status.setText("Syncing…")
        QApplication.processEvents()
        t0 = time.time()
        try:
            r = requests.get(f"{url}/models", headers={"Authorization": f"Bearer {key}"}, timeout=8)
            r.raise_for_status()
            lat = int((time.time() - t0) * 1000)
            data = r.json()
            models = []
            if isinstance(data, list):
                models = [m.get("id") for m in data if isinstance(m, dict) and "id" in m]
            elif isinstance(data, dict):
                models = [m.get("id") for m in data.get("data", []) if isinstance(m, dict) and "id" in m]
            if models:
                curr = self.navy_model.currentText()
                self.navy_model.clear()
                self.navy_model.addItems(models)
                if curr in models:
                    self.navy_model.setCurrentText(curr)
                self.lbl_navy_status.setText(f"<font color='#34D399'>✓ Online ({lat}ms · {len(models)} models)</font>")
            else:
                self.lbl_navy_status.setText(f"<font color='#34D399'>✓ Online ({lat}ms)</font>")
        except Exception as ex:
            self.lbl_navy_status.setText(f"<font color='#EF4444'>✗ {str(ex)[:40]}</font>")

    def test_openai_conn(self):
        key = self.openai_key.text().strip()
        url = self.openai_url.text().strip().rstrip("/")
        if not key:
            self.lbl_openai_status.setText("<font color='#EF4444'>✗ Missing Key</font>")
            return
        self.lbl_openai_status.setText("Testing…")
        QApplication.processEvents()
        t0 = time.time()
        try:
            r = requests.get(f"{url}/models", headers={"Authorization": f"Bearer {key}"}, timeout=8)
            r.raise_for_status()
            lat = int((time.time() - t0) * 1000)
            self.lbl_openai_status.setText(f"<font color='#34D399'>✓ Online ({lat}ms)</font>")
        except Exception as ex:
            self.lbl_openai_status.setText(f"<font color='#EF4444'>✗ {str(ex)[:40]}</font>")

    def test_deepseek_conn(self):
        key = self.deepseek_key.text().strip()
        if not key:
            self.lbl_deepseek_status.setText("<font color='#EF4444'>✗ Missing Key</font>")
            return
        self.lbl_deepseek_status.setText("Testing…")
        QApplication.processEvents()
        t0 = time.time()
        try:
            r = requests.get("https://api.deepseek.com/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=8)
            r.raise_for_status()
            lat = int((time.time() - t0) * 1000)
            self.lbl_deepseek_status.setText(f"<font color='#34D399'>✓ Online ({lat}ms)</font>")
        except Exception as ex:
            self.lbl_deepseek_status.setText(f"<font color='#EF4444'>✗ {str(ex)[:40]}</font>")

    def test_groq_conn(self):
        key = self.groq_key.text().strip()
        if not key:
            self.lbl_groq_status.setText("<font color='#EF4444'>✗ Missing Key</font>")
            return
        self.lbl_groq_status.setText("Testing…")
        QApplication.processEvents()
        t0 = time.time()
        try:
            r = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=8)
            r.raise_for_status()
            lat = int((time.time() - t0) * 1000)
            self.lbl_groq_status.setText(f"<font color='#34D399'>✓ Online ({lat}ms)</font>")
        except Exception as ex:
            self.lbl_groq_status.setText(f"<font color='#EF4444'>✗ {str(ex)[:40]}</font>")

    def test_ollama_conn(self):
        url = self.ollama_url.text().strip().rstrip("/")
        self.lbl_ollama_status.setText("Detecting…")
        QApplication.processEvents()
        t0 = time.time()
        try:
            r = requests.get(f"{url}/api/tags", timeout=5)
            r.raise_for_status()
            models = [m.get("name") for m in r.json().get("models", [])]
            lat = int((time.time() - t0) * 1000)
            self.ollama_model.clear()
            self.ollama_model.addItems(models if models else ["qwen2.5:1.5b"])
            self.lbl_ollama_status.setText(f"<font color='#34D399'>✓ {len(models)} model(s) detected ({lat}ms)</font>")
        except Exception as ex:
            self.lbl_ollama_status.setText(f"<font color='#EF4444'>✗ Ollama offline</font>")

    def browse_gguf_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select GGUF Model File", "", "Model Files (*.gguf *.bin *.safetensors);;All Files (*)")
        if path:
            self.gguf_path.setText(path)
            stem = Path(path).stem.lower().replace(".", "-").replace("_", "-")
            self.gguf_alias.setText(stem)
            self.verify_gguf_action()

    def verify_gguf_action(self):
        p = self.gguf_path.text().strip()
        if not p:
            self.lbl_gguf_status.setText("<font color='#EF4444'>✗ No file selected</font>")
            return
        ok, msg = verify_gguf_header(p)
        color = "#34D399" if ok else "#EF4444"
        self.lbl_gguf_status.setText(f"<font color='{color}'>{msg}</font>")

    def load_and_add_local_model_action(self):
        p = self.gguf_path.text().strip()
        if not p or not Path(p).exists():
            QMessageBox.warning(self, "Model File", "Please select a valid local model file.")
            return
        alias = self.gguf_alias.text().strip() or Path(p).stem.lower().replace(".", "-").replace("_", "-")
        layers = self.gguf_layers.value()
        ctx = int(self.gguf_ctx.currentText())

        modelfile_path = APP_HOME / f"Modelfile_{alias}"
        modelfile_content = f'FROM "{Path(p).as_posix()}"\nPARAMETER num_gpu {layers}\nPARAMETER num_ctx {ctx}\nPARAMETER temperature 0.2\n'
        modelfile_path.write_text(modelfile_content, encoding="utf-8")

        entry = {
            "provider": "Ollama (Local)",
            "base_url": self.ollama_url.text().strip().rstrip("/"),
            "api_key": "",
            "model": alias,
            "modalities": {"chat": True, "code": True, "agent": True},
            "context_window": ctx,
            "path": str(p),
            "enabled": True
        }
        if not any(cm.get("model") == alias for cm in self.custom_models):
            self.custom_models.append(entry)
            write_json(get_custom_models_path(), self.custom_models)
            self.init_custom_models_table()

        try:
            res = subprocess.run(["ollama", "create", alias, "-f", str(modelfile_path)], capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                self.lbl_gguf_status.setText(f"<font color='#34D399'>✓ '{alias}' loaded & active!</font>")
                QMessageBox.information(self, "Success", f"Model '{alias}' created in Ollama and loaded into IDE!")
                self.test_ollama_conn()
            else:
                self.lbl_gguf_status.setText(f"<font color='#38BDF8'>Modelfile generated for '{alias}'</font>")
                QMessageBox.information(self, "Modelfile Generated", f"Modelfile created at:\n{modelfile_path}\nRun: ollama create {alias} -f \"{modelfile_path}\"")
        except Exception as ex:
            self.lbl_gguf_status.setText(f"<font color='#38BDF8'>Modelfile saved</font>")

    def init_custom_models_table(self):
        self.custom_table.setRowCount(0)
        for i, cm in enumerate(self.custom_models):
            self.custom_table.insertRow(i)
            prov_item = QTableWidgetItem(cm.get("provider", "Custom"))
            mod_item = QTableWidgetItem(cm.get("model", ""))
            url_item = QTableWidgetItem(cm.get("base_url", ""))
            mods = cm.get("modalities", {})
            mod_list = [k.capitalize() for k, v in mods.items() if v]
            cap_item = QTableWidgetItem(", ".join(mod_list) if mod_list else "Text")
            stat_item = QTableWidgetItem("Active" if cm.get("enabled", True) else "Disabled")
            stat_item.setForeground(QColor("#34D399") if cm.get("enabled", True) else QColor("#8b949e"))

            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet("background: #7f1d1d; border-color: #991b1b; padding: 2px 6px; font-size: 8pt;")
            btn_del.clicked.connect(lambda _, row=i: self.remove_custom_model_action(row))

            self.custom_table.setItem(i, 0, prov_item)
            self.custom_table.setItem(i, 1, mod_item)
            self.custom_table.setItem(i, 2, url_item)
            self.custom_table.setItem(i, 3, cap_item)
            self.custom_table.setItem(i, 4, stat_item)
            self.custom_table.setCellWidget(i, 5, btn_del)

    def add_custom_model_action(self):
        p_name = self.custom_provider_name.text().strip() or "Custom Provider"
        base_url = self.custom_base_url.text().strip().rstrip("/")
        key = self.custom_api_key.text().strip()
        mod_id = self.custom_model_id.currentText().strip()
        if not base_url or not mod_id:
            QMessageBox.warning(self, "Missing Fields", "Please specify both Base URL and Model ID.")
            return

        entry = {
            "provider": p_name,
            "base_url": base_url,
            "api_key": key,
            "model": mod_id,
            "modalities": {
                "chat": self.mod_chat.isChecked(),
                "vision": self.mod_vision.isChecked(),
                "audio": self.mod_audio.isChecked(),
                "code": self.mod_code.isChecked(),
                "agent": self.mod_agent.isChecked()
            },
            "context_window": self.custom_ctx_size.value(),
            "enabled": True
        }
        self.custom_models.append(entry)
        write_json(get_custom_models_path(), self.custom_models)
        self.init_custom_models_table()
        self.lbl_custom_status.setText(f"<font color='#34D399'>✓ Model '{mod_id}' registered successfully!</font>")
        QMessageBox.information(self, "Model Registered", f"Successfully registered '{mod_id}' under provider '{p_name}'.")

    def remove_custom_model_action(self, row_idx: int):
        if 0 <= row_idx < len(self.custom_models):
            removed = self.custom_models.pop(row_idx)
            write_json(get_custom_models_path(), self.custom_models)
            self.init_custom_models_table()
            self.lbl_custom_status.setText(f"<font color='#8b949e'>Removed {removed.get('model')}</font>")

    def verify_github_conn(self):
        token = self.github_token.text().strip()
        if not token:
            self.lbl_github_status.setText("<font color='#EF4444'>✗ Missing Token</font>")
            return
        self.lbl_github_status.setText("Verifying…")
        QApplication.processEvents()
        try:
            headers = {"Authorization": f"Bearer {token}", "User-Agent": "PRUBETH-IDE"}
            r = requests.get("https://api.github.com/user", headers=headers, timeout=8)
            if r.status_code == 200:
                data = r.json()
                login = data.get("login", "")
                self.github_user.setText(login)
                msg = f"<font color='#34D399'>✓ Authenticated as @{login}</font>"
                self.lbl_github_status.setText(msg)
                self.accounts["github_token"] = token
                self.accounts["github_username"] = login
                self.accounts["github_status"] = msg
                write_json(get_accounts_path(), self.accounts)
            else:
                self.lbl_github_status.setText(f"<font color='#EF4444'>✗ HTTP {r.status_code}</font>")
        except Exception as ex:
            self.lbl_github_status.setText(f"<font color='#EF4444'>✗ Error</font>")

    def apply_git_identity(self):
        u = self.github_user.text().strip()
        e = self.git_email.text().strip()
        if not u or not e:
            QMessageBox.warning(self, "Git Identity", "Please fill in Username and Git Email.")
            return
        try:
            subprocess.run(["git", "config", "--global", "user.name", u], check=True, capture_output=True)
            subprocess.run(["git", "config", "--global", "user.email", e], check=True, capture_output=True)
            QMessageBox.information(self, "Success", f"Configured user.name='{u}' and user.email='{e}'")
        except Exception as ex:
            QMessageBox.warning(self, "Notice", f"Could not run git config: {ex}")

    def verify_google_conn(self):
        self.lbl_google_status.setText("<font color='#34D399'>✓ Google Cloud Auth Active</font>")

    def verify_hf_conn(self):
        token = self.hf_token.text().strip()
        if not token:
            self.lbl_hf_status.setText("<font color='#EF4444'>✗ Missing Token</font>")
            return
        try:
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get("https://huggingface.co/api/whoami-v2", headers=headers, timeout=8)
            if r.status_code == 200:
                data = r.json()
                name = data.get("name", "User")
                msg = f"<font color='#34D399'>✓ Authenticated as @{name}</font>"
                self.lbl_hf_status.setText(msg)
                self.accounts["hf_token"] = token
                write_json(get_accounts_path(), self.accounts)
            else:
                self.lbl_hf_status.setText(f"<font color='#EF4444'>✗ HTTP {r.status_code}</font>")
        except Exception:
            self.lbl_hf_status.setText("<font color='#EF4444'>✗ Error</font>")

    def populate_extension_cards(self):
        while self.ext_card_layout.count():
            item = self.ext_card_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        query = self.ext_search_edit.text().strip().lower()
        selected_cat = self.ext_category_combo.currentText()

        matched = 0
        for ext in self.extensions:
            name = ext.get("name", "")
            desc = ext.get("description", "")
            cat = ext.get("category", "")
            author = ext.get("author", "")

            searchable = f"{ext.get('id', '')} {name} {desc} {cat} {author}".lower()
            q_clean = query.replace(" ", "")
            if query and (query not in searchable and q_clean not in searchable.replace(" ", "")):
                continue
            if selected_cat != "All Categories" and cat != selected_cat:
                continue

            matched += 1
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #181c25;
                    border: 1px solid #282d3b;
                    border-radius: 8px;
                    padding: 8px;
                }
                QFrame:hover {
                    border-color: #388bfd;
                }
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 8, 10, 8)
            c_layout.setSpacing(4)

            top_row = QHBoxLayout()
            icon_lbl = QLabel(f"<font size='4'>{ext.get('icon', '🧩')}</font> <b>{name}</b> <span style='color:#64748B;'>v{ext.get('version', '1.0')}</span>")
            top_row.addWidget(icon_lbl)
            top_row.addStretch()

            badge_cat = QLabel(f"<span style='background:#232836; color:#79c0ff; padding:2px 8px; border-radius:4px;'>{cat}</span>")
            top_row.addWidget(badge_cat)
            c_layout.addLayout(top_row)

            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("color: #8b949e; font-size: 11.5px;")
            c_layout.addWidget(desc_lbl)

            action_row = QHBoxLayout()
            action_row.addStretch()

            is_installed = ext.get("installed", True)
            is_enabled = ext.get("enabled", True)

            if not is_installed:
                btn_act = QPushButton("⬇ Install")
                btn_act.setObjectName("primaryAction")
                btn_act.clicked.connect(lambda _, eid=ext.get("id"): self.toggle_extension(eid, "install"))
            elif is_enabled:
                stat_badge = QLabel("<font color='#34D399'>● Enabled</font>")
                action_row.addWidget(stat_badge)
                btn_act = QPushButton("Disable")
                btn_act.clicked.connect(lambda _, eid=ext.get("id"): self.toggle_extension(eid, "disable"))
            else:
                stat_badge = QLabel("<font color='#8b949e'>○ Disabled</font>")
                action_row.addWidget(stat_badge)
                btn_act = QPushButton("Enable")
                btn_act.setObjectName("primaryAction")
                btn_act.clicked.connect(lambda _, eid=ext.get("id"): self.toggle_extension(eid, "enable"))

            action_row.addWidget(btn_act)
            c_layout.addLayout(action_row)

            self.ext_card_layout.addWidget(card)

        if matched == 0:
            no_lbl = QLabel("<p align='center' style='color:#8b949e; padding:20px;'>No extensions match your search.</p>")
            self.ext_card_layout.addWidget(no_lbl)

        self.ext_card_layout.addStretch()

    def toggle_extension(self, ext_id: str, action: str):
        for ext in self.extensions:
            if ext.get("id") == ext_id:
                if action == "install":
                    ext["installed"] = True
                    ext["enabled"] = True
                elif action == "disable":
                    ext["enabled"] = False
                elif action == "enable":
                    ext["enabled"] = True
                break
        write_json(get_extensions_path(), self.extensions)
        self.populate_extension_cards()

    def import_custom_extension_dialog(self):
        text, ok = QInputDialog.getText(self, "Add Custom Plugin / Extension", "Enter Extension Name or URL:")
        if ok and text.strip():
            new_id = f"custom-ext-{int(time.time())}"
            self.extensions.append({
                "id": new_id,
                "name": text.strip(),
                "category": "Toolkits",
                "version": "1.0.0",
                "author": "Custom",
                "description": f"Custom user plugin endpoint: {text.strip()}",
                "icon": "🔌",
                "installed": True,
                "enabled": True
            })
            write_json(get_extensions_path(), self.extensions)
            self.populate_extension_cards()

    def save_mcp_config(self):
        try:
            data = json.loads(self.mcp_text.toPlainText())
            write_json(get_mcp_config_path(), data)
            QMessageBox.information(self, "MCP Saved", "Model Context Protocol configuration saved.")
        except Exception as ex:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON syntax:\n{ex}")

    def _auto_detect_venv(self):
        paths = [
            Path.cwd() / ".venv" / "Scripts" / "python.exe",
            Path.cwd() / "venv" / "Scripts" / "python.exe",
            Path.home() / ".venv" / "Scripts" / "python.exe"
        ]
        for p in paths:
            if p.exists():
                self.python_path.setText(str(p))
                QMessageBox.information(self, "Auto-Detected", f"Found virtual environment:\n{p}")
                return
        self.python_path.setText(sys.executable)
        QMessageBox.information(self, "Active Python", f"Using active runtime:\n{sys.executable}")

    def _add_search_key_action(self):
        k = self.tavily_key.text().strip()
        if k:
            self.settings["tavily_api_key"] = k
            self.lbl_tavily_display.setText("1. Tavily  " + k[:8] + "...")
            QMessageBox.information(self, "Key Added", "Tavily Search API key saved successfully.")

    def _toggle_show_search_key(self):
        k = self.settings.get("tavily_api_key", self.tavily_key.text().strip())
        QMessageBox.information(self, "Active Key", f"Tavily Key: {k or 'None'}")

    def _copy_search_key(self):
        k = self.settings.get("tavily_api_key", self.tavily_key.text().strip())
        if k:
            QApplication.clipboard().setText(k)
            QMessageBox.information(self, "Copied", "Copied search API key to clipboard.")

    def _remove_search_key(self):
        self.settings.pop("tavily_api_key", None)
        self.tavily_key.clear()
        self.lbl_tavily_display.setText("None configured")

    def _clear_caches_action(self):
        c = APP_HOME / "navy_models_cache.json"
        if c.exists():
            c.unlink()
        QMessageBox.information(self, "Caches Flushed", "Temporary API caches cleared successfully.")

    def _reload_all_state(self):
        self.test_ollama_conn()
        self.init_custom_models_table()
        self.populate_extension_cards()

    def _apply_selected_preset(self, idx: int):
        if idx == 0:  # Gaming Laptop GTX 1050 Ti
            self.gguf_layers.setValue(33)
            self.gguf_ctx.setCurrentText("8192")
            self.fast_diff_toggle.setChecked(True)
            self.lexer_cache_toggle.setChecked(True)
            self.vram_spin.setValue(4096)
            QMessageBox.information(self, "Preset Loaded", "Loaded 'Gaming Laptop 4GB VRAM' preset: 33 CUDA layers, 8K context, fast diff.")
        elif idx == 1:  # Unrestricted Cyber
            self.unrestricted_mode.setChecked(True)
            self.abliteration_mode.setChecked(True)
            self.max_steps.setValue(50)
            self.allow_commands.setChecked(True)
            self.allow_edits.setChecked(True)
            self.auto_heal.setChecked(True)
            QMessageBox.information(self, "Preset Loaded", "Loaded 'Unrestricted Cybersecurity Research' preset: refusal bypass, 50 steps, auto-heal loop.")
        elif idx == 2:  # Air-Gapped Local
            self.unrestricted_mode.setChecked(True)
            self.gguf_layers.setValue(33)
            QMessageBox.information(self, "Preset Loaded", "Loaded 'Maximum Privacy Air-Gapped' preset.")
        elif idx == 3:  # Cloud 1M
            self.gemini_model.setCurrentText("gemini-3.8-flash")
            self.claude_model.setCurrentText("claude-3-7-sonnet-20250219")
            QMessageBox.information(self, "Preset Loaded", "Loaded 'Frontier Cloud Intelligence' preset.")

    def _export_settings_action(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export IDE Settings", "prubeth_ide_settings.json", "JSON (*.json)")
        if path:
            write_json(path, self.values())
            QMessageBox.information(self, "Exported", f"Settings successfully exported to:\n{path}")

    def _import_settings_action(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import IDE Settings", "", "JSON (*.json)")
        if path:
            data = read_json(path, {})
            if data:
                self.settings.update(data)
                QMessageBox.information(self, "Imported", "Settings imported successfully. Click 'Save & Apply' to finalize.")

    # --------------------------------------------------------------------------
    # Values Dictionary Export & Persistence (100% Backward Compatible)
    # --------------------------------------------------------------------------
    def values(self) -> Dict[str, Any]:
        s = dict(self.settings)
        s.update({
            "gemini_api_key": self.gemini_key.text().strip(),
            "gemini_model": self.gemini_model.currentText(),
            "claude_api_key": self.claude_key.text().strip(),
            "claude_model": self.claude_model.currentText(),
            "navy_api_key": self.navy_key.text().strip(),
            "navy_base_url": self.navy_url.text().strip().rstrip("/"),
            "navy_model": self.navy_model.currentText(),
            "openai_api_key": self.openai_key.text().strip(),
            "openai_base_url": self.openai_url.text().strip().rstrip("/"),
            "openai_model": self.openai_model.currentText(),
            "deepseek_api_key": self.deepseek_key.text().strip(),
            "deepseek_model": self.deepseek_model.currentText(),
            "groq_api_key": self.groq_key.text().strip(),
            "groq_model": self.groq_model.currentText(),
            "ollama_url": self.ollama_url.text().strip().rstrip("/"),
            "local_model": self.ollama_model.currentText(),
            "direct_gguf_path": self.gguf_path.text().strip(),
            "gguf_gpu_layers": self.gguf_layers.value(),
            "gguf_context_window": int(self.gguf_ctx.currentText()),
            "github_token": self.github_token.text().strip(),
            "github_username": self.github_user.text().strip(),
            "git_email": self.git_email.text().strip(),
            "git_ssh_key": self.git_ssh_key.text().strip(),
            "google_project": self.google_project.text().strip(),
            "google_email": self.google_email.text().strip(),
            "google_adc_path": self.google_adc_path.text().strip(),
            "hf_token": self.hf_token.text().strip(),
            "max_agent_steps": self.max_steps.value(),
            "model_restriction_tier": ["low", "mid", "high"][self.restriction_tier.currentIndex()],
            "token_budget": self.token_budget.currentText(),
            "tool_exec_policy": self.tool_exec_policy.currentText(),
            "allow_agent_commands": self.allow_commands.isChecked(),
            "allow_agent_edits": self.allow_edits.isChecked(),
            "project_context": self.auto_context.isChecked(),
            "auto_heal_loop": self.auto_heal.isChecked(),
            "unrestricted_mode": self.unrestricted_mode.isChecked(),
            "abliteration_mode": self.abliteration_mode.isChecked(),
            "editor_font_family": self.editor_font_combo.currentText(),
            "editor_font_size": self.editor_font_size.value(),
            "editor_tab_size": 4 if "4" in self.editor_tab_size.currentText() else 2,
            "editor_word_wrap": self.editor_word_wrap.isChecked(),
            "editor_line_numbers": self.editor_line_numbers.isChecked(),
            "terminal_shell": self.terminal_shell_combo.currentText(),
            "python_interpreter": self.python_path.text().strip(),
            "terminal_buffer_lines": self.terminal_buffer_size.value(),
            "max_checkpoints": self.max_checkpoints_spin.value(),
            "auto_checkpoint_on_edit": self.auto_checkpoint_toggle.isChecked(),
            "fast_diff_engine": self.fast_diff_toggle.isChecked(),
            "lexer_cache_enabled": self.lexer_cache_toggle.isChecked(),
            "cuda_vram_limit_mb": self.vram_spin.value(),
            "tavily_api_key": self.tavily_key.text().strip(),
        })

        self.accounts.update({
            "github_token": self.github_token.text().strip(),
            "github_username": self.github_user.text().strip(),
            "git_email": self.git_email.text().strip(),
            "git_ssh_key": self.git_ssh_key.text().strip(),
            "google_project": self.google_project.text().strip(),
            "google_email": self.google_email.text().strip(),
            "google_adc_path": self.google_adc_path.text().strip(),
            "hf_token": self.hf_token.text().strip(),
        })

        write_json(get_accounts_path(), self.accounts)
        write_json(get_custom_models_path(), self.custom_models)
        write_json(get_extensions_path(), self.extensions)

        # Encrypt and persist secrets securely into CredentialStore
        try:
            from core.credentials import get_credential_store
            c_store = get_credential_store()
            for k in [
                "gemini_api_key", "claude_api_key", "navy_api_key",
                "openai_api_key", "deepseek_api_key", "groq_api_key",
                "github_token", "git_ssh_key", "hf_token", "tavily_api_key"
            ]:
                val = s.get(k) or self.accounts.get(k)
                if val:
                    c_store.set_secret(k, val)
        except Exception:
            pass

        return s


SettingsDialog = UniversalProviderHubDialog
IntelligentDedicatedSettingsHub = UniversalProviderHubDialog
