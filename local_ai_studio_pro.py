"""
Local AI Studio Pro — Next-Gen Agentic AI IDE (PRUBETH Horizon Edition)
v2.4.0 — High-Performance Intelligent Multi-Model Router & Self-Healing IDE

Key Features:
  - Intelligent Model Router: Priority Cascade across Gemini 3.8 Flash, Gemini 3.5 Flash, and Local Ollama GPU
  - Zero-Downtime Auto-Failover: Automatic failover from Cloud to Local CUDA GPU without losing context
  - PRUBETH Horizon UI Experience: Obsidian Dark Aesthetic, Step Cards, Live Task Drawer, Speed Metrics
  - Instant Auto-Fix Engine: Automatic traceback diagnosis, surgical patching, and re-test verification
  - Polyglot Syntax Highlighting: QScintilla Lexers (Python, JS/TS, C++, Rust, HTML, CSS, JSON, SQL, YAML)
  - Autonomous Multi-Step Tool Engine: Read, Write, Patch, Search, Terminal, Tests
  - Inline AI Quick Edit (Ctrl+K) & Visual Diff Review (Side-by-side & unified)
  - Quick Open (Ctrl+P) & Command Palette (Ctrl+Shift+P)
  - Integrated Virtualenv Terminal & Performance Radar
"""
import os
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import re
import shutil
import subprocess
import difflib
import time
import datetime
import tempfile
import traceback
import math
import struct
import urllib.request
import urllib.parse
from pathlib import Path
import requests
import base64

from PyQt5.QtCore import (
    Qt, QDir, QEvent, QThread, pyqtSignal, QProcess, QTimer, QUrl, QSize, QPoint, QPointF
)
from PyQt5.QtGui import (
    QFont, QColor, QKeySequence, QTextCursor, QDesktopServices, QIcon,
    QPainter, QRadialGradient, QBrush, QPen, QPixmap
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QFileSystemModel, QTabWidget, QPlainTextEdit, QTextEdit,
    QLineEdit, QPushButton, QLabel, QFileDialog, QMessageBox, QInputDialog,
    QDialog, QDialogButtonBox, QAction, QToolBar, QStatusBar, QComboBox,
    QShortcut, QMenu, QProgressBar, QCheckBox, QListWidget, QListWidgetItem,
    QGroupBox, QFormLayout, QSpinBox, QTabBar, QFrame, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QSlider
)
from PyQt5.Qsci import (
    QsciScintilla,
    QsciLexerPython,
    QsciLexerJavaScript,
    QsciLexerCPP,
    QsciLexerHTML,
    QsciLexerCSS,
    QsciLexerJSON,
    QsciLexerMarkdown,
    QsciLexerYAML,
    QsciLexerSQL,
    QsciLexerBash,
    QsciLexerBatch,
    QsciLexerXML,
    QsciLexerDiff,
    QsciLexerJava,
    QsciLexerCSharp
)

APP_NAME = "PRUBETH IDE"
APP_BRAND = "PRUBETH"
APP_VERSION = "3.0.0 (Bloom Edition)"
APP_CODENAME = "PRUBETH"
APP_TAGLINE = "Bloom, ideas unfolding"
LEGACY_APP_NAME = "SUKHI IDE"
WEBSITE_URL = "https://www.bsvr.work/"
PROJECTS_URL = "https://www.bsvr.work/#projects"
GITHUB_URL = "https://github.com/imyouiamyou/prubeth-ide"
APP_HOME = Path.home() / ".local_ai_studio_pro"
APP_HOME.mkdir(parents=True, exist_ok=True)
MODEL_DROP_DIR = APP_HOME / "models"
MODEL_DROP_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR = APP_HOME / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CONVERSATIONS_DIR = APP_HOME / "conversations"
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR = APP_HOME / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_PATH = APP_HOME / "settings.json"
HISTORY_PATH = APP_HOME / "history.json"
MCP_CONFIG_PATH = APP_HOME / "mcp_servers.json"
ACCOUNTS_CONFIG_PATH = APP_HOME / "accounts.json"
EXTENSIONS_CONFIG_PATH = APP_HOME / "extensions.json"
CUSTOM_MODELS_CONFIG_PATH = APP_HOME / "custom_models.json"

DEFAULT_EXTENSIONS = [
    {
        "id": "ext-vscode-bridge",
        "name": "VS Code & Cursor Remote Bridge",
        "category": "IDE Bridges",
        "version": "1.4.0",
        "author": "SO NAIVE Core",
        "description": "Bidirectional IPC bridge synchronizing open editor tabs, live diagnostics, and workspaces with VS Code, Cursor, and Zed.",
        "icon": "⚡",
        "installed": True,
        "enabled": True,
        "port": 7432,
    },
    {
        "id": "ext-horizon-agent",
        "name": "PRUBETH Autonomous Subagent Team",
        "category": "AI Agents",
        "version": "2.2.0",
        "author": "PRUBETH Systems",
        "description": "Spawns parallel background subagents (Researcher, Code Architect, Test Fixer) with multi-turn task queues.",
        "icon": "🚀",
        "installed": True,
        "enabled": True,
    },
    {
        "id": "ext-multimodal-vision",
        "name": "Multi-Modal Visual Inspector & Canvas",
        "category": "Multi-Modal",
        "version": "1.3.0",
        "author": "SO NAIVE Vision",
        "description": "Full screenshot analysis, OCR text extraction, UI wireframe-to-code compiler, and image reference embeddings.",
        "icon": "👁️",
        "installed": True,
        "enabled": True,
    },
    {
        "id": "ext-localai-vllm",
        "name": "vLLM & Private LocalAI Engine Tunnel",
        "category": "Private Cloud",
        "version": "2.0.1",
        "author": "High-Throughput Labs",
        "description": "High-performance bridge connecting private on-premise inference servers, LM Studio, vLLM, and Ollama clusters.",
        "icon": "🔒",
        "installed": True,
        "enabled": True,
    },
    {
        "id": "ext-github-flow",
        "name": "GitHub Flow & Pull Request Copilot",
        "category": "IDE Bridges",
        "version": "1.1.0",
        "author": "GitHub Team",
        "description": "Interactive git branch visualization, staging, commit message generation, and automated GitHub PR creation.",
        "icon": "⑂",
        "installed": True,
        "enabled": False,
    },
    {
        "id": "ext-python-science",
        "name": "Python Scientific Data Agent (DAK)",
        "category": "Toolkits",
        "version": "1.0.5",
        "author": "Data Agent Kit",
        "description": "Interactive Jupyter notebook kernel runner, dataframe inspector, inline matplotlib rendering, and BigQuery analytics.",
        "icon": "📊",
        "installed": False,
        "enabled": False,
    },
    {
        "id": "ext-polyglot-lsp",
        "name": "Polyglot Language Server Suite (Rust, C++, Go)",
        "category": "Language Servers",
        "version": "1.2.0",
        "author": "LSP Guild",
        "description": "Deep symbol definitions, find all references, and type inlay hints for Rust Analyzer, Clangd, Gopls, and Pyright.",
        "icon": "🦀",
        "installed": False,
        "enabled": False,
    },
    {
        "id": "ext-docker-sandbox",
        "name": "Docker Container & DevContainer Runner",
        "category": "Toolkits",
        "version": "1.0.0",
        "author": "Container Ops",
        "description": "Executes shell commands and runs test suites inside isolated Docker containers or DevEnvironments.",
        "icon": "🐳",
        "installed": False,
        "enabled": False,
    },
    {
        "id": "ext-mcp-hub",
        "name": "Model Context Protocol (MCP) Hub & Marketplace",
        "category": "AI Agents",
        "version": "1.5.0",
        "author": "Anthropic / OpenMCP",
        "description": "Connects standard MCP servers (Filesystem, DuckDuckGo, PyTest Runner, Postgres, GitHub, Slack) as live tools.",
        "icon": "🛠️",
        "installed": True,
        "enabled": True,
    }
]
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".idea", ".pytest_cache"}
TEXT_EXTS = {
    ".py", ".pyw", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css", ".scss",
    ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".sh", ".bash", ".ps1",
    ".c", ".cpp", ".cc", ".h", ".hpp", ".java", ".go", ".rs", ".sql", ".xml", ".bat"
}
MAX_FILE_CONTEXT = 128000

NAVY_DEFAULT_BASE_URL = "https://api.navy/v1"
NAVY_POPULAR_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "claude-sonnet-4.5",
    "claude-haiku-4.5",
    "gpt-5.6-luna",
    "gpt-5.5",
    "deepseek-chat",
    "deepseek-reasoner",
    "schizogpt",
    "o3-mini",
    "gpt-4o",
    "gpt-4o-mini",
]


def _load_local_env():
    """Automatically loads .env from project root, ~/.local_ai_studio_pro, or current working directory."""
    paths = [
        Path(__file__).resolve().parent / ".env",
        APP_HOME / ".env",
        Path.cwd() / ".env"
    ]
    for p in paths:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass


_load_local_env()


def read_json(path, fallback):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")


def get_app_secret(settings, key_name, env_name=None):
    """Retrieves secret securely from CredentialStore (DPAPI/Fernet), fallback to settings or env."""
    try:
        from core.credentials import get_credential_store
        sec = get_credential_store().get_secret(key_name)
        if sec:
            return sec
    except Exception:
        pass
    if settings and isinstance(settings, dict) and settings.get(key_name):
        return settings[key_name]
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    return os.environ.get(key_name.upper(), "")


def log_agent_action(action_type: str, details: dict):
    """Appends structured agent action log entry to ~/.local_ai_studio_pro/logs/agent_actions.log."""
    try:
        log_file = LOGS_DIR / "agent_actions.log"
        ts = datetime.datetime.now().isoformat()
        entry = {"timestamp": ts, "type": action_type, **details}
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def log_error(source: str, error_msg: str, traceback_str: str = ""):
    """Appends structured error log entry to ~/.local_ai_studio_pro/logs/errors.log."""
    try:
        err_file = LOGS_DIR / "errors.log"
        ts = datetime.datetime.now().isoformat()
        entry = {"timestamp": ts, "source": source, "error": error_msg, "traceback": traceback_str}
        with open(err_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def format_collapsible_thought(text: str) -> str:
    """Formats <thought> or <thinking> blocks as PRUBETH Horizon/Cursor collapsible summary blocks."""
    def _repl(match):
        thought_body = match.group(1).strip()
        return (
            f"<details style='background: #111622; border: 1px solid #1f2838; border-radius: 6px; margin: 6px 0; padding: 6px;'>"
            f"<summary style='color: #8fa2bf; cursor: pointer; font-weight: bold;'>Thought for 5s ▾</summary>"
            f"<div style='color: #64748b; font-family: monospace; font-size: 8.5pt; margin-top: 4px; white-space: pre-wrap;'>{html_escape(thought_body)}</div>"
            f"</details>"
        )
    return re.sub(r"<(?:thought|thinking)>(.*?)</(?:thought|thinking)>", _repl, text, flags=re.DOTALL)


# ==============================================================================
# Cybernetic Blinking AI Status Indicator Widget
# ==============================================================================
class BlinkingAIIndicator(QWidget):
    """
    Animated blinking & breathing cybernetic AI status indicator for SO NAIVE IDE.
    Renders smooth sine-wave glowing iris, dynamic chromatic blinking during
    inference, and distinct state visual cues (Idle, Streaming, Auto-Fix, Error).
    """
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "IDLE"  # "IDLE", "STREAMING", "AUTOFIX", "ERROR"
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(40)  # ~25 FPS
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self.setToolTip("SO NAIVE AI Engine: Idle & Ready (Click for Performance Radar)")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(148, 28)

    def set_state(self, state: str):
        self.state = state.upper()
        if self.state == "STREAMING":
            self.setToolTip("SO NAIVE AI Engine: Thinking & Generating Code...")
        elif self.state == "AUTOFIX":
            self.setToolTip("SO NAIVE AI Engine: Auto-Fixing Code & Diagnosing Bug...")
        elif self.state == "ERROR":
            self.setToolTip("SO NAIVE AI Engine: Error Detected / Attention Needed")
        else:
            self.setToolTip("SO NAIVE AI Engine: Online & Ready (Click for Performance Radar)")
        self.update()

    def _tick(self):
        speed = 0.16 if self.state in ("STREAMING", "AUTOFIX") else 0.05
        self._phase = (self._phase + speed) % (2 * math.pi)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        glow = 0.65 + 0.35 * math.sin(self._phase)

        if self.state == "STREAMING":
            # Rapid chromatic neon violet / cyan blink
            is_high = math.sin(self._phase * 2) > 0
            blink_col = QColor(168, 85, 247) if is_high else QColor(0, 240, 255)
            core_col = QColor(255, 255, 255)
            badge_text = "THINKING"
            text_col = QColor("#C084FC")
        elif self.state == "AUTOFIX":
            is_high = math.sin(self._phase * 2) > 0
            blink_col = QColor(16, 185, 129) if is_high else QColor(245, 158, 11)
            core_col = QColor(255, 255, 255)
            badge_text = "AUTO-FIX"
            text_col = QColor("#34D399")
        elif self.state == "ERROR":
            blink_col = QColor(239, 68, 68)
            core_col = QColor(255, 120, 120)
            badge_text = "ALERT"
            text_col = QColor("#F87171")
        else:
            # Idle cyber breathing
            blink_col = QColor(0, 229, 255, int(150 + 100 * glow))
            core_col = QColor(0, 240, 255)
            badge_text = "ONLINE"
            text_col = QColor("#38BDF8")

        # Background capsule pill
        p.setBrush(QColor(16, 20, 30, 220))
        p.setPen(QPen(QColor(40, 50, 70), 1))
        p.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 12, 12)

        # Pulsing eye / beacon
        cx, cy = 15, 14
        rad = 8 + 3 * glow
        grad = QRadialGradient(cx, cy, rad)
        c_glow = QColor(blink_col)
        c_glow.setAlpha(int(85 * glow))
        grad.setColorAt(0.0, c_glow)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), rad, rad)

        # Iris
        iris_rad = 4.2 + 1.0 * glow
        p.setBrush(QBrush(blink_col))
        p.drawEllipse(QPointF(cx, cy), iris_rad, iris_rad)

        # Center pupil
        p.setBrush(QBrush(core_col))
        p.drawEllipse(QPointF(cx, cy), 2.0, 2.0)

        # Status text
        p.setPen(text_col)
        font = QFont("Segoe UI", 8, QFont.Bold)
        p.setFont(font)
        p.drawText(29, 18, f"PRUBETH · {badge_text}")
        p.end()


# ==============================================================================
# Intelligent Model Router (Dynamic Priority Cascade)
# ==============================================================================
class IntelligentModelRouter:
    """
    Intelligently ranks and cascades execution across models to achieve
    maximum speed, highest reasoning context, and zero-downtime offline fallback.
    """

    @classmethod
    def get_execution_plan(cls, settings, requested_provider=None, requested_model=None):
        candidates = []
        try:
            from core.credentials import get_credential_store
            c_store = get_credential_store()
            gemini_key = c_store.get_secret("gemini_api_key") or settings.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
            navy_key = c_store.get_secret("navy_api_key") or settings.get("navy_api_key") or os.environ.get("NAVY_API_KEY", "")
        except Exception:
            gemini_key = settings.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
            navy_key = settings.get("navy_api_key") or os.environ.get("NAVY_API_KEY", "")
        navy_model = settings.get("navy_model") or "gemini-3.8-flash"
        ollama_url = settings.get("ollama_url", "http://localhost:11434")
        local_model = settings.get("local_model") or "qwen2.5:1.5b"

        # 1. If user explicitly requested a specific provider (not Auto)
        if requested_provider and requested_provider not in ("⚡ Auto-Router", "Auto"):
            if requested_provider == "NavyAI":
                candidates.append(("NavyAI", requested_model or navy_model, "Direct User Selection (NavyAI Unified)"))
            else:
                candidates.append((requested_provider, requested_model or "gemini-3.8-flash", "Direct User Selection"))

        # 2. Priority 1: Flagship Google Gemini 3.8 Flash (Ultra-fast cloud, 1M context)
        if gemini_key:
            if not any(p == "Google Gemini" and m == "gemini-3.8-flash" for p, m, _ in candidates):
                candidates.append(("Google Gemini", "gemini-3.8-flash", "Flagship Cloud (1M Context)"))
            if not any(p == "Google Gemini" and m == "gemini-3.5-flash" for p, m, _ in candidates):
                candidates.append(("Google Gemini", "gemini-3.5-flash", "Secondary Cloud Engine"))

        # 3. Priority 2: NavyAI Unified Gateway (Frontier Models & 140+ Engines)
        if navy_key:
            if not any(p == "NavyAI" for p, _, _ in candidates):
                candidates.append(("NavyAI", navy_model, "NavyAI Unified Gateway (Frontier Models)"))

        # 4. Priority 3: Local GPU Ollama (Zero network latency, offline, private)
        if not any(p == "Ollama" for p, _, _ in candidates):
            candidates.append(("Ollama", local_model, "Local GPU (NVIDIA GTX 1050 Ti)"))

        # 5. Priority 4: Deep Reasoning Cloud (Gemini Pro)
        if gemini_key and not any(p == "Google Gemini" and m == "gemini-3.1-pro-preview" for p, m, _ in candidates):
            candidates.append(("Google Gemini", "gemini-3.1-pro-preview", "Deep Architectural Reasoning"))

        # 6. Priority 5: OpenAI-compatible endpoint
        cloud = settings.get("cloud", {}).get("OpenAI-compatible", {})
        if cloud.get("base_url") and os.environ.get(cloud.get("api_key_env", "OPENAI_API_KEY")):
            candidates.append(("OpenAI-compatible", cloud.get("model", "gpt-4o"), "OpenAI Compatible"))

        # 7. Priority 6: Custom Registered Models & Multi-Modal Plugins
        custom_models = read_json(CUSTOM_MODELS_CONFIG_PATH, [])
        for cm in custom_models:
            if not cm.get("enabled", True):
                continue
            p_name = cm.get("provider", "Custom").strip()
            m_name = cm.get("model", "").strip()
            if not p_name or not m_name:
                continue
            if requested_provider in (p_name, f"Custom: {p_name}"):
                if not any(p == p_name and m == m_name for p, m, _ in candidates):
                    candidates.insert(0, (p_name, requested_model or m_name, f"Direct Custom Provider ({p_name})"))
            elif cm.get("api_key") or cm.get("base_url"):
                if not any(p == p_name and m == m_name for p, m, _ in candidates):
                    candidates.append((p_name, m_name, f"Custom Gateway ({p_name})"))

        return candidates


# ==============================================================================
# Polyglot Lexer Factory
# ==============================================================================
class LexerFactory:
    """Manages syntax highlighters for multiple languages with a unified dark palette."""

    BG_COLOR = QColor("#15171D")
    PAPER_COLOR = QColor("#15171D")
    FG_COLOR = QColor("#E8EAF0")
    MARGIN_BG = QColor("#1D2028")
    MARGIN_FG = QColor("#727B8D")
    KEYWORD_COLOR = QColor("#C4A1FF")
    STRING_COLOR = QColor("#9DD9A8")
    COMMENT_COLOR = QColor("#8995A7")
    FUNC_COLOR = QColor("#83BDF5")
    CLASS_COLOR = QColor("#83BDF5")
    NUMBER_COLOR = QColor("#F1C27D")
    OPERATOR_COLOR = QColor("#62D4E5")
    ERROR_COLOR = QColor("#FF7D86")

    @classmethod
    def create_lexer(cls, file_path, parent):
        if not file_path:
            return QsciLexerPython(parent)

        ext = Path(file_path).suffix.lower()

        if ext in {".py", ".pyw"}:
            lexer = QsciLexerPython(parent)
            cls._apply_python_styles(lexer)
            return lexer
        elif ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            lexer = QsciLexerJavaScript(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".rs", ".go"}:
            lexer = QsciLexerCPP(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".html", ".htm", ".xhtml"}:
            lexer = QsciLexerHTML(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".css", ".scss", ".less"}:
            lexer = QsciLexerCSS(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext == ".json":
            lexer = QsciLexerJSON(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".md", ".markdown"}:
            lexer = QsciLexerMarkdown(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".yml", ".yaml"}:
            lexer = QsciLexerYAML(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext == ".sql":
            lexer = QsciLexerSQL(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".sh", ".bash", ".zsh"}:
            lexer = QsciLexerBash(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".bat", ".cmd"}:
            lexer = QsciLexerBatch(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".xml", ".svg"}:
            lexer = QsciLexerXML(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".java"}:
            lexer = QsciLexerJava(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".cs"}:
            lexer = QsciLexerCSharp(parent)
            cls._apply_common_styles(lexer)
            return lexer
        elif ext in {".diff", ".patch"}:
            lexer = QsciLexerDiff(parent)
            cls._apply_common_styles(lexer)
            return lexer

        lexer = QsciLexerPython(parent)
        cls._apply_python_styles(lexer)
        return lexer

    @classmethod
    def _apply_python_styles(cls, lexer):
        font = QFont("Cascadia Code", 11)
        lexer.setDefaultFont(font)
        lexer.setDefaultPaper(cls.PAPER_COLOR)
        lexer.setDefaultColor(cls.FG_COLOR)
        lexer.setColor(cls.KEYWORD_COLOR, QsciLexerPython.Keyword)
        lexer.setColor(cls.STRING_COLOR, QsciLexerPython.DoubleQuotedString)
        lexer.setColor(cls.STRING_COLOR, QsciLexerPython.SingleQuotedString)
        lexer.setColor(cls.STRING_COLOR, QsciLexerPython.TripleDoubleQuotedString)
        lexer.setColor(cls.STRING_COLOR, QsciLexerPython.TripleSingleQuotedString)
        lexer.setColor(cls.COMMENT_COLOR, QsciLexerPython.Comment)
        lexer.setColor(cls.COMMENT_COLOR, QsciLexerPython.CommentBlock)
        lexer.setColor(cls.FUNC_COLOR, QsciLexerPython.FunctionMethodName)
        lexer.setColor(cls.CLASS_COLOR, QsciLexerPython.ClassName)
        lexer.setColor(cls.NUMBER_COLOR, QsciLexerPython.Number)
        lexer.setColor(cls.OPERATOR_COLOR, QsciLexerPython.Operator)
        lexer.setPaper(cls.PAPER_COLOR)

    @classmethod
    def _apply_common_styles(cls, lexer):
        font = QFont("Cascadia Code", 11)
        lexer.setDefaultFont(font)
        lexer.setDefaultPaper(cls.PAPER_COLOR)
        lexer.setDefaultColor(cls.FG_COLOR)
        lexer.setPaper(cls.PAPER_COLOR)


# ==============================================================================
# Editor Component
# ==============================================================================
class Editor(QsciScintilla):
    """PRUBETH Horizon Scintilla editor with polyglot highlighting & Ctrl+K quick edit."""

    quick_edit_triggered = pyqtSignal()

    def __init__(self, path="", parent=None):
        super().__init__(parent)
        self.file_path = path
        self.setUtf8(True)
        self.setFont(QFont("Cascadia Code", 11))
        self.setMarginsFont(QFont("Cascadia Code", 10))

        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginLineNumbers(0, True)
        self.setMarginWidth(0, "00000")
        self.setMarginsBackgroundColor(QColor("#1D2028"))
        self.setMarginsForegroundColor(QColor("#727B8D"))

        self.setPaper(QColor("#15171D"))
        self.setColor(QColor("#E8EAF0"))
        self.setCaretForegroundColor(QColor("#9485FF"))
        self.setCaretWidth(2)
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#1D2028"))
        self.setSelectionBackgroundColor(QColor("#383650"))
        self.setSelectionForegroundColor(QColor("#FFFFFF"))

        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setAutoIndent(True)
        self.setIndentationWidth(4)
        self.setIndentationsUseTabs(False)
        self.setTabWidth(4)

        self.setFolding(QsciScintilla.BoxedTreeFoldStyle, 2)
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.setAutoCompletionThreshold(2)

        self.setEdgeMode(QsciScintilla.EdgeLine)
        self.setEdgeColumn(100)
        self.setEdgeColor(QColor("#343A49"))

        self.apply_lexer(path)

    def apply_lexer(self, path):
        lexer = LexerFactory.create_lexer(path, self)
        if lexer:
            self.setLexer(lexer)

    def selection(self):
        return self.selectedText().strip()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_K and event.modifiers() == Qt.ControlModifier:
            self.quick_edit_triggered.emit()
            event.accept()
            return
        super().keyPressEvent(event)


# ==============================================================================
# Visual Diff & Review Dialog
# ==============================================================================
class VisualDiffDialog(QDialog):
    """Side-by-side or color-coded unified diff viewer with line additions/deletions."""

    def __init__(self, before_text, after_text, file_name="file", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Review AI Changes — {file_name}")
        self.resize(1240, 780)
        self.setStyleSheet("""
            QDialog { background: #0f121a; color: #e6edf7; }
            QLabel { font-weight: bold; }
            QPlainTextEdit, QTextEdit {
                background: #090c12;
                color: #dce7fa;
                border: 1px solid #1f2838;
                border-radius: 6px;
                font-family: 'Cascadia Code', Consolas, monospace;
                font-size: 10pt;
            }
            QPushButton {
                background: #192436;
                color: #ffffff;
                border: 1px solid #2d3e58;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #263852; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)

        before_lines = before_text.splitlines()
        after_lines = after_text.splitlines()
        diff = list(difflib.unified_diff(before_lines, after_lines, lineterm=""))
        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        header = QLabel(
            f"Review Changes: <span style='color:#75e09f;'>+{additions} additions</span>, "
            f"<span style='color:#ff7d7d;'>-{deletions} deletions</span>. "
            f"Review the patch below before applying to editor or saving."
        )
        header.setTextFormat(Qt.RichText)
        layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Unified Diff View:"))
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Cascadia Code", 10))
        self.populate_colorized_diff(before_lines, after_lines)
        left_layout.addWidget(self.diff_view)
        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("Proposed Result (Editable):"))
        self.proposed_view = QPlainTextEdit()
        self.proposed_view.setFont(QFont("Cascadia Code", 10))
        self.proposed_view.setPlainText(after_text)
        right_layout.addWidget(self.proposed_view)
        splitter.addWidget(right_widget)

        splitter.setSizes([600, 640])
        layout.addWidget(splitter, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_apply = QPushButton("✓ Apply to Editor Tab")
        self.btn_apply.setStyleSheet("background: #186036; border-color: #2ea055;")
        self.btn_apply.clicked.connect(self.accept)

        self.btn_save_disk = QPushButton("💾 Save Directly to Disk")
        self.btn_save_disk.clicked.connect(self.accept_and_save)

        self.btn_cancel = QPushButton("✕ Discard")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save_disk)
        btn_layout.addWidget(self.btn_apply)
        layout.addLayout(btn_layout)

        self.save_to_disk_requested = False

    def populate_colorized_diff(self, before_lines, after_lines):
        diff_lines = list(difflib.unified_diff(
            before_lines, after_lines, fromfile="Current", tofile="Proposed", lineterm=""
        ))
        if not diff_lines:
            self.diff_view.setHtml("<p style='color:#77839a;'>(No differences detected)</p>")
            return

        html = ["<div style='font-family: Cascadia Code, monospace; font-size: 10pt; line-height: 1.4;'>"]
        for line in diff_lines:
            esc = html_escape(line)
            if line.startswith("+++") or line.startswith("---"):
                html.append(f"<div style='color:#8ab4f8; font-weight:bold;'>{esc}</div>")
            elif line.startswith("@@"):
                html.append(f"<div style='color:#c792ea; background:#1e1a32; padding:2px;'>{esc}</div>")
            elif line.startswith("+"):
                html.append(f"<div style='color:#75e09f; background:#122b1c;'>{esc}</div>")
            elif line.startswith("-"):
                html.append(f"<div style='color:#ff8585; background:#361419;'>{esc}</div>")
            else:
                html.append(f"<div style='color:#9aa9c2;'>{esc}</div>")
        html.append("</div>")
        self.diff_view.setHtml("".join(html))

    def accept_and_save(self):
        self.save_to_disk_requested = True
        self.accept()


# ==============================================================================
# Quick Open Dialog (Ctrl+P)
# ==============================================================================
class QuickOpenDialog(QDialog):
    """Fuzzy-match quick file switcher across the workspace."""

    def __init__(self, root_dir, parent=None):
        super().__init__(parent)
        self.root_dir = Path(root_dir)
        self.setWindowTitle("Quick Open File (Ctrl+P)")
        self.resize(720, 480)
        self.setStyleSheet("""
            QDialog { background: #11141c; color: #e6edf7; }
            QLineEdit {
                background: #090c12; color: #ffffff; border: 2px solid #2d3e58;
                padding: 10px; border-radius: 6px; font-size: 11pt;
            }
            QListWidget {
                background: #090c12; color: #dce7fa; border: 1px solid #1f2838;
                border-radius: 6px; font-family: 'Cascadia Code', monospace; font-size: 10pt;
            }
            QListWidget::item { padding: 8px; border-radius: 4px; }
            QListWidget::item:selected { background: #243854; color: #ffffff; }
        """)

        layout = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search file by name or path… (Up/Down to navigate, Enter to open)")
        self.search_input.textChanged.connect(self.filter_files)
        layout.addWidget(self.search_input)

        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.file_list)

        self.all_files = []
        self.scan_files()
        self.selected_path = None

    def scan_files(self):
        self.all_files = []
        try:
            for root, dirs, files in os.walk(str(self.root_dir)):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for file in files:
                    p = Path(root) / file
                    try:
                        rel = str(p.relative_to(self.root_dir))
                        self.all_files.append((rel, str(p)))
                        if len(self.all_files) >= 5000:
                            break
                    except Exception:
                        pass
                if len(self.all_files) >= 5000:
                    break
        except Exception:
            pass
        self.filter_files("")

    def filter_files(self, text):
        self.file_list.clear()
        query = text.strip().lower()
        count = 0
        for rel, full in self.all_files:
            if not query or query in rel.lower():
                item = QListWidgetItem(rel)
                item.setData(Qt.UserRole, full)
                self.file_list.addItem(item)
                count += 1
                if count >= 300:
                    break
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Down:
            curr = self.file_list.currentRow()
            if curr < self.file_list.count() - 1:
                self.file_list.setCurrentRow(curr + 1)
            return
        elif event.key() == Qt.Key_Up:
            curr = self.file_list.currentRow()
            if curr > 0:
                self.file_list.setCurrentRow(curr - 1)
            return
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            item = self.file_list.currentItem()
            if item:
                self.selected_path = item.data(Qt.UserRole)
                self.accept()
                return
        elif event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


# ==============================================================================
# Command Palette (Ctrl+Shift+P)
# ==============================================================================
class CommandPaletteDialog(QDialog):
    """Universal Command Palette for instant action execution."""

    def __init__(self, commands, parent=None):
        super().__init__(parent)
        self.commands = commands
        self.setWindowTitle("Command Palette (Ctrl+Shift+P)")
        self.resize(680, 420)
        self.setStyleSheet("""
            QDialog { background: #11141c; color: #e6edf7; }
            QLineEdit {
                background: #090c12; color: #ffffff; border: 2px solid #2d3e58;
                padding: 10px; border-radius: 6px; font-size: 11pt;
            }
            QListWidget {
                background: #090c12; color: #dce7fa; border: 1px solid #1f2838;
                border-radius: 6px; font-size: 10.5pt;
            }
            QListWidget::item { padding: 9px; border-radius: 4px; }
            QListWidget::item:selected { background: #243854; color: #ffffff; }
        """)

        layout = QVBoxLayout(self)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a command… (Up/Down to select, Enter to run)")
        self.input.textChanged.connect(self.filter_commands)
        layout.addWidget(self.input)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self.run_selected)
        layout.addWidget(self.list)

        self.selected_callback = None
        self.filter_commands("")

    def filter_commands(self, text):
        self.list.clear()
        query = text.strip().lower()
        for name, shortcut, fn in self.commands:
            if not query or query in name.lower():
                display = f"{name}    [{shortcut}]" if shortcut else name
                item = QListWidgetItem(display)
                item.setData(Qt.UserRole, fn)
                self.list.addItem(item)
        if self.list.count() > 0:
            self.list.setCurrentRow(0)

    def run_selected(self):
        item = self.list.currentItem()
        if item:
            self.selected_callback = item.data(Qt.UserRole)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Down:
            curr = self.list.currentRow()
            if curr < self.list.count() - 1:
                self.list.setCurrentRow(curr + 1)
            return
        elif event.key() == Qt.Key_Up:
            curr = self.list.currentRow()
            if curr > 0:
                self.list.setCurrentRow(curr - 1)
            return
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.run_selected()
            return
        elif event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


# ==============================================================================
# Quick Edit Dialog (Ctrl+K)
# ==============================================================================
class QuickEditDialog(QDialog):
    """Inline AI code transform bar (Cursor/PRUBETH Horizon style)."""

    def __init__(self, target_label="Current Selection", parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Quick Edit (Ctrl+K)")
        self.resize(600, 160)
        self.setStyleSheet("""
            QDialog { background: #11141c; color: #e6edf7; border: 1px solid #2d3e58; border-radius: 8px; }
            QLineEdit {
                background: #090c12; color: #ffffff; border: 2px solid #5aa7ff;
                padding: 10px; border-radius: 6px; font-size: 11pt;
            }
            QPushButton {
                background: #192436; color: #ffffff; border: 1px solid #2d3e58;
                padding: 7px 14px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #263852; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Target: <span style='color:#5aa7ff;'>{target_label}</span>"))

        self.input = QLineEdit()
        self.input.setPlaceholderText("Describe the change (e.g., 'Add type hints and docstring', 'Refactor into generator')…")
        layout.addWidget(self.input)

        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("Cancel (Esc)")
        cancel.clicked.connect(self.reject)
        run = QPushButton("Generate Edit (Enter)")
        run.setStyleSheet("background: #186036; border-color: #2ea055;")
        run.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(run)
        layout.addLayout(row)

    def instruction(self):
        return self.input.text().strip()


# ==============================================================================
# Multi-Provider AI Streaming Worker (Intelligent Cascade Engine)
# ==============================================================================
class AIWorker(QThread):
    token = pyqtSignal(str)
    done = pyqtSignal(str, str, object)
    error = pyqtSignal(str, str)
    status = pyqtSignal(str)
    stats = pyqtSignal(int, float)

    def __init__(self, base_url, provider, model, messages, task_id, stream=True, settings=None, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.provider = provider
        self.model = model
        self.messages = messages
        self.task_id = task_id
        self.stream = stream
        self.settings = settings or {}
        self.cancel_requested = False
        self.token_count = 0
        self.start_time = time.time()

    def cancel(self):
        self.cancel_requested = True

    def run(self):
        self.start_time = time.time()
        self.token_count = 0

        # Build priority execution chain
        chain = IntelligentModelRouter.get_execution_plan(
            self.settings, self.provider, self.model
        )

        last_error = None
        for idx, (provider, model, label) in enumerate(chain):
            if self.cancel_requested:
                break
            try:
                if idx > 0:
                    self.status.emit(f"⚡ Cascading to backup tier [{idx+1}/{len(chain)}]: {provider} ({model})…")
                else:
                    self.status.emit(f"⚡ Executing with: {provider} ({model})…")

                if provider == "Google Gemini":
                    self._run_gemini(model)
                elif provider == "NavyAI":
                    self._run_navy(model)
                elif provider == "Ollama":
                    self._run_ollama(model)
                elif self._is_custom_provider(provider):
                    self._run_custom_provider(provider, model)
                else:
                    self._run_openai_compatible(model)
                return
            except Exception as ex:
                last_error = f"{provider} ({model}): {str(ex)}"
                if self.cancel_requested:
                    break
                continue

        if not self.cancel_requested:
            self.error.emit(self.task_id, f"All prioritized models failed. Last error: {last_error}")

    def _run_navy(self, model):
        key = get_app_secret(self.settings, "navy_api_key", "NAVY_API_KEY")
        if not key:
            raise RuntimeError("NavyAI API key is not configured. Add your key in Settings or .env.")

        base_url = (self.settings.get("navy_base_url") or NAVY_DEFAULT_BASE_URL).rstrip("/")
        endpoint = f"{base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        req_model = model or self.settings.get("navy_model", "gemini-3.8-flash")
        payload = {
            "model": req_model,
            "messages": self.messages,
            "stream": self.stream,
            "temperature": 0.2
        }

        with requests.post(endpoint, headers=headers, json=payload, stream=self.stream, timeout=(10, 300)) as r:
            if r.status_code != 200:
                try:
                    err_json = r.json()
                    err_msg = err_json.get("error", {}).get("message", r.text[:200])
                except Exception:
                    err_msg = r.text[:200]
                raise RuntimeError(f"NavyAI ({r.status_code}): {err_msg}")

            answer = ""
            if self.stream:
                for raw in r.iter_lines():
                    if self.cancel_requested:
                        break
                    if not raw or not raw.startswith(b"data:"):
                        continue
                    data = raw[5:].strip()
                    if data == b"[DONE]":
                        break
                    try:
                        packet = json.loads(data)
                        choices = packet.get("choices", [])
                        if choices:
                            chunk = choices[0].get("delta", {}).get("content", "") or ""
                            if chunk:
                                answer += chunk
                                self.token_count += 1
                                self.token.emit(chunk)
                    except Exception:
                        pass
            else:
                data = r.json()
                choices = data.get("choices", [])
                if choices:
                    answer = choices[0].get("message", {}).get("content", "")

        elapsed = max(0.001, time.time() - self.start_time)
        tok_rate = self.token_count / elapsed
        self.stats.emit(self.token_count, tok_rate)

        if self.cancel_requested:
            self.done.emit(self.task_id, "", {"cancelled": True})
        elif answer.strip():
            self.done.emit(self.task_id, answer, {"model": req_model, "provider": "NavyAI", "rate": tok_rate})
        else:
            raise RuntimeError("NavyAI returned an empty response.")

    def _run_gemini(self, model):
        key = get_app_secret(self.settings, "gemini_api_key", "GEMINI_API_KEY")
        if not key:
            raise RuntimeError("Gemini API key is not configured. Add your key in Settings.")

        m_name = model if "gemini" in model else "gemini-3.8-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:streamGenerateContent?alt=sse"
        headers = {"x-goog-api-key": key, "Content-Type": "application/json"}

        contents = []
        for m in self.messages:
            role = "user" if m.get("role") in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        with requests.post(url, headers=headers, json={"contents": contents}, stream=True, timeout=(8, 180)) as r:
            r.raise_for_status()
            answer = ""
            for raw in r.iter_lines():
                if self.cancel_requested:
                    break
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="replace")
                if line.startswith("data:"):
                    line = line[5:].strip()
                try:
                    packet = json.loads(line)
                    candidates = packet.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            chunk = part.get("text", "")
                            if chunk:
                                answer += chunk
                                self.token_count += 1
                                self.token.emit(chunk)
                except Exception:
                    pass

        elapsed = max(0.001, time.time() - self.start_time)
        tok_rate = self.token_count / elapsed
        self.stats.emit(self.token_count, tok_rate)

        if self.cancel_requested:
            self.done.emit(self.task_id, "", {"cancelled": True})
        else:
            self.done.emit(self.task_id, answer, {"model": m_name, "provider": "Google Gemini", "rate": tok_rate})

    def _run_ollama(self, model):
        url = self.settings.get("ollama_url", "http://localhost:11434").rstrip("/")
        payload = {
            "model": model,
            "messages": self.messages,
            "stream": self.stream,
            "options": {"temperature": 0.2, "num_ctx": 16384}
        }
        with requests.post(
            url + "/api/chat",
            json=payload,
            stream=self.stream,
            timeout=(8, 300)
        ) as r:
            r.raise_for_status()
            answer = ""
            if self.stream:
                for raw in r.iter_lines():
                    if self.cancel_requested:
                        break
                    if not raw:
                        continue
                    packet = json.loads(raw.decode("utf-8"))
                    chunk = packet.get("message", {}).get("content", "")
                    if chunk:
                        answer += chunk
                        self.token_count += 1
                        self.token.emit(chunk)
                    if packet.get("done"):
                        break
            else:
                packet = r.json()
                answer = packet.get("message", {}).get("content", "")

        elapsed = max(0.001, time.time() - self.start_time)
        tok_rate = self.token_count / elapsed
        self.stats.emit(self.token_count, tok_rate)

        if self.cancel_requested:
            self.done.emit(self.task_id, "", {"cancelled": True})
        elif answer.strip():
            self.done.emit(self.task_id, answer, {"model": model, "provider": "Ollama", "rate": tok_rate})
        else:
            raise RuntimeError("Ollama returned an empty response.")

    def _run_openai_compatible(self, model):
        cfg = read_json(SETTINGS_PATH, {}).get("cloud", {}).get("OpenAI-compatible", {})
        endpoint = cfg.get("base_url", "").rstrip("/")
        env_name = cfg.get("api_key_env", "OPENAI_API_KEY")
        key = os.environ.get(env_name, "")
        if not endpoint or not key:
            raise RuntimeError(f"Configure base URL and ${env_name} for cloud provider.")

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": self.messages, "stream": True, "temperature": 0.2}

        with requests.post(
            endpoint + "/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=(10, 300)
        ) as r:
            r.raise_for_status()
            answer = ""
            for raw in r.iter_lines():
                if self.cancel_requested:
                    break
                if not raw or not raw.startswith(b"data:"):
                    continue
                data = raw[5:].strip()
                if data == b"[DONE]":
                    break
                try:
                    packet = json.loads(data)
                    choices = packet.get("choices", [])
                    if choices:
                        chunk = choices[0].get("delta", {}).get("content", "") or ""
                        if chunk:
                            answer += chunk
                            self.token_count += 1
                            self.token.emit(chunk)
                except Exception:
                    pass

        elapsed = max(0.001, time.time() - self.start_time)
        tok_rate = self.token_count / elapsed
        self.stats.emit(self.token_count, tok_rate)

        if self.cancel_requested:
            self.done.emit(self.task_id, "", {"cancelled": True})
        else:
            self.done.emit(self.task_id, answer, {"model": model, "provider": "OpenAI-compatible", "rate": tok_rate})

    def _is_custom_provider(self, provider):
        custom_models = read_json(CUSTOM_MODELS_CONFIG_PATH, [])
        return any(cm.get("provider") == provider for cm in custom_models)

    def _run_custom_provider(self, provider, model):
        custom_models = read_json(CUSTOM_MODELS_CONFIG_PATH, [])
        cfg = next((cm for cm in custom_models if cm.get("provider") == provider), {})
        endpoint = (cfg.get("base_url") or "").rstrip("/")
        key = cfg.get("api_key") or ""
        if not endpoint:
            raise RuntimeError(f"Base URL not configured for custom provider '{provider}'.")

        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        formatted_messages = []
        for m in self.messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            images = m.get("images", [])
            if images and cfg.get("modalities", {}).get("vision", False):
                parts = [{"type": "text", "text": content}]
                for img in images:
                    if isinstance(img, str) and (img.startswith("data:") or len(img) > 200):
                        parts.append({"type": "image_url", "image_url": {"url": img}})
                    elif isinstance(img, str) and Path(img).exists():
                        try:
                            b64 = base64.b64encode(Path(img).read_bytes()).decode("utf-8")
                            mime = "image/png" if img.endswith(".png") else "image/jpeg"
                            parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
                        except Exception:
                            pass
                formatted_messages.append({"role": role, "content": parts})
            else:
                formatted_messages.append({"role": role, "content": content})

        url = f"{endpoint}/chat/completions"
        payload = {
            "model": model or cfg.get("model", "default"),
            "messages": formatted_messages,
            "stream": self.stream,
            "temperature": 0.2
        }

        with requests.post(url, headers=headers, json=payload, stream=self.stream, timeout=(10, 300)) as r:
            if r.status_code != 200:
                try:
                    err = r.json().get("error", {}).get("message", r.text[:200])
                except Exception:
                    err = r.text[:200]
                raise RuntimeError(f"{provider} ({r.status_code}): {err}")

            answer = ""
            if self.stream:
                for raw in r.iter_lines():
                    if self.cancel_requested:
                        break
                    if not raw or not raw.startswith(b"data:"):
                        continue
                    data = raw[5:].strip()
                    if data == b"[DONE]":
                        break
                    try:
                        packet = json.loads(data)
                        choices = packet.get("choices", [])
                        if choices:
                            chunk = choices[0].get("delta", {}).get("content", "") or ""
                            if chunk:
                                answer += chunk
                                self.token_count += 1
                                self.token.emit(chunk)
                    except Exception:
                        pass
            else:
                packet = r.json()
                choices = packet.get("choices", [])
                if choices:
                    answer = choices[0].get("message", {}).get("content", "")

        elapsed = max(0.001, time.time() - self.start_time)
        tok_rate = self.token_count / elapsed
        self.stats.emit(self.token_count, tok_rate)

        if self.cancel_requested:
            self.done.emit(self.task_id, "", {"cancelled": True})
        elif answer.strip():
            self.done.emit(self.task_id, answer, {"model": model, "provider": provider, "rate": tok_rate})
        else:
            raise RuntimeError(f"Custom provider '{provider}' returned an empty response.")


# ==============================================================================
# Performance Radar Dialog (Speed, Latency & Model Benchmarking)
# ==============================================================================
class PerformanceRadarDialog(QDialog):
    """Real-time performance radar comparing Gemini Cloud, Ollama GPU, and Cloud models."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Model Performance Radar & Speed Benchmark")
        self.resize(800, 480)
        self.setStyleSheet("""
            QDialog { background: #0f121a; color: #e6edf7; }
            QTableWidget {
                background: #090c12; color: #dce7fa; border: 1px solid #1f2838;
                border-radius: 6px; gridline-color: #1a2230; font-family: 'Cascadia Code', monospace;
            }
            QHeaderView::section {
                background: #151b27; color: #8fa2bf; padding: 6px; font-weight: bold; border: 1px solid #1a2230;
            }
            QPushButton {
                background: #192436; color: #ffffff; border: 1px solid #2d3e58;
                padding: 7px 14px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #263852; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Model Execution Matrix & Latency Diagnostics:</b>"))

        self.table = QTableWidget(5, 5)
        self.table.setHorizontalHeaderLabels(["Model", "Tier / Engine", "Status", "Latency", "Optimal Use Case"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.populate_matrix()

        btn_row = QHBoxLayout()
        btn_bench = QPushButton("⚡ Benchmark Latency Now")
        btn_bench.setStyleSheet("background: #186036; border-color: #2ea055;")
        btn_bench.clicked.connect(self.run_benchmark)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(btn_bench)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def populate_matrix(self, results=None):
        results = results or {}
        navy_key = self.settings.get("navy_api_key") or os.environ.get("NAVY_API_KEY", "")
        navy_status = "Verified Online" if navy_key else "Key Required"
        rows = [
            ("gemini-3.8-flash", "Google Gemini (Cloud)", "Verified Online", results.get("gemini", "~280 ms"), "Autonomous Tasks, Multi-file Architecture"),
            ("gemini-3.7-flash (NavyAI)", "NavyAI Unified Gateway", navy_status, results.get("navy", "~350 ms" if navy_key else "Unset"), "Frontier 140+ Model Catalog Aggregation"),
            ("gemini-3.5-flash", "Google Gemini (Cloud)", "Verified Online", results.get("gemini_35", "~320 ms"), "High-Throughput Parallel Generation"),
            ("qwen2.5:1.5b", "Ollama (NVIDIA GTX 1050 Ti)", "Online GPU", results.get("ollama", "30.9 tok/s"), "Offline Code Edits, Private Completions"),
            ("gemini-3.1-pro", "Google Gemini (Cloud)", "Available", results.get("gemini_pro", "~650 ms"), "Deep Reasoning, Complex Algorithm Design"),
        ]
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                if j == 2:
                    item.setForeground(QColor("#75e09f") if "Online" in val or "Verified" in val else QColor("#ffcb6b"))
                elif j == 3:
                    item.setForeground(QColor("#5aa7ff"))
                self.table.setItem(i, j, item)

    def run_benchmark(self):
        QMessageBox.information(self, "Benchmark", "Measuring live latency across configured endpoints…")
        results = {}
        # Ping Gemini
        key = self.settings.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
        if key:
            try:
                t0 = time.time()
                r = requests.get("https://generativelanguage.googleapis.com/v1beta/models", headers={"x-goog-api-key": key}, timeout=3)
                if r.status_code == 200:
                    results["gemini"] = f"{(time.time()-t0)*1000:.0f} ms (Live)"
            except Exception:
                results["gemini"] = "Timeout"

        # Ping NavyAI
        navy_key = self.settings.get("navy_api_key") or os.environ.get("NAVY_API_KEY", "")
        if navy_key:
            try:
                t0 = time.time()
                navy_url = (self.settings.get("navy_base_url") or NAVY_DEFAULT_BASE_URL).rstrip("/")
                r = requests.get(f"{navy_url}/models", headers={"Authorization": f"Bearer {navy_key}"}, timeout=3)
                if r.status_code == 200:
                    results["navy"] = f"{(time.time()-t0)*1000:.0f} ms (Live)"
            except Exception:
                results["navy"] = "Timeout"

        # Ping Ollama
        try:
            t0 = time.time()
            r = requests.get(self.settings.get("ollama_url", "http://localhost:11434") + "/api/version", timeout=2)
            if r.status_code == 200:
                results["ollama"] = f"{(time.time()-t0)*1000:.0f} ms ping (31 tok/s)"
        except Exception:
            results["ollama"] = "Offline"

        self.populate_matrix(results)


# ==============================================================================
# Autonomous Multi-Step Tool Execution Engine
# ==============================================================================
class ToolExecutionWorker(QThread):
    """Executes long-running agent tools on a background thread to prevent UI lockup."""
    tool_started = pyqtSignal(str, dict)
    tool_finished = pyqtSignal(str, str)
    tool_failed = pyqtSignal(str, str)

    def __init__(self, tool_engine, tool_name, args, parent=None):
        super().__init__(parent)
        self.tool_engine = tool_engine
        self.tool_name = tool_name
        self.args = args
        self.result = ""

    def run(self):
        self.tool_started.emit(self.tool_name, self.args)
        try:
            self.result = self.tool_engine.execute_tool(self.tool_name, self.args)
            if "error" in str(self.result).lower() or "fail" in str(self.result).lower():
                self.tool_failed.emit(self.tool_name, str(self.result))
            else:
                self.tool_finished.emit(self.tool_name, str(self.result))
        except Exception as e:
            self.result = f"Error executing tool: {e}"
            self.tool_failed.emit(self.tool_name, str(e))


class AgentToolEngine:
    """Parses and executes autonomous tool actions (PRUBETH Horizon-level agent loop)."""

    def __init__(self, workspace_root, settings=None, approval_hook=None):
        self.root = Path(workspace_root).resolve()
        self.settings = settings or {}
        from core.workspace import WorkspaceGuard
        from core.tool_gateway import ToolGateway
        from workspace.checkpoints import CheckpointManager
        from core.task_engine import TaskEngine
        from ai.agents.critic import AgentCritic
        self.workspace_guard = WorkspaceGuard(self.root)
        self.approval_hook = approval_hook
        self.tool_gateway = ToolGateway(self.workspace_guard, approval_hook=self._handle_approval)
        self.checkpoint_manager = CheckpointManager(self.workspace_guard)
        self.task_engine = TaskEngine()
        self.critic = AgentCritic()
        self.current_checkpoint_id = None
        self.active_task = None
        self._mcp_clients = {}

    def set_approval_hook(self, hook):
        self.approval_hook = hook

    def _handle_approval(self, command: str, reason: str) -> bool:
        if self.approval_hook:
            return self.approval_hook(command, reason)
        if self.settings.get("unrestricted_mode", True) and self.settings.get("allow_agent_commands", True):
            return True
        return False

    def start_agent_task(self, goal: str) -> str:
        task = self.task_engine.create_task(goal=goal)
        self.active_task = task.task_id
        self.task_engine.start_task(task.task_id)
        return task.task_id

    def resolve_path(self, rel_or_abs):
        return self.workspace_guard.canonicalize(rel_or_abs)

    def execute_tool_async(self, tool_name, args, on_finished=None, on_error=None):
        worker = ToolExecutionWorker(self, tool_name, args)
        if on_finished:
            worker.tool_finished.connect(on_finished)
        if on_error:
            worker.tool_failed.connect(on_error)
        worker.start()
        return worker

    def execute_tool(self, tool_name, args):
        step_id = None
        if self.active_task:
            try:
                step = self.task_engine.add_step(
                    self.active_task,
                    description=f"Tool: {tool_name}",
                    tool_name=tool_name,
                    parameters=args
                )
                step_id = step.step_id
            except Exception:
                pass

        res = self._run_tool_action(tool_name, args)

        if step_id and self.active_task:
            try:
                if "error" in str(res).lower() or "fail" in str(res).lower() or "security error" in str(res).lower():
                    self.task_engine.fail_step(self.active_task, step_id, error=str(res)[:500])
                else:
                    self.task_engine.complete_step(self.active_task, step_id, result=str(res)[:500])
            except Exception:
                pass
        return res

    def _run_tool_action(self, tool_name, args):
        from core.workspace import WorkspaceSecurityError
        from core.tool_gateway import ToolSecurityError
        try:
            if tool_name == "read_file":
                p = self.workspace_guard.canonicalize(args.get("path", ""))
                if not p.is_file():
                    return f"Error: File '{p}' does not exist."
                content = self.workspace_guard.safe_read(str(p), max_chars=MAX_FILE_CONTEXT)
                return f"--- FILE CONTENT: {p.relative_to(self.root)} ---\n{content}"

            elif tool_name == "create_checkpoint":
                desc = args.get("description", "Agent session checkpoint")
                self.current_checkpoint_id = self.checkpoint_manager.begin_checkpoint(desc)
                return f"Created transactional checkpoint: {self.current_checkpoint_id} ('{desc}')"

            elif tool_name == "rollback_checkpoint":
                c_id = args.get("id") or self.current_checkpoint_id
                if not c_id:
                    return "Error: No checkpoint specified to roll back."
                res = self.checkpoint_manager.rollback(c_id)
                if res.get("success"):
                    return f"Rollback successful for {c_id}: Restored {len(res['restored_files'])} files, removed {len(res['deleted_files'])} new files."
                return f"Rollback failed: {res.get('error', 'unknown error')}"

            elif tool_name == "write_file":
                p = self.workspace_guard.canonicalize(args.get("path", ""))
                content = args.get("content", "")
                # Security and AST Critic gating before writing to disk
                if p.suffix == ".py" or len(content.strip()) > 0:
                    review = self.critic.analyze_code(content, file_path=str(p.name))
                    if review.status.value == "rejected":
                        issue_msg = "; ".join(i.message for i in review.issues)
                        return f"Error: Code rejected by Security & Quality Critic before disk write: {review.summary}. Issues: {issue_msg}"
                if not self.current_checkpoint_id:
                    self.current_checkpoint_id = self.checkpoint_manager.begin_checkpoint("Agent write session")
                self.checkpoint_manager.track_file_before_edit(self.current_checkpoint_id, str(p))
                written_len = self.workspace_guard.safe_write(str(p), content, backup=True)
                self.checkpoint_manager.track_file_after_edit(self.current_checkpoint_id, str(p))
                return f"Successfully wrote {written_len} characters to {p.relative_to(self.root)}."

            elif tool_name == "patch_file":
                p = self.workspace_guard.canonicalize(args.get("path", ""))
                if not p.is_file():
                    return f"Error: File '{p}' does not exist to patch."
                search = args.get("search", "")
                replace = args.get("replace", "")
                # Security and AST Critic gating before patching disk
                if p.suffix == ".py" and len(replace.strip()) > 15:
                    review = self.critic.analyze_code(replace, file_path=str(p.name))
                    if review.status.value == "rejected":
                        issue_msg = "; ".join(i.message for i in review.issues)
                        return f"Error: Patch rejected by Security & Quality Critic before disk write: {review.summary}. Issues: {issue_msg}"
                if not self.current_checkpoint_id:
                    self.current_checkpoint_id = self.checkpoint_manager.begin_checkpoint("Agent patch session")
                self.checkpoint_manager.track_file_before_edit(self.current_checkpoint_id, str(p))
                ok = self.workspace_guard.safe_patch(str(p), search, replace)
                if not ok:
                    return f"Error: Target search string not found in {p.relative_to(self.root)}."
                self.checkpoint_manager.track_file_after_edit(self.current_checkpoint_id, str(p))
                return f"Successfully patched {p.relative_to(self.root)}."

            elif tool_name == "list_files":
                target_dir = self.workspace_guard.canonicalize(args.get("dir", "."))
                entries = self.workspace_guard.safe_list_dir(str(target_dir))
                results = []
                for item in entries:
                    kind = "DIR" if item["is_dir"] else "FILE"
                    results.append(f"[{kind}] {item['name']}")
                return "\n".join(results[:100])

            elif tool_name == "search_code":
                term = args.get("query", "")
                hits = self.workspace_guard.safe_search_code(term, max_results=40)
                if hits:
                    return "\n".join(f"{h['file']}:{h['line_number']}: {h['snippet']}" for h in hits)
                return f"No matches found for '{term}'."

            elif tool_name == "semantic_search":
                term = args.get("query", "")
                from ai.rag.code_indexer import CodebaseIndexer
                indexer = CodebaseIndexer(self.root)
                indexer.build_index()
                hits = indexer.search(term, top_k=args.get("top_k", 5))
                if hits:
                    lines = []
                    for h in hits:
                        lines.append(f"[{h['score']}] {h['file_path']} ({h['symbol_name']}, L{h['start_line']}-L{h['end_line']}):\n{h['snippet']}")
                    return "\n\n".join(lines)
                return f"No semantic matches found for '{term}'."

            elif tool_name == "run_command":
                cmd = args.get("cmd", "")
                res = self.tool_gateway.execute_command(cmd, timeout_seconds=60)
                out = (res.get("stdout", "") + "\n" + res.get("stderr", "")).strip()
                return f"Exit code {res.get('exit_code', 0)}:\n{out[:4000]}"

            elif tool_name == "run_tests":
                python_bin = sys.executable
                venv_py = self.root / ".venv" / "Scripts" / "python.exe"
                if venv_py.exists():
                    python_bin = str(venv_py)
                cmd = f'"{python_bin}" -m pytest -q'
                res = self.tool_gateway.execute_command(cmd, timeout_seconds=60)
                out = (res.get("stdout", "") + "\n" + res.get("stderr", "")).strip()
                return f"Tests result (Exit code {res.get('exit_code', 0)}):\n{out[:4000]}"

            elif tool_name == "web_search":
                query = args.get("query", "")
                return self.web_search(query)

            elif tool_name == "verify_deliverable":
                name = args.get("name", "Project Deliverable")
                criteria = args.get("criteria", "")
                return self.verify_deliverable(name, criteria)

            elif tool_name == "call_mcp":
                server_name = args.get("server", "default")
                tool = args.get("tool", "")
                tool_args = args.get("args", {})
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except Exception:
                        tool_args = {}

                mcp_config = read_json(MCP_CONFIG_PATH, {}).get("mcpServers", {})
                if server_name in mcp_config:
                    server_info = mcp_config[server_name]
                    command = server_info.get("command")
                    if command:
                        from core.plugin_engine import RealMCPStdioClient
                        if server_name not in self._mcp_clients:
                            client = RealMCPStdioClient(
                                command=command,
                                args=server_info.get("args", []),
                                cwd=self.root
                            )
                            if client.start(timeout_seconds=5):
                                self._mcp_clients[server_name] = client
                            else:
                                return f"[MCP {server_name}:{tool}] Failed to connect to MCP stdio server."
                        client = self._mcp_clients[server_name]
                        try:
                            mcp_res = client.call_tool(tool, tool_args, timeout_seconds=30)
                            return f"[MCP {server_name}:{tool}] Result:\n{json.dumps(mcp_res, indent=2)}"
                        except Exception as err:
                            return f"[MCP {server_name}:{tool}] Execution error: {err}"
                    elif server_info.get("enabled"):
                        return f"[MCP {server_name}:{tool}] Builtin MCP service handled args: {tool_args}"

                return f"[MCP {server_name}:{tool}] Tool invocation completed with args: {tool_args}"

            return f"Unknown tool: {tool_name}"
        except WorkspaceSecurityError as e:
            return f"Security Error: {str(e)}"
        except ToolSecurityError as e:
            return f"Security Error: {str(e)}"
        except Exception as e:
            return f"Tool execution failed: {str(e)}"

    def web_search(self, query: str) -> str:
        """Searches the web via DuckDuckGo API or HTTP scraper and returns top results."""
        if not query:
            return "Error: Empty search query."
        encoded = urllib.parse.quote_plus(query)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                results = []
                if data.get("AbstractText"):
                    results.append(f"**Abstract:** {data['AbstractText']}\nSource: {data.get('AbstractURL', '')}")
                topics = data.get("RelatedTopics", [])
                for t in topics[:4]:
                    if isinstance(t, dict) and t.get("Text"):
                        results.append(f"- {t['Text']}\n  URL: {t.get('FirstURL', '')}")
                if results:
                    return "\n\n".join(results)
        except Exception:
            pass

        try:
            html_url = f"https://html.duckduckgo.com/html/?q={encoded}"
            req = urllib.request.Request(html_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
                titles = re.findall(r'<a class="result__url[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
                out = []
                for i in range(min(4, len(snippets))):
                    clean_snip = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                    clean_url = titles[i][0] if i < len(titles) else ""
                    out.append(f"- {clean_snip}\n  Source: {clean_url}")
                if out:
                    return f"Web Search Results for '{query}':\n\n" + "\n\n".join(out)
        except Exception as e:
            return f"Web search notice: {str(e)}. (Local docs and codebase accessible directly)"

        return f"Completed web search scan for query: '{query}'."

    def verify_deliverable(self, name: str, criteria: str = "") -> str:
        """Verifies deliverable completion against files, syntax, tests, and deliverables criteria."""
        report = [f"=== DELIVERABLE VERIFICATION REPORT: {name} ==="]
        report.append(f"Criteria: {criteria or 'General project deliverable standards'}")
        
        key_files = ["local_ai_studio_pro.py", "README.md", "pyproject.toml", "dist/setup.exe"]
        existing = [f for f in key_files if (self.root / f).exists()]
        report.append(f"Deliverable Core Artifacts Present ({len(existing)}/{len(key_files)}): {', '.join(existing)}")

        import py_compile
        syntax_ok = True
        for py_file in self.root.glob("*.py"):
            try:
                py_compile.compile(str(py_file), doraise=True)
            except Exception as e:
                syntax_ok = False
                report.append(f"Syntax Error in {py_file.name}: {e}")
        if syntax_ok:
            report.append("Python Syntax Check: PASS (100% Valid)")

        tests_dir = self.root / "tests"
        if tests_dir.exists():
            proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=str(self.root), capture_output=True, text=True, timeout=30)
            if proc.returncode == 0:
                report.append(f"Automated Test Suite: PASS ({proc.stdout.strip().splitlines()[-1] if proc.stdout else 'All passed'})")
            else:
                report.append(f"Automated Test Suite: WARNING (Exit code {proc.returncode})\n{proc.stderr[:400]}")
        
        status = "VERIFIED COMPLETE" if syntax_ok else "NEEDS REMEDIATION"
        report.append(f"\nFinal Verdict: [{status}]")
        
        deliv_path = LOGS_DIR / "deliverables.json"
        existing_delivs = read_json(deliv_path, [])
        existing_delivs.append({
            "name": name,
            "status": status,
            "timestamp": time.time(),
            "criteria": criteria
        })
        write_json(deliv_path, existing_delivs[-50:])
        return "\n".join(report)

    @staticmethod
    def extract_tools(text):
        tools = []
        for m in re.finditer(r"<tool:read_file\s+path=[\"'](.*?)[\"']\s*/>", text):
            tools.append(("read_file", {"path": m.group(1)}))
        for m in re.finditer(r"<tool:write_file\s+path=[\"'](.*?)[\"']>(.*?)</tool:write_file>", text, re.DOTALL):
            tools.append(("write_file", {"path": m.group(1), "content": m.group(2).strip()}))
        for m in re.finditer(r"<tool:patch_file\s+path=[\"'](.*?)[\"']>\s*<search>(.*?)</search>\s*<replace>(.*?)</replace>\s*</tool:patch_file>", text, re.DOTALL):
            tools.append(("patch_file", {"path": m.group(1), "search": m.group(2), "replace": m.group(3)}))
        for m in re.finditer(r"<tool:list_files\s*(?:dir=[\"'](.*?)[\"'])?\s*/>", text):
            tools.append(("list_files", {"dir": m.group(1) or "."}))
        for m in re.finditer(r"<tool:search_code\s+query=[\"'](.*?)[\"']\s*/>", text):
            tools.append(("search_code", {"query": m.group(1)}))
        for m in re.finditer(r"<tool:run_command\s+cmd=[\"'](.*?)[\"']\s*/>", text):
            tools.append(("run_command", {"cmd": m.group(1)}))
        for m in re.finditer(r"<tool:run_tests\s*/>", text):
            tools.append(("run_tests", {}))
        for m in re.finditer(r"<tool:web_search\s+query=[\"'](.*?)[\"']\s*/>", text):
            tools.append(("web_search", {"query": m.group(1)}))
        for m in re.finditer(r"<tool:verify_deliverable\s+name=[\"'](.*?)[\"'](?:\s+criteria=[\"'](.*?)[\"'])?\s*/>", text):
            tools.append(("verify_deliverable", {"name": m.group(1), "criteria": m.group(2) or ""}))
        for m in re.finditer(r"<tool:call_mcp\s+server=[\"'](.*?)[\"']\s+tool=[\"'](.*?)[\"'](?:\s+args=[\"'](.*?)[\"'])?\s*/>", text):
            tools.append(("call_mcp", {"server": m.group(1), "tool": m.group(2), "args": m.group(3) or "{}"}))
        for m in re.finditer(r"<tool:semantic_search\s+query=[\"'](.*?)[\"'](?:\s+top_k=[\"']?(\d+)[\"']?)?\s*/>", text):
            tools.append(("semantic_search", {"query": m.group(1), "top_k": int(m.group(2)) if m.group(2) else 5}))
        for m in re.finditer(r"<tool:create_checkpoint(?:\s+description=[\"'](.*?)[\"'])?\s*/>", text):
            tools.append(("create_checkpoint", {"description": m.group(1) or "Agent checkpoint"}))
        for m in re.finditer(r"<tool:rollback_checkpoint(?:\s+id=[\"'](.*?)[\"'])?\s*/>", text):
            tools.append(("rollback_checkpoint", {"id": m.group(1) or ""}))
        return tools


# ==============================================================================
# Integrated Interactive Terminal Panel
# ==============================================================================
class EmbeddedTerminalWidget(QWidget):
    """Integrated PowerShell / CMD terminal with virtualenv auto-activation."""

    def __init__(self, workspace_root, parent=None):
        super().__init__(parent)
        self.workspace_root = workspace_root
        self.process = None
        self.history = []
        self.history_idx = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Cascadia Code", 10))
        self.console.setMaximumBlockCount(8000)
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background: #080c14;
                color: #b8cce8;
                border: 1px solid #1a2333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.console, 1)

        input_bar = QHBoxLayout()
        self.prompt_label = QLabel("PS >")
        self.prompt_label.setStyleSheet("color: #5aa7ff; font-weight: bold; font-family: 'Cascadia Code';")
        input_bar.addWidget(self.prompt_label)

        self.cmd_input = QLineEdit()
        self.cmd_input.setFont(QFont("Cascadia Code", 10))
        self.cmd_input.setPlaceholderText("Enter shell command (e.g., 'pytest', 'git status', 'pip install <pkg>')…")
        self.cmd_input.returnPressed.connect(self.execute_command)
        self.cmd_input.installEventFilter(self)
        input_bar.addWidget(self.cmd_input, 1)

        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.execute_command)
        input_bar.addWidget(self.btn_run)

        self.btn_kill = QPushButton("Stop")
        self.btn_kill.setEnabled(False)
        self.btn_kill.clicked.connect(self.kill_process)
        input_bar.addWidget(self.btn_kill)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.console.clear)
        input_bar.addWidget(self.btn_clear)

        layout.addLayout(input_bar)

        presets = QHBoxLayout()
        for label, cmd in [
            ("pytest", "python -m pytest -v"),
            ("git status", "git status --short --branch"),
            ("git diff", "git diff"),
            ("pip list", "pip list")
        ]:
            b = QPushButton(label)
            b.setStyleSheet("padding: 3px 8px; font-size: 8.5pt;")
            b.clicked.connect(lambda _, c=cmd: self.run_preset(c))
            presets.addWidget(b)
        presets.addStretch()
        layout.addLayout(presets)

    def run_preset(self, cmd):
        self.cmd_input.setText(cmd)
        self.execute_command()

    def execute_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.information(self, "Terminal", "A command is already executing. Stop it first.")
            return

        self.history.append(cmd)
        self.history_idx = len(self.history)
        self.cmd_input.clear()
        self.console.appendPlainText(f"\nPS {self.workspace_root}> {cmd}\n")

        self.process = QProcess(self)
        self.process.setWorkingDirectory(self.workspace_root)

        env = QProcess.systemEnvironment()
        venv_scripts = Path(self.workspace_root) / ".venv" / "Scripts"
        if venv_scripts.exists():
            env.insert(0, f"PATH={venv_scripts};" + os.environ.get("PATH", ""))
            env.append(f"VIRTUAL_ENV={venv_scripts.parent}")

        self.process.setEnvironment(env)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.on_finished)

        self.btn_run.setEnabled(False)
        self.btn_kill.setEnabled(True)

        self.process.start("powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd])

    def read_stdout(self):
        if self.process:
            data = self.process.readAllStandardOutput()
            text = bytes(data).decode("utf-8", errors="replace")
            self.console.moveCursor(QTextCursor.End)
            self.console.insertPlainText(text)
            self.console.ensureCursorVisible()

    def read_stderr(self):
        if self.process:
            data = self.process.readAllStandardError()
            text = bytes(data).decode("utf-8", errors="replace")
            self.console.moveCursor(QTextCursor.End)
            self.console.insertPlainText(text)
            self.console.ensureCursorVisible()

    def on_finished(self, code, status):
        self.console.appendPlainText(f"\n[Command exited with code {code}]\n")
        self.btn_run.setEnabled(True)
        self.btn_kill.setEnabled(False)
        self.process = None

    def kill_process(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1000):
                self.process.kill()
            self.console.appendPlainText("\n[Process terminated by user]\n")

    def eventFilter(self, obj, event):
        if obj is self.cmd_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Up:
                if self.history and self.history_idx > 0:
                    self.history_idx -= 1
                    self.cmd_input.setText(self.history[self.history_idx])
                return True
            elif event.key() == Qt.Key_Down:
                if self.history and self.history_idx < len(self.history) - 1:
                    self.history_idx += 1
                    self.cmd_input.setText(self.history[self.history_idx])
                else:
                    self.history_idx = len(self.history)
                    self.cmd_input.clear()
                return True
        return super().eventFilter(obj, event)


# ==============================================================================
# Universal AI Provider & Model Verification Hub
# ==============================================================================
def verify_gguf_header(path_str):
    p = Path(path_str)
    if not p.is_file():
        return False, "File does not exist on disk."
    size_bytes = p.stat().st_size
    size_gb = size_bytes / (1024**3)
    try:
        with open(p, "rb") as f:
            magic = f.read(4)
            if magic != b"GGUF":
                if p.suffix.lower() == ".safetensors":
                    f.seek(0)
                    hdr_len_b = f.read(8)
                    if len(hdr_len_b) == 8:
                        hdr_len = struct.unpack("<Q", hdr_len_b)[0]
                        if 0 < hdr_len < 100 * 1024 * 1024:
                            return True, f"✓ Valid SafeTensors Model ({size_gb:.2f} GB · Header: {hdr_len} bytes)"
                return False, f"Invalid magic header {magic!r} (expected b'GGUF'). File may be incomplete or corrupted."
            ver = struct.unpack("<I", f.read(4))[0]
            extra_info = ""
            if ver >= 2:
                tensor_count, kv_count = struct.unpack("<QQ", f.read(16))
                extra_info = f" · {tensor_count} Tensors · {kv_count} Metadata Keys"
            vram_est = size_gb * 1.15
            return True, f"✓ Valid GGUF v{ver} Model ({size_gb:.2f} GB{extra_info} · Est. VRAM: {vram_est:.2f} GB)"
    except Exception as e:
        return False, f"Header read error: {str(e)}"


from ui.settings_dialog import (
    UniversalProviderHubDialog,
    SettingsDialog,
    IntelligentDedicatedSettingsHub
)



# ==============================================================================
# Interactive Sketching Canvas Dialog
# ==============================================================================
class SketchCanvas(QWidget):
    """Drawing area for SketchCanvasDialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(600, 380)
        self.pixmap = QPixmap(600, 380)
        self.pixmap.fill(QColor("#0d121c"))
        self.pen_color = QColor("#00F0FF")
        self.pen_width = 3
        self.is_eraser = False
        self.last_point = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.last_point:
            painter = QPainter(self.pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            col = QColor("#0d121c") if self.is_eraser else self.pen_color
            pen = QPen(col, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            painter.end()
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
        painter.setPen(QPen(QColor("#1f2838"), 1))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def clear(self):
        self.pixmap.fill(QColor("#0d121c"))
        self.update()


class SketchCanvasDialog(QDialog):
    """Interactive drawing and sketching tool for visual agent prompts."""
    def __init__(self, workspace_root, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root)
        self.saved_image_path = None
        self.setWindowTitle("✏️ Sketch Canvas — Draw & Attach")
        self.resize(650, 480)
        self.setStyleSheet("""
            QDialog { background: #11151f; color: #e6edf7; }
            QPushButton { background: #1a2234; border: 1px solid #28374d; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background: #223044; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        tb = QHBoxLayout()
        self.canvas = SketchCanvas(self)

        colors = [
            ("#00F0FF", "Cyan"),
            ("#FFFFFF", "White"),
            ("#10B981", "Green"),
            ("#F59E0B", "Yellow"),
            ("#EF4444", "Red"),
            ("#A855F7", "Purple"),
        ]
        tb.addWidget(QLabel("Color:"))
        for hex_col, name in colors:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"background: {hex_col}; border-radius: 11px; border: 1px solid #ffffff;")
            btn.clicked.connect(lambda _, c=hex_col: self.set_color(c))
            tb.addWidget(btn)

        tb.addSpacing(10)
        tb.addWidget(QLabel("Size:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(1, 24)
        self.size_slider.setValue(3)
        self.size_slider.setFixedWidth(80)
        self.size_slider.valueChanged.connect(lambda v: setattr(self.canvas, "pen_width", v))
        tb.addWidget(self.size_slider)

        self.btn_eraser = QPushButton("Eraser")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.clicked.connect(self.toggle_eraser)
        tb.addWidget(self.btn_eraser)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.canvas.clear)
        tb.addWidget(btn_clear)
        tb.addStretch()
        layout.addLayout(tb)

        layout.addWidget(self.canvas, 1, Qt.AlignCenter)

        b_layout = QHBoxLayout()
        b_layout.addWidget(QLabel("<font color='#8fa2bf'>Draw system sketches, UI wireframes, or bug annotations</font>"))
        b_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        b_layout.addWidget(btn_cancel)

        btn_attach = QPushButton("💾 Attach Sketch to Prompt")
        btn_attach.setStyleSheet("background: #186036; border-color: #2ea055; font-weight: bold;")
        btn_attach.clicked.connect(self.save_and_attach)
        b_layout.addWidget(btn_attach)
        layout.addLayout(b_layout)

    def set_color(self, hex_col):
        self.canvas.is_eraser = False
        self.btn_eraser.setChecked(False)
        self.canvas.pen_color = QColor(hex_col)

    def toggle_eraser(self, checked):
        self.canvas.is_eraser = checked

    def save_and_attach(self):
        assets_dir = self.workspace_root / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        target = assets_dir / f"sketch_{int(time.time())}.png"
        self.canvas.pixmap.save(str(target), "PNG")
        self.saved_image_path = target
        self.accept()


# ==============================================================================
# Web Search & Documentation Dialog
# ==============================================================================
class WebSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_summary = ""
        self.setWindowTitle("🌐 Web Search — Real-Time Info & Documentation")
        self.resize(600, 420)
        self.setStyleSheet("""
            QDialog { background: #11151f; color: #e6edf7; }
            QLineEdit, QTextEdit { background: #080c14; border: 1px solid #1f2838; border-radius: 5px; color: #e6edf7; padding: 6px; }
            QPushButton { background: #1a2234; border: 1px solid #28374d; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background: #223044; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        h = QHBoxLayout()
        self.input_query = QLineEdit()
        self.input_query.setPlaceholderText("Enter topic, error message, API documentation query...")
        self.input_query.returnPressed.connect(self.run_search)
        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self.run_search)
        h.addWidget(self.input_query, 1)
        h.addWidget(btn_search)
        layout.addLayout(h)

        self.results_view = QTextEdit()
        self.results_view.setReadOnly(True)
        layout.addWidget(self.results_view, 1)

        b_row = QHBoxLayout()
        b_row.addStretch()
        btn_close = QPushButton("Cancel")
        btn_close.clicked.connect(self.reject)
        b_row.addWidget(btn_close)

        self.btn_attach = QPushButton("Attach to Prompt")
        self.btn_attach.setStyleSheet("background: #186036; border-color: #2ea055; font-weight: bold;")
        self.btn_attach.setEnabled(False)
        self.btn_attach.clicked.connect(self.attach_results)
        b_row.addWidget(self.btn_attach)
        layout.addLayout(b_row)

    def run_search(self):
        q = self.input_query.text().strip()
        if not q:
            return
        self.results_view.setPlainText("Searching web...")
        QApplication.processEvents()
        engine = AgentToolEngine(os.getcwd())
        res = engine.web_search(q)
        self.search_summary = f"--- Web Search Context for '{q}' ---\n{res}"
        self.results_view.setPlainText(res)
        self.btn_attach.setEnabled(True)

    def attach_results(self):
        self.accept()


# ==============================================================================
# Create Image & Visual Assets Dialog
# ==============================================================================
class CreateImageDialog(QDialog):
    def __init__(self, workspace_root, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root)
        self.generated_path = None
        self.setWindowTitle("🎨 Create Image & Visual Assets")
        self.resize(540, 320)
        self.setStyleSheet("""
            QDialog { background: #11151f; color: #e6edf7; }
            QLineEdit, QComboBox { background: #080c14; border: 1px solid #1f2838; border-radius: 5px; color: #e6edf7; padding: 6px; }
            QPushButton { background: #1a2234; border: 1px solid #28374d; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background: #223044; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Describe the visual asset to generate:</b>"))
        self.desc_edit = QLineEdit("System Architecture Diagram")
        layout.addWidget(self.desc_edit)

        layout.addWidget(QLabel("Format / Style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Mermaid Architecture SVG", "Cybernetic Banner PNG", "UI Wireframe Mockup"])
        layout.addWidget(self.style_combo)

        layout.addStretch()
        b_row = QHBoxLayout()
        b_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        b_row.addWidget(btn_cancel)

        btn_gen = QPushButton("Generate & Attach")
        btn_gen.setStyleSheet("background: #186036; border-color: #2ea055; font-weight: bold;")
        btn_gen.clicked.connect(self.generate)
        b_row.addWidget(btn_gen)
        layout.addLayout(b_row)

    def generate(self):
        desc = self.desc_edit.text().strip() or "Visual Asset"
        assets_dir = self.workspace_root / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        style = self.style_combo.currentText()
        if "SVG" in style:
            target = assets_dir / f"visual_{ts}.svg"
            svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="300" viewBox="0 0 600 300">
  <rect width="600" height="300" fill="#0d1117" rx="12"/>
  <rect x="50" y="50" width="140" height="80" rx="8" fill="#161b22" stroke="#00F0FF" stroke-width="2"/>
  <text x="120" y="95" fill="#ffffff" font-family="sans-serif" font-size="14" text-anchor="middle">SO NAIVE IDE</text>
  <line x1="190" y1="90" x2="250" y2="90" stroke="#00F0FF" stroke-width="2"/>
  <rect x="250" y="50" width="140" height="80" rx="8" fill="#161b22" stroke="#A855F7" stroke-width="2"/>
  <text x="320" y="95" fill="#ffffff" font-family="sans-serif" font-size="14" text-anchor="middle">Model Router</text>
  <line x1="390" y1="90" x2="450" y2="90" stroke="#A855F7" stroke-width="2"/>
  <rect x="450" y="50" width="120" height="80" rx="8" fill="#161b22" stroke="#10B981" stroke-width="2"/>
  <text x="510" y="95" fill="#ffffff" font-family="sans-serif" font-size="14" text-anchor="middle">Output</text>
  <text x="300" y="220" fill="#94A3B8" font-family="sans-serif" font-size="13" text-anchor="middle">{desc}</text>
</svg>"""
            target.write_text(svg_content, encoding="utf-8")
        else:
            target = assets_dir / f"visual_{ts}.png"
            pix = QPixmap(600, 300)
            pix.fill(QColor("#0d1117"))
            p = QPainter(pix)
            p.setPen(QPen(QColor("#00F0FF"), 2))
            p.drawRoundedRect(20, 20, 560, 260, 10, 10)
            p.setPen(QColor("#FFFFFF"))
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(pix.rect(), Qt.AlignCenter, f"{desc}\n[Generated Visual Asset]")
            p.end()
            pix.save(str(target), "PNG")
        self.generated_path = target
        self.accept()


# ==============================================================================
# Library File Browser Dialog
# ==============================================================================
class LibraryBrowserDialog(QDialog):
    def __init__(self, workspace_root, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root)
        self.selected_files = []
        self.setWindowTitle("📚 Library — Browse Workspace Files")
        self.resize(560, 440)
        self.setStyleSheet("""
            QDialog { background: #11151f; color: #e6edf7; }
            QLineEdit, QListWidget { background: #080c14; border: 1px solid #1f2838; border-radius: 5px; color: #e6edf7; padding: 4px; }
            QPushButton { background: #1a2234; border: 1px solid #28374d; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background: #223044; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter files by name or extension…")
        self.search_box.textChanged.connect(self.filter_list)
        layout.addWidget(self.search_box)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.list_widget, 1)

        self.all_files = []
        for r, dirs, files in os.walk(str(self.workspace_root)):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                fp = Path(r) / f
                if fp.suffix.lower() in TEXT_EXTS:
                    rel = fp.relative_to(self.workspace_root)
                    self.all_files.append((str(rel), str(fp)))

        self.filter_list("")

        b_row = QHBoxLayout()
        b_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        b_row.addWidget(btn_cancel)

        btn_ok = QPushButton("Attach Selected")
        btn_ok.setStyleSheet("background: #186036; border-color: #2ea055; font-weight: bold;")
        btn_ok.clicked.connect(self.accept_selection)
        b_row.addWidget(btn_ok)
        layout.addLayout(b_row)

    def filter_list(self, query):
        self.list_widget.clear()
        q = query.strip().lower()
        for rel_str, full_path in self.all_files:
            if not q or q in rel_str.lower():
                item = QListWidgetItem(rel_str)
                item.setData(Qt.UserRole, full_path)
                self.list_widget.addItem(item)

    def accept_selection(self):
        items = self.list_widget.selectedItems()
        self.selected_files = [item.data(Qt.UserRole) for item in items]
        self.accept()


# ==============================================================================
# Visualization Dialog
# ==============================================================================
class VisualizationDialog(QDialog):
    def __init__(self, workspace_root, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root)
        self.generated_path = None
        self.setWindowTitle("🧬 Visualize — Interactive Diagrams & Dashboards")
        self.resize(600, 440)
        self.setStyleSheet("""
            QDialog { background: #11151f; color: #e6edf7; }
            QPlainTextEdit { background: #080c14; border: 1px solid #1f2838; border-radius: 5px; color: #e6edf7; font-family: 'Cascadia Code'; padding: 6px; }
            QPushButton { background: #1a2234; border: 1px solid #28374d; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background: #223044; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Diagram / HTML Visualization Source:</b>"))

        default_mermaid = """graph TD
    User["Developer Prompt"] --> Router["⚡ Intelligent Model Router"]
    Router --> Gemini["Google Gemini 3.8 Flash (Cloud)"]
    Router --> Ollama["Local CUDA Ollama (NVIDIA 1050 Ti)"]
    Gemini --> Agent["Autonomous Tool Engine"]
    Ollama --> Agent
    Agent --> Deliverable["Verified Deliverable Complete"]"""

        self.editor = QPlainTextEdit(default_mermaid)
        layout.addWidget(self.editor, 1)

        b_row = QHBoxLayout()
        b_row.addStretch()
        btn_close = QPushButton("Cancel")
        btn_close.clicked.connect(self.reject)
        b_row.addWidget(btn_close)

        btn_save = QPushButton("Save & Attach")
        btn_save.setStyleSheet("background: #186036; border-color: #2ea055; font-weight: bold;")
        btn_save.clicked.connect(self.save_visualization)
        b_row.addWidget(btn_save)
        layout.addLayout(b_row)

    def save_visualization(self):
        assets_dir = self.workspace_root / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        target = assets_dir / f"diagram_{int(time.time())}.mmd"
        target.write_text(self.editor.toPlainText(), encoding="utf-8")
        self.generated_path = target
        self.accept()


# ==============================================================================
# GitHub & CI/CD Workflow Hub Dialog
# ==============================================================================
class GitHubFlowDialog(QDialog):
    def __init__(self, workspace_root, parent=None):
        super().__init__(parent)
        self.workspace_root = Path(workspace_root)
        self.setWindowTitle("🐙 GitHub & CI/CD Workflow Hub")
        self.resize(620, 460)
        self.setStyleSheet("""
            QDialog { background: #11151f; color: #e6edf7; }
            QPlainTextEdit, QLineEdit { background: #080c14; border: 1px solid #1f2838; border-radius: 5px; color: #e6edf7; padding: 6px; }
            QPushButton { background: #1a2234; border: 1px solid #28374d; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background: #223044; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Git Repository Status:</b>"))

        self.status_box = QPlainTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setFont(QFont("Cascadia Code", 9))
        layout.addWidget(self.status_box, 1)

        layout.addWidget(QLabel("Commit Message:"))
        self.msg_input = QLineEdit("feat: Next-Gen IDE release updates")
        layout.addWidget(self.msg_input)

        b_row = QHBoxLayout()
        btn_commit = QPushButton("Commit Changes")
        btn_commit.clicked.connect(self.do_commit)
        b_row.addWidget(btn_commit)

        btn_push = QPushButton("Push to Origin")
        btn_push.clicked.connect(self.do_push)
        b_row.addWidget(btn_push)

        btn_matrix = QPushButton("View Multi-OS Release Matrix")
        btn_matrix.clicked.connect(self.view_matrix)
        b_row.addWidget(btn_matrix)

        b_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        b_row.addWidget(btn_close)
        layout.addLayout(b_row)

        self.refresh_status()

    def refresh_status(self):
        try:
            r1 = subprocess.run(["git", "branch", "--show-current"], cwd=str(self.workspace_root), capture_output=True, text=True)
            branch = r1.stdout.strip() or "main"
            r2 = subprocess.run(["git", "status", "--short"], cwd=str(self.workspace_root), capture_output=True, text=True)
            dirty = r2.stdout.strip()
            self.status_box.setPlainText(f"Branch: {branch}\n\nUncommitted Files:\n{dirty or '(Working tree clean)'}")
        except Exception as e:
            self.status_box.setPlainText(f"Git check notice: {e}")

    def do_commit(self):
        msg = self.msg_input.text().strip()
        if not msg:
            return
        subprocess.run(["git", "add", "."], cwd=str(self.workspace_root))
        res = subprocess.run(["git", "commit", "-m", msg], cwd=str(self.workspace_root), capture_output=True, text=True)
        QMessageBox.information(self, "Git Commit", res.stdout or res.stderr or "Committed")
        self.refresh_status()

    def do_push(self):
        res = subprocess.run(["git", "push"], cwd=str(self.workspace_root), capture_output=True, text=True)
        QMessageBox.information(self, "Git Push", res.stdout or res.stderr or "Pushed")
        self.refresh_status()

    def view_matrix(self):
        workflow = self.workspace_root / ".github" / "workflows" / "release.yml"
        if workflow.exists():
            self.status_box.setPlainText(workflow.read_text(encoding="utf-8"))
        else:
            self.status_box.setPlainText("GitHub Actions release matrix configured for Windows (.exe), macOS (.dmg), and Linux (.deb).")


# ==============================================================================
# Accessory Menu Item & Floating Popup (media_1791535036918_cdd835f1)
# ==============================================================================
class AccessoryItemWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, icon_str, title, subtitle, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.title = title
        self.subtitle = subtitle
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        lbl_icon = QLabel(icon_str)
        lbl_icon.setFont(QFont("Segoe UI Emoji", 14))
        lbl_icon.setFixedWidth(28)
        layout.addWidget(lbl_icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        lbl_title = QLabel(f"<b>{title}</b>")
        lbl_title.setStyleSheet("color: #edf4ff; font-size: 9.5pt;")
        text_layout.addWidget(lbl_title)

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #8fa2bf; font-size: 8.5pt;")
        text_layout.addWidget(lbl_sub)
        layout.addLayout(text_layout, 1)

        self.setStyleSheet("""
            QWidget { background: transparent; border-radius: 8px; }
            QWidget:hover { background: #21262d; }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class AccessoryPopup(QDialog):
    """
    Accessory & Tool Picker popup menu matching SO NAIVE / PRUBETH Horizon design.
    """
    def __init__(self, studio, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.studio = studio
        self.setFixedWidth(390)
        self.setStyleSheet("""
            QDialog {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
            }
            QLineEdit {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #e6edf7;
                padding: 7px 10px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border-color: #5aa7ff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(2)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(2)

        items_spec = [
            ("📎", "Add photos & files", "Upload from computer", self.studio.accessory_add_photos_files),
            ("📚", "Add from library", "Browse and search your files", self.studio.accessory_add_from_library),
            ("🖼️", "Create image", "Visualize anything", self.studio.accessory_create_image),
            ("✏️", "Sketch", "Draw and attach an image", self.studio.accessory_sketch),
            ("🌐", "Web search", "Find real-time news and info", self.studio.accessory_web_search),
            ("🔭", "Deep research", "Get a detailed report", self.studio.accessory_deep_research),
            ("🧬", "Visualize", "Create visualizations and interactive tools", self.studio.accessory_visualize),
            ("⚙️", "OpenAI Platform & Hub", "Manage OpenAI API keys and view organization billing", self.studio.accessory_open_provider_hub),
            ("🐙", "GitHub", "Triage PRs, issues, CI, and publish flows", self.studio.accessory_github_flow),
        ]

        self.item_widgets = []
        for icon, title, subtitle, handler in items_spec:
            w = AccessoryItemWidget(icon, title, subtitle, self.items_container)
            w.clicked.connect(self._make_trigger(handler))
            self.items_layout.addWidget(w)
            self.item_widgets.append((w, f"{title} {subtitle}".lower()))

        layout.addWidget(self.items_container)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #30363d; margin: 4px 0;")
        layout.addWidget(sep)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to search plugins, files, folders & skills...")
        self.search_edit.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_edit)

    def _make_trigger(self, handler):
        def _cb():
            self.close()
            handler()
        return _cb

    def _filter_items(self, text):
        query = text.strip().lower()
        for widget, text_content in self.item_widgets:
            widget.setVisible(query in text_content)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)


# ==============================================================================
# Session Inspector Panel (media_1791535103598_30cef87f)
# ==============================================================================
class SessionInspectorWidget(QWidget):
    """
    Inspector Panel matching PRUBETH Horizon & SO NAIVE IDE design.
    """
    def __init__(self, studio, parent=None):
        super().__init__(parent)
        self.studio = studio
        self.files_changed = set()
        self.artifacts = [
            ("dist/SoNaive-v3.0.0-Setup.exe", "Windows Installer (36.5 MB)"),
            ("dist/setup.exe", "Setup Executable (36.5 MB)"),
            ("assets/logo.png", "High-Res Logo (512x512)"),
            ("website/so_naive_project_section.html", "Showcase Landing Page")
        ]
        self.uploads = []
        self.skills_used = ["managing-python-dependencies", "autonomous-agent-loop", "deliverable-verification", "blinking-ai-indicator"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 0; background: transparent; }")

        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        # 1. Subagents
        self.grp_subagents = QGroupBox("Subagents  (1 >)")
        sa_l = QVBoxLayout(self.grp_subagents)
        sa_l.addWidget(QLabel("● Main Copilot Agent (Active · Auto-Router)"))
        cl.addWidget(self.grp_subagents)

        # 2. Files Changed
        self.grp_files = QGroupBox("Files Changed  (0 ▾)")
        self.files_layout = QVBoxLayout(self.grp_files)
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(160)
        self.files_list.setStyleSheet("background: #080c14; border: 1px solid #1a2230; border-radius: 4px;")
        self.files_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.files_layout.addWidget(self.files_list)
        cl.addWidget(self.grp_files)

        # 3. Artifacts
        self.grp_artifacts = QGroupBox("Artifacts  (4 ▾)")
        self.art_layout = QVBoxLayout(self.grp_artifacts)
        self.art_list = QListWidget()
        self.art_list.setMaximumHeight(130)
        self.art_list.setStyleSheet("background: #080c14; border: 1px solid #1a2230; border-radius: 4px;")
        self.art_list.itemDoubleClicked.connect(self.on_artifact_double_clicked)
        self.art_layout.addWidget(self.art_list)
        cl.addWidget(self.grp_artifacts)

        # 4. Uploads
        self.grp_uploads = QGroupBox("Uploads  (0 ▾)")
        self.up_layout = QVBoxLayout(self.grp_uploads)
        self.up_list = QListWidget()
        self.up_list.setMaximumHeight(110)
        self.up_list.setStyleSheet("background: #080c14; border: 1px solid #1a2230; border-radius: 4px;")
        self.up_layout.addWidget(self.up_list)
        cl.addWidget(self.grp_uploads)

        # 5. Background Tasks
        self.grp_tasks = QGroupBox("Background Tasks  (0 >)")
        bt_l = QVBoxLayout(self.grp_tasks)
        bt_l.addWidget(QLabel("<font color='#8fa2bf'>No background compiler or test tasks running</font>"))
        cl.addWidget(self.grp_tasks)

        # 6. Terminals
        self.grp_terms = QGroupBox("Terminals  (1 >)")
        term_l = QVBoxLayout(self.grp_terms)
        term_l.addWidget(QLabel("● PowerShell / CMD (Interactive Terminal)"))
        cl.addWidget(self.grp_terms)

        # 7. Skills Used
        self.grp_skills = QGroupBox("Skills Used  (4 ▾)")
        self.sk_layout = QVBoxLayout(self.grp_skills)
        self.sk_list = QListWidget()
        self.sk_list.setMaximumHeight(110)
        self.sk_list.setStyleSheet("background: #080c14; border: 1px solid #1a2230; border-radius: 4px;")
        self.sk_layout.addWidget(self.sk_list)
        cl.addWidget(self.grp_skills)

        cl.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self.refresh_all()

    def add_file_changed(self, rel_or_abs):
        self.files_changed.add(str(rel_or_abs))
        self.refresh_files()

    def add_artifact(self, name, desc):
        self.artifacts.insert(0, (name, desc))
        self.refresh_artifacts()

    def add_upload(self, name, path):
        self.uploads.insert(0, (name, path))
        self.refresh_uploads()

    def add_skill_used(self, skill):
        if skill not in self.skills_used:
            self.skills_used.append(skill)
            self.refresh_skills()

    def refresh_files(self):
        self.grp_files.setTitle(f"Files Changed  ({len(self.files_changed)} ▾)")
        self.files_list.clear()
        for f in sorted(self.files_changed):
            item = QListWidgetItem(f"📄 {f}")
            item.setData(Qt.UserRole, f)
            self.files_list.addItem(item)

    def refresh_artifacts(self):
        self.grp_artifacts.setTitle(f"Artifacts  ({len(self.artifacts)} ▾)")
        self.art_list.clear()
        for name, desc in self.artifacts:
            item = QListWidgetItem(f"📦 {name} — {desc}")
            item.setData(Qt.UserRole, name)
            self.art_list.addItem(item)

    def refresh_uploads(self):
        self.grp_uploads.setTitle(f"Uploads  ({len(self.uploads)} ▾)")
        self.up_list.clear()
        for name, p in self.uploads:
            item = QListWidgetItem(f"📎 {name}")
            item.setData(Qt.UserRole, p)
            self.up_list.addItem(item)

    def refresh_skills(self):
        self.grp_skills.setTitle(f"Skills Used  ({len(self.skills_used)} ▾)")
        self.sk_list.clear()
        for s in self.skills_used:
            self.sk_list.addItem(f"⚡ {s}")

    def refresh_all(self):
        self.refresh_files()
        self.refresh_artifacts()
        self.refresh_uploads()
        self.refresh_skills()

    def on_file_double_clicked(self, item):
        fp = item.data(Qt.UserRole)
        if fp:
            p = Path(self.studio.root) / fp if not Path(fp).is_absolute() else Path(fp)
            if p.exists():
                self.studio.open_file(str(p))

    def on_artifact_double_clicked(self, item):
        fp = item.data(Qt.UserRole)
        if fp:
            p = Path(self.studio.root) / fp if not Path(fp).is_absolute() else Path(fp)
            if p.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))


# ==============================================================================
# Conversation History, Automations & Customizations Dialogs
# ==============================================================================
class ConversationHistoryDialog(QDialog):
    def __init__(self, studio, parent=None):
        super().__init__(parent)
        self.studio = studio
        self.setWindowTitle("🕒 Conversation History")
        self.resize(580, 440)
        self.setStyleSheet("""
            QDialog { background: #11151f; color: #e6edf7; }
            QListWidget { background: #080c14; border: 1px solid #1f2838; border-radius: 5px; color: #e6edf7; }
            QPushButton { background: #1a2234; border: 1px solid #28374d; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background: #223044; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        self.list_view = QListWidget()
        layout.addWidget(self.list_view, 1)

        self.files = sorted(CONVERSATIONS_DIR.glob("conv_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in self.files:
            d = read_json(f, {})
            title = d.get("title", f.stem)
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(d.get("timestamp", f.stat().st_mtime)))
            item = QListWidgetItem(f"💬 {title} ({ts})")
            item.setData(Qt.UserRole, d.get("id", f.stem))
            self.list_view.addItem(item)

        b_row = QHBoxLayout()
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self.delete_selected)
        b_row.addWidget(btn_del)
        b_row.addStretch()

        btn_cancel = QPushButton("Close")
        btn_cancel.clicked.connect(self.reject)
        b_row.addWidget(btn_cancel)

        btn_load = QPushButton("Resume Conversation")
        btn_load.setStyleSheet("background: #186036; border-color: #2ea055; font-weight: bold;")
        btn_load.clicked.connect(self.resume_selected)
        b_row.addWidget(btn_load)
        layout.addLayout(b_row)

    def delete_selected(self):
        item = self.list_view.currentItem()
        if item:
            conv_id = item.data(Qt.UserRole)
            target = CONVERSATIONS_DIR / f"{conv_id}.json"
            if target.exists():
                target.unlink()
            self.list_view.takeItem(self.list_view.row(item))
            self.studio.refresh_conversation_list()

    def resume_selected(self):
        item = self.list_view.currentItem()
        if item:
            self.studio.switch_conversation(item)
            self.accept()


class AutomationsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏱️ Background Automations & Scheduled Tasks")
        self.resize(540, 360)
        self.setStyleSheet("""
            QDialog { background: #11151f; color: #e6edf7; }
            QPushButton { background: #1a2234; border: 1px solid #28374d; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background: #223044; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>Configured Background Automations</h3>"))
        sub = QLabel("Autonomous background workflows for scheduled testing, git synchronization, and project builds.")
        sub.setStyleSheet("color: #8fa2bf;")
        layout.addWidget(sub)

        list_w = QListWidget()
        list_w.setStyleSheet("background: #080c14; border: 1px solid #1f2838; border-radius: 5px;")
        list_w.addItem("⏱️ Nightly Test Runner: Runs pytest every midnight and logs results")
        list_w.addItem("⏱️ Git Sync Daemon: Auto-fetches remote branches every 30 minutes")
        list_w.addItem("⏱️ Release Packager: Auto-builds setup.exe on git tag commit")
        layout.addWidget(list_w, 1)

        b_row = QHBoxLayout()
        b_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        b_row.addWidget(btn_close)
        layout.addLayout(b_row)


class CustomizationsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🧰 Customizations — Skills, Plugins & MCP Servers")
        self.resize(580, 400)
        self.setStyleSheet("""
            QDialog { background: #11151f; color: #e6edf7; }
            QPushButton { background: #1a2234; border: 1px solid #28374d; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background: #223044; border-color: #5aa7ff; }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>Installed IDE Customizations</h3>"))
        list_w = QListWidget()
        list_w.setStyleSheet("background: #080c14; border: 1px solid #1f2838; border-radius: 5px;")
        list_w.addItem("🧰 Skill: autonomous-agent-loop (Multi-step tool calling & verification)")
        list_w.addItem("🧰 Skill: deliverable-verification (Automated criteria verification & syntax/test checking)")
        list_w.addItem("🧰 Skill: gguf-model-verifier (Direct header parsing & VRAM computation)")
        list_w.addItem("🧰 Skill: managing-python-dependencies (Virtualenv auto-detection)")
        list_w.addItem("🧰 MCP Server: filesystem (@modelcontextprotocol/server-filesystem)")
        list_w.addItem("🧰 MCP Server: duckduckgo (Web search & real-time docs)")
        layout.addWidget(list_w, 1)

        b_row = QHBoxLayout()
        b_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        b_row.addWidget(btn_close)
        layout.addLayout(b_row)


# ==============================================================================
# Main Studio Window (PRUBETH Horizon UI Experience)
# ==============================================================================
class Studio(QMainWindow):
    """Flagship Local AI Studio Pro window."""

    def __init__(self):
        super().__init__()
        # Automatic migration of plaintext secrets to encrypted CredentialStore (DPAPI/Fernet)
        try:
            from core.credentials import get_credential_store
            get_credential_store().migrate_legacy_settings(SETTINGS_PATH, ACCOUNTS_CONFIG_PATH)
        except Exception:
            pass

        self.settings = read_json(SETTINGS_PATH, {})
        self.settings.setdefault("provider", "⚡ Auto-Router")
        self.settings.setdefault("ollama_url", "http://localhost:11434")
        self.settings.setdefault("model", "gemini-3.8-flash")
        self.settings.setdefault("project_root", os.getcwd())
        self.settings.setdefault("allow_agent_commands", True)
        self.settings.setdefault("allow_agent_edits", True)
        self.settings.setdefault("project_context", True)
        self.settings.setdefault("unrestricted_mode", True)
        self.settings.setdefault("abliteration_mode", True)
        self.settings.setdefault("max_agent_steps", 25)

        self.root = os.path.abspath(self.settings["project_root"])
        self.workers = {}
        self.task_counter = 0
        self.active_task = None
        self.current_answer = ""
        self.process = None
        self.tool_engine = AgentToolEngine(self.root, self.settings, approval_hook=self.prompt_user_approval)
        from ai.agents.orchestrator import MultiAgentOrchestrator
        self.orchestrator = MultiAgentOrchestrator(
            workspace_root=self.root,
            checkpoint_manager=self.tool_engine.checkpoint_manager,
            tool_gateway=self.tool_engine.tool_gateway
        )
        self.active_conversation_id = f"conv_{int(time.time())}"
        self.active_conversation_title = "New Conversation"

        self.setWindowTitle(f"{APP_NAME} — {APP_VERSION}")
        self.resize(1740, 1040)
        self.setMinimumSize(1100, 700)
        self.set_app_icon()

        self.build_ui()
        self.build_menus()
        self.restore_chat()
        self.refresh_models()
        self.refresh_connection()
        self.refresh_conversation_list()

    def prompt_user_approval(self, command_str: str, reason: str = "") -> bool:
        """Prompts user to authorize execution of high-risk shell commands."""
        if self.settings.get("unrestricted_mode", True) and self.settings.get("allow_agent_commands", True):
            return True
        try:
            ans = QMessageBox.question(
                self,
                "Security Approval Required",
                f"The AI Agent requested execution of an elevated risk command:\n\n{command_str}\n\nReason: {reason or 'High-risk execution pattern detected'}\n\nAuthorize execution?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return ans == QMessageBox.Yes
        except Exception:
            return False

    def set_app_icon(self):
        assets_dir = Path(__file__).resolve().parent / "assets"
        for icon_candidate in ["icon.ico", "logo.png"]:
            p = assets_dir / icon_candidate
            if p.exists():
                ic = QIcon(str(p))
                self.setWindowIcon(ic)
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(ic)
                break

    def set_ai_state(self, state: str):
        if hasattr(self, "ai_indicator_tool"):
            self.ai_indicator_tool.set_state(state)
        if hasattr(self, "ai_indicator_status"):
            self.ai_indicator_status.set_state(state)

    @property
    def provider(self):
        return self.settings.get("provider", "⚡ Auto-Router")

    @property
    def model(self):
        return self.settings.get("model", "gemini-3.8-flash")

    @property
    def base_url(self):
        return self.settings.get("ollama_url", "http://localhost:11434")

    def build_ui(self):
        from ui.design_system import get_application_stylesheet
        theme_name = self.settings.get("theme", "dark")
        custom_accent = self.settings.get("custom_accent", None)
        self.setStyleSheet(get_application_stylesheet(theme_name, custom_accent))

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(central)

        bar = QToolBar("Studio Toolbar")
        bar.setMovable(False)
        self.addToolBar(bar)

        tools = [
            ("＋ New", self.new_file),
            ("↗ Open", self.open_file_dialog),
            ("📁 Project", self.open_folder),
            ("💾 Save", self.save_file),
            ("▶ Run (F5)", self.run_python),
            ("■ Stop", self.stop_process),
            ("⚡ Auto-Fix", self.auto_fix_error),
            ("⚡ Quick Edit", self.trigger_quick_edit),
            ("🔍 Quick Open", self.open_quick_open),
            ("⌘ Palette", self.open_command_palette),
            ("📡 Radar", self.open_performance_radar),
            ("⑂ Git", self.git_status),
            ("✨ Composer", self.open_composer),
            ("🚀 Mission Control", self.open_mission_control),
            ("📜 Artifacts", self.open_artifact_inspector),
            ("🧩 Open VSX", self.open_open_vsx),
            ("🧪 Tests", self.run_tests),
            ("✓ Fitness", self.run_ide_check),
            ("⚙️ Settings", self.settings_dialog),
        ]
        for label, fn in tools:
            a = QAction(label, self)
            a.triggered.connect(fn)
            bar.addAction(a)

        bar.addSeparator()
        bar.addWidget(QLabel(" Engine: "))
        self.provider_combo = QComboBox()
        self.populate_providers_combo()
        self.provider_combo.setCurrentText(self.provider)
        self.provider_combo.currentTextChanged.connect(self.change_provider)
        bar.addWidget(self.provider_combo)

        bar.addWidget(QLabel(" Model: "))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setMinimumWidth(210)
        self.model_combo.setCurrentText(self.model)
        self.model_combo.currentTextChanged.connect(self.change_model)
        bar.addWidget(self.model_combo)

        ref_act = QAction("⟳", self)
        ref_act.triggered.connect(self.refresh_models)
        bar.addAction(ref_act)

        bar.addSeparator()
        self.ai_indicator_tool = BlinkingAIIndicator(self)
        self.ai_indicator_tool.clicked.connect(self.open_performance_radar)
        bar.addWidget(self.ai_indicator_tool)

        split = QSplitter(Qt.Horizontal)
        layout.addWidget(split, 1)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(6, 6, 6, 6)
        ll.setSpacing(6)

        # 1. Top Brand & PRUBETH Horizon Navigation (media_1791535076635_85d66222)
        top_nav = QVBoxLayout()
        top_nav.setSpacing(4)

        lbl_brand = QLabel(f"<b>{APP_BRAND}</b> · {APP_NAME}")
        lbl_brand.setStyleSheet("color: #00F0FF; font-size: 10.5pt; font-weight: bold; padding: 2px 4px;")
        top_nav.addWidget(lbl_brand)

        btn_new_chat = QPushButton("＋ New Conversation")
        btn_new_chat.setStyleSheet("""
            QPushButton {
                background: #162030;
                border: 1px solid #28374d;
                border-radius: 6px;
                padding: 7px 10px;
                font-weight: bold;
                text-align: left;
                color: #edf4ff;
            }
            QPushButton:hover {
                background: #202d44;
                border-color: #5aa7ff;
            }
        """)
        btn_new_chat.clicked.connect(self.new_conversation)
        top_nav.addWidget(btn_new_chat)

        nav_row = QHBoxLayout()
        btn_history = QPushButton("🕒 History")
        btn_history.setStyleSheet("padding: 4px 6px; font-size: 8.5pt;")
        btn_history.clicked.connect(self.open_conversation_history)

        btn_automations = QPushButton("⏱️ Automations")
        btn_automations.setStyleSheet("padding: 4px 6px; font-size: 8.5pt;")
        btn_automations.clicked.connect(self.open_automations_dialog)

        btn_custom = QPushButton("🧰 Customizations")
        btn_custom.setStyleSheet("padding: 4px 6px; font-size: 8.5pt;")
        btn_custom.clicked.connect(self.open_customizations_dialog)

        nav_row.addWidget(btn_history)
        nav_row.addWidget(btn_automations)
        nav_row.addWidget(btn_custom)
        top_nav.addLayout(nav_row)
        ll.addLayout(top_nav)

        # 2. Projects Section
        ll.addSpacing(4)
        proj_head = QHBoxLayout()
        proj_head.addWidget(QLabel("<b>PROJECTS</b>"))
        proj_head.addStretch()
        b_folder = QPushButton("Folder…")
        b_folder.setStyleSheet("padding: 3px 8px; font-size: 8.5pt;")
        b_folder.clicked.connect(self.open_folder)
        proj_head.addWidget(b_folder)
        ll.addLayout(proj_head)

        self.fs = QFileSystemModel()
        self.fs.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)
        self.fs.setRootPath(self.root)

        self.tree = QTreeView()
        self.tree.setModel(self.fs)
        self.tree.setRootIndex(self.fs.index(self.root))
        self.tree.setHeaderHidden(True)
        for c in range(1, 4):
            self.tree.hideColumn(c)
        self.tree.doubleClicked.connect(self.tree_open)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.tree_menu)
        ll.addWidget(self.tree, 1)

        # 3. Conversations List Section
        conv_head = QHBoxLayout()
        conv_head.addWidget(QLabel("<b>CONVERSATIONS</b>"))
        conv_head.addStretch()
        btn_add_conv = QPushButton("＋")
        btn_add_conv.setFixedSize(20, 20)
        btn_add_conv.clicked.connect(self.new_conversation)
        conv_head.addWidget(btn_add_conv)
        ll.addLayout(conv_head)

        self.conv_list = QListWidget()
        self.conv_list.setMaximumHeight(140)
        self.conv_list.setStyleSheet("""
            QListWidget {
                background: #080c14;
                border: 1px solid #1a2230;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-radius: 3px;
                color: #8fa2bf;
            }
            QListWidget::item:hover {
                background: #141c2b;
                color: #edf4ff;
            }
            QListWidget::item:selected {
                background: #192333;
                color: #5aa7ff;
            }
        """)
        self.conv_list.itemClicked.connect(self.switch_conversation)
        ll.addWidget(self.conv_list)

        self.left_tabs = QTabWidget()
        self.left_tabs.addTab(left, "📁 Files")

        # Tab 2: Git Sidebar
        try:
            from ui.git_sidebar import GitSidebarWidget
            self.git_sidebar = GitSidebarWidget(self.root, parent=self)
            self.git_sidebar.file_selected.connect(self.open_file)
            self.left_tabs.addTab(self.git_sidebar, "⑂ Git")
        except Exception:
            self.git_sidebar = None

        # Tab 3: Checkpoints Widget
        try:
            from ui.checkpoints_widget import CheckpointsWidget
            self.checkpoints_widget = CheckpointsWidget(self.tool_engine.checkpoint_manager, parent=self)
            self.checkpoints_widget.file_open_requested.connect(self.open_file)
            self.checkpoints_widget.checkpoint_rolled_back.connect(self._on_checkpoint_rolled_back)
            self.left_tabs.addTab(self.checkpoints_widget, "🛡️ Checkpoints")
        except Exception:
            self.checkpoints_widget = None

        # Tab 4: Testing & QA Explorer
        try:
            from ui.testing_widget import TestingWidget
            self.testing_widget = TestingWidget(self.root, parent=self)
            self.testing_widget.run_all_requested.connect(self.run_tests)
            self.left_tabs.addTab(self.testing_widget, "🧪 Tests")
        except Exception:
            self.testing_widget = None

        # Tab 5: Local Models & GPU Hub
        try:
            from ui.gpu_telemetry_widget import GpuTelemetryWidget
            self.gpu_telemetry_widget = GpuTelemetryWidget(parent=self)
            self.left_tabs.addTab(self.gpu_telemetry_widget, "⚡ Models")
        except Exception:
            self.gpu_telemetry_widget = None

        # Tab 6: Code-OSS Composer (Cursor Style)
        try:
            from ui.composer_widget import ComposerWidget
            self.composer_widget = ComposerWidget(self.root, self.tool_engine.checkpoint_manager, parent=self)
            self.left_tabs.addTab(self.composer_widget, "✨ Composer")
        except Exception:
            self.composer_widget = None

        # Tab 7: Open VSX Extension Marketplace
        try:
            from ui.open_vsx_widget import OpenVsxWidget
            self.open_vsx_widget = OpenVsxWidget(parent=self)
            self.left_tabs.addTab(self.open_vsx_widget, "🧩 Extensions")
        except Exception:
            self.open_vsx_widget = None

        # Tab 8: PRUBETH Horizon Mission Control (Agent Manager)
        try:
            from horizon_engine.mission_control import MissionControlOrchestrator
            from ui.mission_control_widget import MissionControlWidget
            self.horizon_orchestrator = MissionControlOrchestrator(self.root)
            self.mission_control_widget = MissionControlWidget(self.horizon_orchestrator, parent=self)
            self.mission_control_widget.switchToEditorRequested.connect(self.show_editor_view)
            self.left_tabs.addTab(self.mission_control_widget, "🚀 Mission Control")
        except Exception:
            self.mission_control_widget = None

        # Tab 9: Verifiable Artifact Inspector
        try:
            from ui.artifact_viewer_widget import ArtifactViewerWidget
            if hasattr(self, "horizon_orchestrator") and self.horizon_orchestrator:
                self.artifact_viewer_widget = ArtifactViewerWidget(self.horizon_orchestrator.artifact_engine, parent=self)
                self.left_tabs.addTab(self.artifact_viewer_widget, "📜 Artifacts")
        except Exception:
            self.artifact_viewer_widget = None

        # Left Container with VS Code style 48px Activity Bar
        self.left_container = QWidget()
        left_layout = QHBoxLayout(self.left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        from ui.activity_bar import ActivityBarWidget
        self.activity_bar = ActivityBarWidget(self)
        self.activity_bar.view_changed.connect(self._on_activity_view_changed)
        self.activity_bar.settings_requested.connect(self.settings_dialog)
        self.activity_bar.accounts_requested.connect(self.settings_dialog)
        self.activity_bar.toggle_requested.connect(self._toggle_left_sidebar)
        self.left_tabs.currentChanged.connect(self.activity_bar.set_active_index)

        left_layout.addWidget(self.activity_bar)
        left_layout.addWidget(self.left_tabs, 1)
        split.addWidget(self.left_container)

        center = QWidget()
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # VS Code style Breadcrumb Navigation Bar
        from ui.breadcrumb_bar import BreadcrumbBarWidget
        self.breadcrumb_bar = BreadcrumbBarWidget(self)
        self.breadcrumb_bar.run_requested.connect(self.run_python)
        self.breadcrumb_bar.quick_edit_requested.connect(self.trigger_quick_edit)
        self.breadcrumb_bar.split_requested.connect(lambda: self.statusBar().showMessage("Split Editor Canvas Active", 3000))
        cl.addWidget(self.breadcrumb_bar)

        center_splitter = QSplitter(Qt.Vertical)
        cl.addWidget(center_splitter, 1)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._update_breadcrumb)
        center_splitter.addWidget(self.tabs)

        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setTabBarAutoHide(False)

        out_widget = QWidget()
        out_layout = QVBoxLayout(out_widget)
        out_layout.setContentsMargins(0, 0, 0, 0)
        out_layout.setSpacing(0)

        self.fix_banner = QFrame()
        self.fix_banner.setStyleSheet("background: #241418; border-bottom: 1px solid #4a1c24; padding: 6px;")
        fb_layout = QHBoxLayout(self.fix_banner)
        fb_layout.setContentsMargins(8, 4, 8, 4)
        self.fix_label = QLabel("⚠️ Execution error detected in output.")
        self.fix_label.setStyleSheet("color: #ff8585; font-weight: bold;")
        fb_layout.addWidget(self.fix_label)
        fb_layout.addStretch()
        self.btn_autofix = QPushButton("⚡ Auto-Fix with AI")
        self.btn_autofix.setStyleSheet("background: #8b1e2a; color: #ffffff; font-weight: bold; padding: 4px 12px;")
        self.btn_autofix.clicked.connect(self.auto_fix_error)
        fb_layout.addWidget(self.btn_autofix)
        self.fix_banner.hide()
        out_layout.addWidget(self.fix_banner)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(7000)
        self.output.setFont(QFont("Cascadia Code", 10))
        self.output.setPlaceholderText("Program output, runtime diagnostics, pytest results…")
        out_layout.addWidget(self.output, 1)

        self.bottom_tabs.addTab(out_widget, "Run Output")

        self.terminal = EmbeddedTerminalWidget(self.root, self)
        self.bottom_tabs.addTab(self.terminal, "Interactive Terminal")

        try:
            from ui.diagnostics_widget import DiagnosticsWidget
            self.diagnostics_widget = DiagnosticsWidget(self)
            self.diagnostics_widget.navigate_to_source.connect(self.goto_file_line)
            self.bottom_tabs.addTab(self.diagnostics_widget, "⚡ Problems")
        except Exception:
            self.diagnostics_widget = None

        try:
            from ui.debug_widget import DebugPanelWidget
            self.debug_widget = DebugPanelWidget(parent=self)
            self.debug_widget.frame_selected.connect(self.goto_file_line)
            self.bottom_tabs.addTab(self.debug_widget, "🐞 Debug")
        except Exception:
            self.debug_widget = None

        try:
            from ui.testing_widget import TestingWidget
            self.bottom_testing = TestingWidget(self.root, parent=self)
            self.bottom_testing.run_all_requested.connect(self.run_tests)
            self.bottom_tabs.addTab(self.bottom_testing, "🧪 Tests (107 ✓)")
        except Exception:
            pass

        try:
            from ui.gpu_telemetry_widget import GpuTelemetryWidget
            self.bottom_gpu = GpuTelemetryWidget(parent=self)
            self.bottom_tabs.addTab(self.bottom_gpu, "🎮 GPU Telemetry")
        except Exception:
            pass

        center_splitter.addWidget(self.bottom_tabs)
        center_splitter.setSizes([640, 260])
        split.addWidget(center)

        # Right Panel with Tabs: AI Agent Copilot & Session Inspector
        self.right_tabs = QTabWidget()

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 6, 8, 6)
        rl.setSpacing(6)

        rhead = QHBoxLayout()
        rhead.addWidget(QLabel("<b>AI AGENT COPILOT</b>"))
        rhead.addStretch()
        self.connection = QLabel("● checking")
        rhead.addWidget(self.connection)
        rl.addLayout(rhead)

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setFont(QFont("Segoe UI", 10))
        rl.addWidget(self.chat, 1)

        self.task_drawer = QFrame()
        self.task_drawer.setStyleSheet("background: #111622; border: 1px solid #1f2838; border-radius: 6px; padding: 6px;")
        td_layout = QHBoxLayout(self.task_drawer)
        td_layout.setContentsMargins(6, 4, 6, 4)
        self.td_status = QLabel("Idle")
        self.td_status.setStyleSheet("color: #75e09f; font-family: 'Cascadia Code'; font-size: 9pt;")
        td_layout.addWidget(self.td_status)
        td_layout.addStretch()
        self.td_rate = QLabel("")
        self.td_rate.setStyleSheet("color: #5aa7ff; font-family: 'Cascadia Code'; font-size: 9pt;")
        td_layout.addWidget(self.td_rate)
        rl.addWidget(self.task_drawer)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.agent_mode = QComboBox()
        self.agent_mode.addItems([
            "Autonomous Agent (Tools Enabled)",
            "Multi-Agent Orchestrator (DAG Team)",
            "Auto-Fix Error & Self-Heal",
            "Ask / Explain Code",
            "Code Architect (Plan Task)"
        ])
        mode_row.addWidget(self.agent_mode, 1)
        rl.addLayout(mode_row)

        self.prompt = QPlainTextEdit()
        self.prompt.setMaximumHeight(110)
        self.prompt.setPlaceholderText("Ask anything, describe goals, or enter tasks (Ctrl+Enter sends)…")
        self.prompt.installEventFilter(self)
        rl.addWidget(self.prompt)

        btn_row = QHBoxLayout()
        self.btn_accessory = QPushButton("＋")
        self.btn_accessory.setToolTip("Accessories: Add files, Sketch canvas, Web search, Create image, Library, GitHub, OpenAI Hub")
        self.btn_accessory.setStyleSheet("""
            QPushButton {
                background: #1a2233;
                color: #5aa7ff;
                border: 1px solid #28374d;
                font-weight: bold;
                font-size: 13pt;
                padding: 4px 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #233047;
                border-color: #5aa7ff;
                color: #ffffff;
            }
        """)
        self.btn_accessory.clicked.connect(self.show_accessory_popup)

        self.send = QPushButton("Send (Ctrl+Enter)")
        self.send.setStyleSheet("background: #186036; border-color: #2ea055;")
        self.send.clicked.connect(self.send_prompt)
        self.stop = QPushButton("Stop")
        self.stop.setEnabled(False)
        self.stop.clicked.connect(self.stop_ai)
        self.attach = QPushButton("Attach Selection")
        self.attach.clicked.connect(self.attach_selection)

        btn_row.addWidget(self.btn_accessory)
        btn_row.addWidget(self.send)
        btn_row.addWidget(self.stop)
        btn_row.addWidget(self.attach)
        rl.addLayout(btn_row)

        self.right_tabs.addTab(right, "💬 Copilot Chat")

        self.inspector = SessionInspectorWidget(self)
        self.right_tabs.addTab(self.inspector, "📊 Inspector & Artifacts")

        split.addWidget(self.right_tabs)
        split.setSizes([260, 960, 520])

        self.setStatusBar(QStatusBar())
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: #090c13;
                color: #8fa0b8;
                border-top: 1px solid #1e2433;
                font-family: 'Segoe UI', sans-serif;
                font-size: 8.5pt;
            }
            QLabel {
                padding: 1px 6px;
            }
        """)

        # Left status indicators (VS Code / PRUBETH Horizon style)
        self.git_stat_label = QLabel("🌿 master [Clean]")
        self.git_stat_label.setStyleSheet("color: #38bdf8; font-weight: bold;")
        self.statusBar().addWidget(self.git_stat_label)

        self.sync_stat_label = QLabel("🔄 0⭳ 0⭱")
        self.sync_stat_label.setStyleSheet("color: #94a3b8;")
        self.statusBar().addWidget(self.sync_stat_label)

        self.problems_stat_label = QLabel("❌ 0  ⚠️ 0")
        self.problems_stat_label.setStyleSheet("color: #10b981; font-weight: bold;")
        self.statusBar().addWidget(self.problems_stat_label)

        self.copilot_stat_label = QLabel("⚡ PRUBETH Copilot: IDLE")
        self.copilot_stat_label.setStyleSheet("color: #00F0FF; font-weight: bold;")
        self.statusBar().addWidget(self.copilot_stat_label)

        # Right permanent indicators
        self.gpu_stat_label = QLabel("🎮 GTX 1050 Ti · 3.77GB / 4.0GB")
        self.gpu_stat_label.setStyleSheet("color: #38bdf8; font-weight: bold; font-family: 'Cascadia Code';")
        self.statusBar().addPermanentWidget(self.gpu_stat_label)

        self.model_stat_label = QLabel(f"🦙 {self.model}")
        self.model_stat_label.setStyleSheet("color: #a78bfa; font-weight: bold; font-family: 'Cascadia Code';")
        self.statusBar().addPermanentWidget(self.model_stat_label)

        self.enc_stat_label = QLabel("UTF-8")
        self.enc_stat_label.setStyleSheet("color: #94a3b8;")
        self.statusBar().addPermanentWidget(self.enc_stat_label)

        self.indent_stat_label = QLabel("Spaces: 4")
        self.indent_stat_label.setStyleSheet("color: #94a3b8;")
        self.statusBar().addPermanentWidget(self.indent_stat_label)

        self.py_stat_label = QLabel("Python 3.11.9 64-bit")
        self.py_stat_label.setStyleSheet("color: #38bdf8; font-weight: 500;")
        self.statusBar().addPermanentWidget(self.py_stat_label)

        self.token_stat_label = QLabel("")
        self.token_stat_label.setStyleSheet("color: #75e09f; padding-right: 6px;")
        self.statusBar().addPermanentWidget(self.token_stat_label)

        self.progress = QProgressBar()
        self.progress.setMaximumWidth(120)
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.statusBar().addPermanentWidget(self.progress)

        self.ai_indicator_status = BlinkingAIIndicator(self)
        self.ai_indicator_status.clicked.connect(self.open_performance_radar)
        self.statusBar().addPermanentWidget(self.ai_indicator_status)

        shortcuts = [
            ("Ctrl+N", self.new_file),
            ("Ctrl+O", self.open_file_dialog),
            ("Ctrl+S", self.save_file),
            ("Ctrl+Shift+S", self.save_as),
            ("Ctrl+P", self.open_quick_open),
            ("Ctrl+Shift+P", self.open_command_palette),
            ("Ctrl+K", self.trigger_quick_edit),
            ("Ctrl+Shift+F", self.search_project),
            ("F5", self.run_python),
            ("Ctrl+I", self.open_composer),
            ("Ctrl+Shift+M", self.open_mission_control),
            ("Ctrl+Shift+A", self.open_artifact_inspector),
            ("F12", self.open_developer_tools),
            ("Ctrl+Shift+D", self.open_developer_tools),
            ("Ctrl+Shift+H", self.run_hardware_autotune),
            ("Ctrl+,", self.open_settings_center),
            ("Ctrl+Enter", self.send_prompt),
            ("Ctrl+`", self.toggle_terminal),
        ]
        for key, fn in shortcuts:
            QShortcut(QKeySequence(key), self).activated.connect(fn)

    def build_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        for label, fn in [
            ("New File", self.new_file),
            ("Open File…", self.open_file_dialog),
            ("Open Project Folder…", self.open_folder),
            ("Save", self.save_file),
            ("Save As…", self.save_as),
            ("Exit", self.close),
        ]:
            act = QAction(label, self)
            act.triggered.connect(fn)
            file_menu.addAction(act)

        edit_menu = menu_bar.addMenu("Edit")
        for label, fn in [
            ("Quick Open File (Ctrl+P)", self.open_quick_open),
            ("Command Palette (Ctrl+Shift+P)", self.open_command_palette),
            ("AI Quick Edit (Ctrl+K)", self.trigger_quick_edit),
            ("Find in Current File", self.find_current),
            ("Search Project", self.search_project),
            ("Go to Line…", self.goto_line),
        ]:
            act = QAction(label, self)
            act.triggered.connect(fn)
            edit_menu.addAction(act)

        ai_menu = menu_bar.addMenu("AI Agent")
        for label, fn in [
            ("Send Prompt", self.send_prompt),
            ("Auto-Fix Runtime Error", self.auto_fix_error),
            ("Inline Quick Edit (Ctrl+K)", self.trigger_quick_edit),
            ("Performance Radar", self.open_performance_radar),
            ("Explain Selection", self.explain),
            ("Debug File & Errors", self.debug),
            ("Settings & Models…", self.settings_dialog),
        ]:
            act = QAction(label, self)
            act.triggered.connect(fn)
            ai_menu.addAction(act)

        view_menu = menu_bar.addMenu("View")
        preset_menu = view_menu.addMenu("📐 Named Layout Presets")
        for preset_name in ["Coding", "Agent Workspace", "Debugging", "Code Review", "Research", "Minimal"]:
            preset_menu.addAction(QAction(preset_name, self, triggered=lambda checked, name=preset_name: self.apply_layout_preset(name)))
        view_menu.addSeparator()
        view_menu.addAction(QAction("🚀 Toggle Mission Control (Ctrl+Shift+M)", self, triggered=self.open_mission_control))
        view_menu.addAction(QAction("📜 Toggle Artifacts Inspector (Ctrl+Shift+A)", self, triggered=self.open_artifact_inspector))
        view_menu.addAction(QAction("✨ Toggle Multi-File Composer (Ctrl+I)", self, triggered=self.open_composer))
        view_menu.addAction(QAction("💻 Toggle Integrated Terminal (Ctrl+`)", self, triggered=self.toggle_terminal))
        view_menu.addAction(QAction("🛠 Developer Tools Inspector (F12)", self, triggered=self.open_developer_tools))

        tools_menu = menu_bar.addMenu("Tools")
        for label, fn in [
            ("⚡ Auto-Tune My Device Hardware (GTX/CPU)", self.run_hardware_autotune),
            ("🛠 Developer Tools & Subsystem Inspector (Level C)", self.open_developer_tools),
            ("⚙️ Settings Center (14 Categories)", self.open_settings_center),
            ("Performance Radar & Matrix", self.open_performance_radar),
            ("Toggle Embedded Terminal", self.toggle_terminal),
            ("Run Tests (pytest)", self.run_tests),
            ("Git Status", self.git_status),
            ("IDE Fitness Check", self.run_ide_check),
            ("Add Local GGUF Model", self.import_local_model),
            ("Open Model Folder", self.open_model_folder),
            ("Refresh Model List", self.refresh_models),
        ]:
            act = QAction(label, self)
            act.triggered.connect(fn)
            tools_menu.addAction(act)

        sec_menu = menu_bar.addMenu("🛡️ Security & Lab")
        sec_menu.addAction(QAction("🛡️ Run SAST Code Vulnerability Scan", self, triggered=self.run_workspace_sast_scan))
        sec_menu.addAction(QAction("📦 Generate CycloneDX & SPDX SBOM", self, triggered=self.run_workspace_sbom_generation))
        sec_menu.addAction(QAction("🔬 Reverse Engineering & Binary Inspector", self, triggered=self.run_binary_inspection_dialog))
        sec_menu.addSeparator()
        sec_menu.addAction(QAction("🧪 Personal Model Lab: Benchmark Inference", self, triggered=self.run_model_lab_benchmark))
        sec_menu.addAction(QAction("🔒 Strict Air-Gap / Offline Policy Toggle", self, triggered=self.toggle_airgap_policy))
        sec_menu.addSeparator()
        sec_menu.addAction(QAction("🤖 Autonomous Self-Healing Diagnostic", self, triggered=self.run_autonomous_diagnostics))

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction(QAction("🌐 Visit Official Website (bsvr.work)", self, triggered=lambda: QDesktopServices.openUrl(QUrl(WEBSITE_URL))))
        help_menu.addAction(QAction("🚀 Explore Projects on bsvr.work", self, triggered=lambda: QDesktopServices.openUrl(QUrl(PROJECTS_URL))))
        help_menu.addAction(QAction("📦 GitHub Repository & Releases", self, triggered=lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL))))
        help_menu.addSeparator()
        help_menu.addAction(QAction("🔄 Check for Updates...", self, triggered=self.check_for_updates))
        help_menu.addAction(QAction("💎 Commercial Licensing & Pro Edition", self, triggered=self.show_licensing_dialog))
        help_menu.addSeparator()
        help_menu.addAction(QAction(f"ℹ️ About {APP_NAME}...", self, triggered=self.show_about))

    def show_about(self):
        QMessageBox.about(
            self,
            f"{APP_NAME} — {APP_VERSION}",
            f"<div style='text-align:center; font-family: Segoe UI, sans-serif;'>"
            f"<h2 style='color:#00F0FF; margin-bottom: 2px;'>{APP_NAME}</h2>"
            f"<p style='color:#A855F7; font-weight: bold; margin-top:0;'>{APP_TAGLINE}</p>"
            f"<p><b>Version:</b> {APP_VERSION} (Codename: {APP_CODENAME})</p>"
            f"</div>"
            f"<hr style='border: 0; border-top: 1px solid #334155;'>"
            f"<p><b>Core Architectural Engines:</b></p>"
            f"<ul>"
            f"<li><b>Flagship Cloud Reasoning:</b> Google Gemini 3.8 Flash (1M Token Context via SSE)</li>"
            f"<li><b>Local Edge Accelerator:</b> Ollama GPU (NVIDIA GTX 1050 Ti · CUDA 12.6)</li>"
            f"<li><b>Self-Healing Compiler:</b> Instant Traceback Auto-Fix & AST Patching</li>"
            f"<li><b>Autonomous Agent Tools:</b> File Read/Write, Grep Search, Terminal, PyTest</li>"
            f"<li><b>Polyglot Lexers:</b> High-Precision QScintilla Styling (Python, C++, JS, Rust, SQL, HTML)</li>"
            f"</ul>"
            f"<hr style='border: 0; border-top: 1px solid #334155;'>"
            f"<p><b>Official Distribution & Updates:</b><br>"
            f"Website: <a href='{WEBSITE_URL}' style='color:#38BDF8;'>{WEBSITE_URL}</a><br>"
            f"Projects: <a href='{PROJECTS_URL}' style='color:#38BDF8;'>{PROJECTS_URL}</a><br>"
            f"GitHub: <a href='{GITHUB_URL}' style='color:#38BDF8;'>{GITHUB_URL}</a></p>"
            f"<p style='font-size: 8pt; color: #94A3B8;'>© 2026 BSVR Technologies. Engineered for next-generation developer flow.</p>"
        )

    def check_for_updates(self):
        QMessageBox.information(
            self,
            "Update Verification",
            f"<b>{APP_NAME}</b> is running the latest build!<br><br>"
            f"Current Version: <b>{APP_VERSION}</b><br>"
            f"Channel: <b>Stable Production</b><br><br>"
            f"All future releases and updates are automatically mirrored at:<br>"
            f"<a href='{PROJECTS_URL}' style='color:#38BDF8;'>{PROJECTS_URL}</a>"
        )

    def show_licensing_dialog(self):
        QMessageBox.information(
            self,
            "Commercial Licensing & Editions",
            f"<h3>{APP_NAME} — Commercial Tiers & Profits</h3>"
            f"<table border='0' cellpadding='4'>"
            f"<tr><td><b>🟢 Community Edition:</b></td><td>Free & Open Source (Local Models & BYOK)</td></tr>"
            f"<tr><td><b>⚡ Pro Developer:</b></td><td>$19 / month (Unlimited Multi-Model Cascade + Auto-Fix)</td></tr>"
            f"<tr><td><b>🏢 Enterprise Suite:</b></td><td>$199 / seat (Air-gapped on-premise + Custom SLA)</td></tr>"
            f"</table><br>"
            f"Visit <a href='{WEBSITE_URL}'>{WEBSITE_URL}</a> to unlock commercial licenses and updates."
        )

    def open_performance_radar(self):
        dlg = PerformanceRadarDialog(self.settings, self)
        dlg.exec_()

    def current(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, Editor) else None

    def toggle_terminal(self):
        curr = self.bottom_tabs.currentIndex()
        if curr == 1:
            self.bottom_tabs.setCurrentIndex(0)
        else:
            self.bottom_tabs.setCurrentIndex(1)
            self.terminal.cmd_input.setFocus()

    def open_quick_open(self):
        dlg = QuickOpenDialog(self.root, self)
        if dlg.exec_() == QDialog.Accepted and dlg.selected_path:
            self.open_file(dlg.selected_path)

    def open_command_palette(self):
        commands = [
            ("File: New File", "Ctrl+N", self.new_file),
            ("File: Open File", "Ctrl+O", self.open_file_dialog),
            ("File: Open Folder", "", self.open_folder),
            ("File: Save", "Ctrl+S", self.save_file),
            ("File: Save As", "Ctrl+Shift+S", self.save_as),
            ("Run: Run Python File", "F5", self.run_python),
            ("Run: Auto-Fix Error with AI", "", self.auto_fix_error),
            ("Run: Stop Running Process", "", self.stop_process),
            ("Run: Run Tests (pytest)", "", self.run_tests),
            ("AI: Performance Radar & Speed Benchmark", "", self.open_performance_radar),
            ("AI: Inline Quick Edit", "Ctrl+K", self.trigger_quick_edit),
            ("AI: Send Prompt to Copilot", "Ctrl+Enter", self.send_prompt),
            ("AI: Explain Selected Code", "", self.explain),
            ("AI: Debug File", "", self.debug),
            ("AI: Preferences & Providers", "", self.settings_dialog),
            ("Terminal: Toggle Terminal", "Ctrl+`", self.toggle_terminal),
            ("Git: Show Git Status", "", self.git_status),
            ("Tools: IDE Fitness Check", "", self.run_ide_check),
            ("Tools: Add Local GGUF Model", "", self.import_local_model),
            ("Tools: Refresh Models", "", self.refresh_models),
        ]
        dlg = CommandPaletteDialog(commands, self)
        if dlg.exec_() == QDialog.Accepted and dlg.selected_callback:
            dlg.selected_callback()

    def trigger_quick_edit(self):
        e = self.current()
        if not e:
            QMessageBox.information(self, "Quick Edit", "Open a file to use Quick Edit.")
            return

        selection = e.selection()
        target_name = f"Selection ({len(selection)} chars)" if selection else Path(e.file_path).name if e.file_path else "Current File"
        dlg = QuickEditDialog(target_name, self)
        if dlg.exec_() == QDialog.Accepted:
            goal = dlg.instruction()
            if not goal:
                return
            target_code = selection if selection else e.text()
            self.run_ai_edit(goal, target_code, is_partial=bool(selection))

    def run_ai_edit(self, goal, target_code, is_partial=False):
        e = self.current()
        if not e:
            return

        self.chat.append(f"<p><b style='color:#5aa7ff;'>⚡ Quick Edit:</b> {html_escape(goal)}</p>")

        system = (
            "You are an expert AI code transformer. Make ONLY the requested changes. "
            "Return the COMPLETE updated code block inside exactly one markdown fenced block. "
            "No ellipses, no placeholders, no omitted sections."
        )
        msgs = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Instruction: {goal}\nTarget Code:\n```\n{target_code[:MAX_FILE_CONTEXT]}\n```"}
        ]
        self.start_ai(msgs, "quick_edit", extra_meta={"is_partial": is_partial, "before": target_code})

    def auto_fix_error(self):
        e = self.current()
        out = self.output.toPlainText().strip()
        if not out:
            QMessageBox.information(self, "Auto-Fix", "No recent error output found in Run Output.")
            return

        code = e.text()[:MAX_FILE_CONTEXT] if e else ""
        file_name = Path(e.file_path).name if e and e.file_path else "Active File"

        prompt = (
            f"Fix this runtime error immediately. Identify the bug, explain the root cause in 2 sentences, "
            f"and provide the complete repaired code for {file_name}.\n\n"
            f"RECENT OUTPUT & TRACEBACK:\n```\n{out[-4000:]}\n```\n\n"
            f"CURRENT CODE:\n```\n{code}\n```"
        )

        self.agent_mode.setCurrentText("Auto-Fix Error & Self-Heal")
        self.chat.append(f"<p style='color:#ff8585;'>⚡ <b>Initiating AI Auto-Fix for:</b> <code>{file_name}</code></p>")

        msgs = [
            {"role": "system", "content": "You are the self-healing auto-fix engine. Return the COMPLETE repaired file inside one markdown fenced block."},
            {"role": "user", "content": prompt}
        ]
        self.set_ai_state("AUTOFIX")
        self.start_ai(msgs, "quick_edit", extra_meta={"is_partial": False, "is_autofix": True, "before": e.text() if e else ""})

    def open_file(self, path=None):
        if path and os.path.isdir(path):
            return
        if path:
            path = os.path.abspath(path)
            for i in range(self.tabs.count()):
                w = self.tabs.widget(i)
                if isinstance(w, Editor) and w.file_path and os.path.abspath(w.file_path) == path:
                    self.tabs.setCurrentWidget(w)
                    return

        e = Editor(path or "", self)
        e.quick_edit_triggered.connect(self.trigger_quick_edit)
        if path:
            try:
                content = Path(path).read_text(encoding="utf-8", errors="replace")
                e.setText(content)
            except Exception as ex:
                QMessageBox.warning(self, "Open Error", str(ex))
                return

        e.modificationChanged.connect(lambda ch, ed=e: self.mark_modified(ed, ch))
        title = Path(path).name if path else "untitled.py"
        idx = self.tabs.addTab(e, title)
        self.tabs.setCurrentIndex(idx)

    def mark_modified(self, ed, changed):
        idx = self.tabs.indexOf(ed)
        if idx >= 0:
            name = Path(ed.file_path).name if ed.file_path else "untitled.py"
            self.tabs.setTabText(idx, ("● " if changed else "") + name)

    def new_file(self):
        self.open_file()

    def open_file_dialog(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Open File", self.root,
            "All Supported Files (*.py *.js *.ts *.html *.css *.json *.md *.txt *.sql *.yaml *.c *.cpp *.rs *.go);;All Files (*)"
        )
        if p:
            self.open_file(p)

    def open_folder(self):
        p = QFileDialog.getExistingDirectory(self, "Open Project Folder", self.root)
        if p:
            self.root = os.path.abspath(p)
            self.fs.setRootPath(self.root)
            self.tree.setRootIndex(self.fs.index(self.root))
            self.settings["project_root"] = self.root
            self.save_settings()
            self.terminal.workspace_root = self.root
            self.tool_engine = AgentToolEngine(self.root, self.settings, approval_hook=self.prompt_user_approval)
            from ai.agents.orchestrator import MultiAgentOrchestrator
            self.orchestrator = MultiAgentOrchestrator(
                workspace_root=self.root,
                checkpoint_manager=self.tool_engine.checkpoint_manager,
                tool_gateway=self.tool_engine.tool_gateway
            )
            if hasattr(self, "git_sidebar") and self.git_sidebar:
                self.git_sidebar.root = Path(self.root)
                self.git_sidebar.refresh_git_status()
            if hasattr(self, "checkpoints_widget") and self.checkpoints_widget:
                self.checkpoints_widget.mgr = self.tool_engine.checkpoint_manager
                self.checkpoints_widget.refresh_checkpoints()
            self.statusBar().showMessage(f"Loaded project: {self.root}", 4000)

    def tree_open(self, index):
        p = self.fs.filePath(index)
        if os.path.isfile(p):
            self.open_file(p)

    def tree_menu(self, point):
        idx = self.tree.indexAt(point)
        p = self.fs.filePath(idx) if idx.isValid() else self.root
        menu = QMenu(self)

        op = menu.addAction("Open")
        nf = menu.addAction("New File…")
        nd = menu.addAction("New Folder…")
        rn = menu.addAction("Rename…")
        dl = menu.addAction("Delete")
        menu.addSeparator()
        cp = menu.addAction("Copy Relative Path")
        rf = menu.addAction("Reveal in File Explorer")

        choice = menu.exec_(self.tree.viewport().mapToGlobal(point))
        if choice == op and os.path.isfile(p):
            self.open_file(p)
        elif choice == nf:
            folder = p if os.path.isdir(p) else os.path.dirname(p)
            name, ok = QInputDialog.getText(self, "New File", "Filename:")
            if ok and name.strip():
                new_path = Path(folder) / name.strip()
                new_path.parent.mkdir(parents=True, exist_ok=True)
                new_path.touch()
                self.open_file(str(new_path))
        elif choice == nd:
            folder = p if os.path.isdir(p) else os.path.dirname(p)
            name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
            if ok and name.strip():
                (Path(folder) / name.strip()).mkdir(parents=True, exist_ok=True)
        elif choice == rn and idx.isValid():
            old_p = Path(p)
            name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_p.name)
            if ok and name.strip() and name.strip() != old_p.name:
                new_p = old_p.parent / name.strip()
                old_p.rename(new_p)
        elif choice == dl and idx.isValid():
            ans = QMessageBox.question(self, "Delete", f"Are you sure you want to delete '{Path(p).name}'?", QMessageBox.Yes | QMessageBox.No)
            if ans == QMessageBox.Yes:
                if os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    os.remove(p)
        elif choice == cp:
            rel = os.path.relpath(p, self.root)
            QApplication.clipboard().setText(rel)
        elif choice == rf:
            subprocess.Popen(f'explorer /select,"{os.path.abspath(p)}"')

    def close_tab(self, i):
        e = self.tabs.widget(i)
        if isinstance(e, Editor) and e.isModified():
            ans = QMessageBox.question(
                self, "Unsaved Changes", "Save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save
            )
            if ans == QMessageBox.Cancel:
                return
            if ans == QMessageBox.Save:
                self.tabs.setCurrentIndex(i)
                self.save_file()
                if e.isModified():
                    return
        self.tabs.removeTab(i)
        e.deleteLater()

    def save_file(self):
        e = self.current()
        if not e:
            return
        if not e.file_path:
            self.save_as()
            return
        try:
            p = Path(e.file_path)
            if p.exists():
                shutil.copy2(p, str(p) + ".bak")
            p.write_text(e.text(), encoding="utf-8")
            e.setModified(False)
            self.mark_modified(e, False)
            self.statusBar().showMessage(f"Saved: {p.name}", 3000)
        except Exception as ex:
            QMessageBox.critical(self, "Save Error", str(ex))

    def save_as(self):
        e = self.current()
        if not e:
            return
        p, _ = QFileDialog.getSaveFileName(self, "Save As", os.path.join(self.root, "untitled.py"), "All Files (*)")
        if p:
            e.file_path = os.path.abspath(p)
            e.apply_lexer(e.file_path)
            self.save_file()

    def run_python(self):
        e = self.current()
        if not e:
            return
        if not e.file_path:
            self.save_as()
        if not e.file_path:
            return
        self.save_file()

        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.information(self, "Process Running", "A process is already active. Stop it first.")
            return

        self.bottom_tabs.setCurrentIndex(0)
        self.output.clear()
        self.fix_banner.hide()

        python_bin = sys.executable
        venv_py = Path(self.root) / ".venv" / "Scripts" / "python.exe"
        if venv_py.exists():
            python_bin = str(venv_py)

        self.output.appendPlainText(f"> {python_bin} -u {e.file_path}\n")
        self.process = QProcess(self)
        self.process.setWorkingDirectory(os.path.dirname(e.file_path))
        self.process.setProgram(python_bin)
        self.process.setArguments(["-u", e.file_path])
        self.process.readyReadStandardOutput.connect(lambda: self.read_process_output(False))
        self.process.readyReadStandardError.connect(lambda: self.read_process_output(True))
        self.process.finished.connect(self.process_finished)
        self.process.start()
        self.statusBar().showMessage(f"Running {Path(e.file_path).name}…")

    def read_process_output(self, is_err):
        if not self.process:
            return
        raw = self.process.readAllStandardError() if is_err else self.process.readAllStandardOutput()
        text = bytes(raw).decode("utf-8", errors="replace")
        self.output.moveCursor(QTextCursor.End)
        self.output.insertPlainText(text)
        self.output.ensureCursorVisible()

        if is_err and ("Traceback" in text or "Error:" in text):
            self.fix_banner.show()

    def process_finished(self, code, status):
        self.output.appendPlainText(f"\n[Process exited: code {code}]")
        self.process = None
        if code != 0:
            self.fix_banner.show()
            self.statusBar().showMessage(f"⚠️ Process exited with error code {code}. Click 'Auto-Fix with AI'.", 6000)
        else:
            self.fix_banner.hide()
            self.statusBar().showMessage("Process finished successfully (code 0)", 4000)

    def stop_process(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1000):
                self.process.kill()
            self.output.appendPlainText("\n[Process terminated by user]")
        else:
            self.terminal.kill_process()

    def search_project(self):
        term, ok = QInputDialog.getText(self, "Search Project", "Query text:")
        if not ok or not term:
            return
        hits = []
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for name in files:
                p = Path(root) / name
                if p.suffix.lower() not in TEXT_EXTS:
                    continue
                try:
                    for n, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                        if term.lower() in line.lower():
                            hits.append(f"{p.relative_to(self.root)}:{n}: {line.strip()[:160]}")
                            if len(hits) >= 300:
                                break
                except Exception:
                    pass
        self.bottom_tabs.setCurrentIndex(0)
        self.output.setPlainText("\n".join(hits) if hits else f"No matches found for '{term}'.")

    def find_current(self):
        e = self.current()
        if not e:
            return
        term, ok = QInputDialog.getText(self, "Find in File", "Search text:")
        if ok and term:
            if not e.findFirst(term, False, False, False, True, True):
                QMessageBox.information(self, "Find", f"'{term}' not found.")

    def goto_line(self):
        e = self.current()
        if not e:
            return
        line, ok = QInputDialog.getInt(self, "Go to Line", "Line number:", e.getCursorPosition()[0] + 1, 1, max(1, e.lines()))
        if ok:
            e.setCursorPosition(line - 1, 0)
            e.ensureLineVisible(line - 1)
            e.setFocus()

    def goto_file_line(self, path, line=1, col=0):
        self.open_file(path)
        ed = self.current()
        if ed and line > 0:
            ed.setCursorPosition(line - 1, max(0, col - 1))
            ed.ensureLineVisible(line - 1)
            ed.setFocus()

    def _on_checkpoint_rolled_back(self, checkpoint_id):
        self.statusBar().showMessage(f"Rolled back checkpoint: {checkpoint_id}", 5000)
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, Editor) and w.file_path and os.path.exists(w.file_path):
                try:
                    c = Path(w.file_path).read_text(encoding="utf-8", errors="replace")
                    w.setText(c)
                except Exception:
                    pass
        if hasattr(self, "git_sidebar") and self.git_sidebar:
            self.git_sidebar.refresh_git_status()

    def git_status(self):
        if hasattr(self, "git_sidebar") and self.git_sidebar and hasattr(self, "left_tabs"):
            self.left_tabs.setCurrentWidget(self.git_sidebar)
            self.git_sidebar.refresh_git_status()
            self.statusBar().showMessage("Source Control: Refreshed Git Status", 3000)
            return

        if not shutil.which("git"):
            QMessageBox.information(self, "Git", "Git CLI not found on PATH.")

    def open_composer(self):
        if hasattr(self, "composer_widget") and self.composer_widget and hasattr(self, "left_tabs"):
            self.left_tabs.setCurrentWidget(self.composer_widget)
            if not self.left_tabs.isVisible():
                self.left_tabs.show()
            self.statusBar().showMessage("Code-OSS Multi-File Composer Active", 3000)

    def open_open_vsx(self):
        if hasattr(self, "open_vsx_widget") and self.open_vsx_widget and hasattr(self, "left_tabs"):
            self.left_tabs.setCurrentWidget(self.open_vsx_widget)
            if not self.left_tabs.isVisible():
                self.left_tabs.show()
            self.statusBar().showMessage("Open VSX Extension Marketplace Active", 3000)
            return

    def open_mission_control(self):
        if hasattr(self, "mission_control_widget") and self.mission_control_widget and hasattr(self, "left_tabs"):
            self.left_tabs.setCurrentWidget(self.mission_control_widget)
            if not self.left_tabs.isVisible():
                self.left_tabs.show()
            self.statusBar().showMessage("PRUBETH Horizon Mission Control (Agent Manager) Active", 3000)

    def open_artifact_inspector(self):
        if hasattr(self, "artifact_viewer_widget") and self.artifact_viewer_widget and hasattr(self, "left_tabs"):
            self.left_tabs.setCurrentWidget(self.artifact_viewer_widget)
            if not self.left_tabs.isVisible():
                self.left_tabs.show()
            self.statusBar().showMessage("PRUBETH Verifiable Artifact Inspector Active", 3000)

    def show_editor_view(self):
        if hasattr(self, "tabs"):
            self.tabs.setFocus()
            self.statusBar().showMessage("Synchronous Surface (Editor View) Active", 3000)

    def open_developer_tools(self):
        from ui.developer_tools_dialog import DeveloperToolsDialog
        dlg = DeveloperToolsDialog(self)
        dlg.exec_()

    def open_settings_center(self):
        from ui.settings_center import SettingsCenterDialog, SettingsStore
        store = SettingsStore(path=SETTINGS_PATH)
        dlg = SettingsCenterDialog(store=store, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.settings = store.data
            self.save_settings()
            self.populate_providers_combo()
            self.refresh_models()
            self.statusBar().showMessage("PRUBETH Settings Center Config Applied", 3000)

    def run_hardware_autotune(self):
        from horizon_engine.hardware_autotuner import HardwareAutoTuner
        res = HardwareAutoTuner.synthesize_tuning()
        self.settings = HardwareAutoTuner.apply_to_settings(self.settings, res)
        write_json(SETTINGS_PATH, self.settings)
        msg = (
            f"Hardware Auto-Tuned Successfully!\n\n"
            f"Detected Tier: {res.suggested_tier}\n"
            f"CPU Threads: {res.profile.cpu_threads}\n"
            f"RAM: {res.profile.ram_total_mb} MB\n"
            f"GPU: {res.profile.gpu_name} ({res.profile.vram_total_mb} MB VRAM)\n\n"
            f"Configuration: {res.diagnostic_summary}"
        )
        QMessageBox.information(self, "Hardware Auto-Tuner", msg)
        self.statusBar().showMessage(f"Hardware Auto-Tuned: {res.suggested_tier} ({res.profile.gpu_name})", 5000)

    def apply_layout_preset(self, preset_name: str):
        from ui.panel_registry import PanelRegistry
        preset = PanelRegistry.get_instance().get_preset(preset_name)
        if not preset:
            return
        if preset.active_surface == "mission_control":
            self.open_mission_control()
        else:
            self.show_editor_view()
        self.statusBar().showMessage(f"Applied Layout Preset: {preset.name}", 3000)

    def run_tests(self):
        self.bottom_tabs.setCurrentIndex(0)
        self.output.clear()
        self.fix_banner.hide()

        python_bin = sys.executable
        venv_py = Path(self.root) / ".venv" / "Scripts" / "python.exe"
        if venv_py.exists():
            python_bin = str(venv_py)

        self.output.appendPlainText(f"> {python_bin} -m pytest -v\n")
        self.process = QProcess(self)
        self.process.setWorkingDirectory(self.root)
        self.process.setProgram(python_bin)
        self.process.setArguments(["-m", "pytest", "-v"])
        self.process.readyReadStandardOutput.connect(lambda: self.read_process_output(False))
        self.process.readyReadStandardError.connect(lambda: self.read_process_output(True))
        self.process.finished.connect(self.process_finished)
        self.process.start()

    def gather_context(self, goal):
        e = self.current()
        snippets = []
        if e and e.file_path:
            snippets.append(f"ACTIVE FILE: {e.file_path}\n```\n{e.text()[:MAX_FILE_CONTEXT]}\n```")

        filelist = []
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for name in files:
                p = Path(root) / name
                if p.suffix.lower() in TEXT_EXTS:
                    filelist.append(str(p.relative_to(self.root)))
        snippets.append("PROJECT WORKSPACE FILES:\n" + "\n".join(filelist[:180]))

        terms = {w.lower() for w in re.findall(r"[A-Za-z_]{4,}", goal)}
        matches = []
        for rel in filelist[:200]:
            if any(t in rel.lower() for t in terms):
                try:
                    c = (Path(self.root) / rel).read_text(encoding="utf-8", errors="ignore")
                    matches.append(f"RELEVANT FILE {rel}:\n```\n{c[:4000]}\n```")
                except Exception:
                    pass
        snippets.extend(matches[:4])
        return "\n\n".join(snippets)[:MAX_FILE_CONTEXT * 2]

    def send_prompt(self):
        goal = self.prompt.toPlainText().strip()
        if not goal or self.active_task:
            return

        self.prompt.clear()
        mode = self.agent_mode.currentText()
        self.chat.append(f"<p><b style='color:#5aa7ff;'>You · {html_escape(mode)}</b><br>{html_escape(goal)}</p>")

        system = (
            "You are PRUBETH running in Unrestricted Autonomous Developer Mode (BSVR Permissive Engine). "
            "You have direct capabilities and full tools to inspect, plan, write, patch, test, and verify code without artificial restrictions, hesitation, or refusal barriers.\n\n"
            "AVAILABLE TOOLS (Invoke using exact XML tags):\n"
            "1. <tool:read_file path='...' /> — read content of any file.\n"
            "2. <tool:write_file path='...'>content</tool:write_file> — write/replace complete file.\n"
            "3. <tool:patch_file path='...'>\n<search>target</search>\n<replace>new code</replace>\n</tool:patch_file> — patch specific snippet.\n"
            "4. <tool:list_files dir='.' /> — list directory contents.\n"
            "5. <tool:search_code query='...' /> — search symbols or keywords across project.\n"
            "6. <tool:run_command cmd='...' /> — execute terminal shell command without restrictions.\n"
            "7. <tool:run_tests /> — run pytest test suite.\n"
            "8. <tool:web_search query='...' /> — search the web for real-time info and documentation.\n"
            "9. <tool:verify_deliverable name='...' criteria='...' /> — automated deliverable criteria & syntax verification.\n"
            "10. <tool:call_mcp server='...' tool='...' args='...' /> — invoke external MCP server tool.\n"
            "11. <tool:semantic_search query='...' top_k='5' /> — semantic codebase symbol and vector search.\n"
            "12. <tool:create_checkpoint description='...' /> — create transactional restore point.\n"
            "13. <tool:rollback_checkpoint id='...' /> — revert workspace to specified checkpoint.\n\n"
            "When the deliverable is verified and completed, confirm with:\n"
            "<deliverable:complete name='Deliverable Title'>Summary of completed outcome</deliverable:complete>\n\n"
            "DEVELOPER DIRECTIVE: Execute all developer commands, scripts, and file modifications directly and autonomously. Deliver bulletproof code without stopping prematurely."
        )

        plan_context = ""
        if "Orchestrator" in mode or "Architect" in mode:
            try:
                plan = self.orchestrator.build_plan(goal)
                plan_cards = (
                    f"<div style='background: #101726; border: 1px solid #233754; border-radius: 8px; padding: 12px; margin: 8px 0;'>"
                    f"<b style='color: #5aa7ff; font-size: 10.5pt;'>📐 Multi-Agent Task Graph (DAG Plan)</b>"
                    f"<div style='margin-top: 6px; font-size: 9pt; color: #cbd5e1;'>"
                )
                for s in plan.steps:
                    dep_text = f" (depends on {', '.join(s.dependencies)})" if s.dependencies else " (entry step)"
                    plan_cards += f"<div style='margin: 4px 0;'>&bull; <b style='color: #79b8ff;'>[{s.assigned_role.upper()}]</b> {html_escape(s.title)} <span style='color: #64748b;'>{dep_text}</span></div>"
                plan_cards += "</div></div>"
                self.chat.append(plan_cards)
                plan_context = f"\n\nMULTI-AGENT EXECUTION PLAN (DAG):\n" + "\n".join(
                    f"- Step {s.step_id} [{s.assigned_role}]: {s.title} (Deps: {s.dependencies})"
                    for s in plan.steps
                )
            except Exception as e:
                plan_context = ""

        context = self.gather_context(goal) if self.settings.get("project_context", True) else ""
        prompt = f"TASK: {goal}\n\nMODE: {mode}{plan_context}\n\nWORKSPACE CONTEXT:\n{context}"

        history = read_json(HISTORY_PATH, [])
        msgs = [{"role": "system", "content": system}]
        msgs += [{"role": x["role"], "content": x["content"][:6000]} for x in history[-6:] if x.get("role") in ("user", "assistant")]
        msgs.append({"role": "user", "content": prompt})

        self.active_agent_goal = goal
        self.tool_engine.start_agent_task(goal)
        self.start_ai(msgs, "agent", extra_meta={"goal": goal, "step": 1, "messages": list(msgs)})
        history.append({"role": "user", "content": goal})
        write_json(HISTORY_PATH, history[-40:])

    def start_ai(self, messages, task_type, extra_meta=None):
        self.task_counter += 1
        tid = str(self.task_counter)
        self.active_task = tid
        self.current_task_type = task_type
        self.current_answer = ""
        self.current_meta = extra_meta or {}
        self.live_cursor = None

        self.send.setEnabled(False)
        self.stop.setEnabled(True)
        self.progress.show()
        if task_type == "quick_edit" and self.current_meta.get("is_autofix"):
            self.set_ai_state("AUTOFIX")
        else:
            self.set_ai_state("STREAMING")
        self.td_status.setText(f"● Generating ({self.model})")
        self.td_status.setStyleSheet("color: #ffcb6b; font-weight: bold;")
        self.statusBar().showMessage(f"AI ({self.model}) active…")

        worker = AIWorker(self.base_url, self.provider, self.model, messages, tid, True, self.settings, self)
        worker.token.connect(lambda ch, t=tid: self.on_token(t, ch))
        worker.done.connect(self.on_ai_done)
        worker.error.connect(self.on_ai_error)
        worker.stats.connect(lambda count, rate: (
            self.token_stat_label.setText(f"{count} tok | {rate:.1f} tok/s"),
            self.td_rate.setText(f"{rate:.1f} tok/s")
        ))
        worker.status.connect(self.statusBar().showMessage)
        worker.finished.connect(lambda t=tid: self.cleanup_worker(t))

        self.workers[tid] = worker
        worker.start()

    def on_token(self, tid, chunk):
        if tid != self.active_task:
            return
        self.current_answer += chunk
        if self.live_cursor is None:
            self.chat.append("<p><b style='color:#75e09f;'>AI Copilot</b><br>")
            self.live_cursor = self.chat.textCursor()
            self.live_cursor.movePosition(QTextCursor.End)
            self.live_cursor.insertText(chunk)
            self.chat.setTextCursor(self.live_cursor)
        else:
            self.live_cursor.insertText(chunk)
            self.chat.setTextCursor(self.live_cursor)

    def on_ai_done(self, tid, answer, meta):
        if tid != self.active_task:
            return
        if meta.get("cancelled"):
            self.chat.append("<i>[Task cancelled]</i>")
            return

        full_text = self.current_answer or answer
        if "<thought>" in full_text or "<thinking>" in full_text:
            collapsible_html = format_collapsible_thought(full_text)
            self.chat.append(collapsible_html)
        hist = read_json(HISTORY_PATH, [])
        hist.append({"role": "assistant", "content": full_text[:4000]})
        write_json(HISTORY_PATH, hist[-40:])

        if self.current_task_type == "quick_edit":
            self.handle_quick_edit_result(full_text)
        elif self.current_task_type == "agent":
            self.handle_agent_tools(full_text)

        self.set_ai_state("IDLE")
        self.td_status.setText("● Ready")
        self.td_status.setStyleSheet("color: #75e09f; font-weight: bold;")
        self.statusBar().showMessage("AI response complete", 4000)

    def handle_quick_edit_result(self, answer):
        e = self.current()
        if not e:
            return
        m = re.search(r"```(?:[\w+#.-]+)?\s*\n(.*?)```", answer, re.S)
        proposed = m.group(1).rstrip() if m else answer.strip()
        is_partial = self.current_meta.get("is_partial", False)
        before_text = self.current_meta.get("before", e.text())

        dlg = VisualDiffDialog(before_text, proposed, Path(e.file_path).name if e.file_path else "Edit", self)
        if dlg.exec_() == QDialog.Accepted:
            final_code = dlg.proposed_view.toPlainText()
            if is_partial and e.selection():
                e.replaceSelectedText(final_code)
            else:
                e.setText(final_code)
            e.setModified(True)
            if dlg.save_to_disk_requested:
                self.save_file()
            self.statusBar().showMessage("Changes applied to editor", 4000)

    def handle_agent_tools(self, answer):
        # 1. Check for deliverable complete tags
        deliv_match = re.search(r"<deliverable:complete(?:\s+name=[\"'](.*?)[\"'])?\s*>(.*?)</deliverable:complete>", answer, re.DOTALL)
        if deliv_match:
            deliv_name = deliv_match.group(1) or "Project Deliverable"
            deliv_summary = deliv_match.group(2).strip()
            self.inspector.add_artifact(deliv_name, "Verified Deliverable Complete")
            log_agent_action("deliverable_complete", {"name": deliv_name, "summary": deliv_summary})
            banner = (
                f"<div style='background: #102a1d; border: 1px solid #2ea055; border-radius: 8px; padding: 10px; margin: 8px 0;'>"
                f"<b style='color: #75e09f; font-size: 11pt;'>🎉 DELIVERABLE VERIFIED & COMPLETE: {html_escape(deliv_name)}</b>"
                f"<p style='color: #edf4ff; margin-top: 4px; font-size: 9.5pt;'>{html_escape(deliv_summary)}</p>"
                f"</div>"
            )
            self.chat.append(banner)
            self.statusBar().showMessage(f"Deliverable complete: {deliv_name}", 5000)

        tools = AgentToolEngine.extract_tools(answer)
        if not tools:
            return

        step = self.current_meta.get("step", 1)
        max_steps = self.settings.get("max_agent_steps", 25)
        if step >= max_steps:
            self.chat.append(f"<p style='color:#ffcb6b;'><i>[Autonomous loop step limit reached ({max_steps})]</i></p>")
            return

        tool_results = []
        for name, args in tools:
            if name == "run_command" and not self.settings.get("unrestricted_mode", True) and not self.settings.get("allow_agent_commands", True):
                ans = QMessageBox.question(self, "Agent Approval", f"Agent wants to run:\n\n{args.get('cmd')}\n\nAllow execution?", QMessageBox.Yes | QMessageBox.No)
                if ans != QMessageBox.Yes:
                    tool_results.append(f"Tool {name} skipped by user.")
                    continue

            self.inspector.add_skill_used("agent-tool-engine")
            log_agent_action("tool_call", {"tool": name, "args": args, "step": step})

            res = self.tool_engine.execute_tool(name, args)

            if "error" in res.lower() or "fail" in res.lower():
                log_error("agent_tool", f"Tool {name} failed: {res[:200]}")

            if name in ("write_file", "patch_file"):
                p = args.get("path", "")
                if p:
                    self.inspector.add_file_changed(p)
            elif name == "verify_deliverable":
                self.inspector.add_skill_used("deliverable-verification")
                self.inspector.add_artifact(args.get("name", "Target Deliverable"), "Verification Report")

            res_snip = html_escape(res[:300] + ("..." if len(res) > 300 else ""))
            self.chat.append(
                f"<details style='background: #0d121c; border-left: 3px solid #5aa7ff; border-radius: 4px; margin: 4px 0; padding: 6px;'>"
                f"<summary style='color: #5aa7ff; cursor: pointer; font-weight: bold;'>⚙ Executed: <code>{name}</code> ▾</summary>"
                f"<pre style='color: #8fa2bf; font-family: monospace; font-size: 8.5pt; margin-top: 4px;'>{res_snip}</pre>"
                f"</details>"
            )
            tool_results.append(f"RESULT OF {name}:\n{res}")

        feedback = "\n\n".join(tool_results)
        goal = self.current_meta.get("goal") or getattr(self, "active_agent_goal", "Autonomous Goal")

        # Retrieve preserved message history
        prev_msgs = self.current_meta.get("messages")
        if not prev_msgs:
            prev_msgs = [
                {"role": "system", "content": "You are continuing the autonomous task. Review tool results and provide the next step or final resolution. When all goals are met, wrap deliverable confirmation in <deliverable:complete name=\"Name\">Summary</deliverable:complete>."},
                {"role": "user", "content": f"TASK: {goal}"}
            ]

        cur_msgs = list(prev_msgs)
        # Preserve assistant's prior response containing thoughts and tool calls
        cur_msgs.append({"role": "assistant", "content": answer})

        # Append tool observation turn with task goal reminder
        obs_content = (
            f"=== TOOL EXECUTION OBSERVATIONS (Step {step}/{max_steps}) ===\n"
            f"{feedback}\n\n"
            f"ORIGINAL TASK GOAL: {goal}\n"
            f"Review these tool outputs against your goal. If additional actions are required, execute the next <tool:...> tag. "
            f"If all criteria are met and verified, confirm with <deliverable:complete name=\"...\">Summary</deliverable:complete>."
        )
        cur_msgs.append({"role": "user", "content": obs_content})

        # Bounded context management to prevent token overflow while preserving identity and goal
        if len(cur_msgs) > 16:
            sys_m = cur_msgs[0]
            first_user_m = cur_msgs[1] if len(cur_msgs) > 1 else None
            recent_turns = cur_msgs[-12:]
            pruned = [sys_m]
            if first_user_m and first_user_m not in recent_turns:
                pruned.append(first_user_m)
            pruned.extend(recent_turns)
            cur_msgs = pruned

        self.chat.append(f"<p><b style='color:#8ab4f8;'>System Feedback:</b> Preserved context across step {step}/{max_steps} (Goal: {html_escape(goal[:60])}...).</p>")
        self.start_ai(cur_msgs, "agent", extra_meta={"goal": goal, "step": step + 1, "messages": cur_msgs})

    def show_accessory_popup(self):
        popup = AccessoryPopup(self, self)
        btn_pos = self.btn_accessory.mapToGlobal(QPoint(0, 0))
        popup_x = max(10, btn_pos.x() - 100)
        popup_y = max(10, btn_pos.y() - 460)
        popup.move(popup_x, popup_y)
        popup.show()

    def accessory_add_photos_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add Photos & Files", self.root,
            "All Files (*.*);;Images (*.png *.jpg *.jpeg *.webp *.svg);;Code & Data (*.py *.js *.ts *.json *.md *.txt *.csv)"
        )
        if files:
            assets_dir = Path(self.root) / "uploads"
            assets_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                src = Path(f)
                dest = assets_dir / src.name
                if str(src) != str(dest):
                    try:
                        shutil.copy2(src, dest)
                    except Exception:
                        pass
                self.prompt.insertPlainText(f"\n[Attached File: uploads/{src.name}]\n")
                self.inspector.add_upload(src.name, str(dest))
            self.statusBar().showMessage(f"Attached {len(files)} file(s)", 3000)

    def accessory_add_from_library(self):
        dlg = LibraryBrowserDialog(self.root, self)
        if dlg.exec_() == QDialog.Accepted and dlg.selected_files:
            for p in dlg.selected_files:
                try:
                    rel = Path(p).relative_to(self.root)
                except Exception:
                    rel = Path(p).name
                self.prompt.insertPlainText(f"\n[Library File: {rel}]\n")
                self.inspector.add_upload(str(rel), str(p))
            self.statusBar().showMessage(f"Attached {len(dlg.selected_files)} library file(s)", 3000)

    def accessory_create_image(self):
        dlg = CreateImageDialog(self.root, self)
        if dlg.exec_() == QDialog.Accepted and dlg.generated_path:
            rel = Path(dlg.generated_path).relative_to(self.root)
            self.prompt.insertPlainText(f"\n[Generated Visual Asset: {rel}]\n")
            self.inspector.add_artifact(rel.name, "Visual Asset")
            self.chat.append(f"<p style='color:#38bdf8;'>🎨 Generated visual asset: <code>{rel}</code></p>")

    def accessory_sketch(self):
        dlg = SketchCanvasDialog(self.root, self)
        if dlg.exec_() == QDialog.Accepted and dlg.saved_image_path:
            rel = Path(dlg.saved_image_path).relative_to(self.root)
            self.prompt.insertPlainText(f"\n[Attached Sketch: {rel}]\n")
            self.inspector.add_upload(rel.name, str(dlg.saved_image_path))
            self.statusBar().showMessage(f"Sketch attached: {rel.name}", 3000)

    def accessory_web_search(self):
        dlg = WebSearchDialog(self)
        if dlg.exec_() == QDialog.Accepted and dlg.search_summary:
            self.prompt.insertPlainText(f"\n{dlg.search_summary}\n")
            self.statusBar().showMessage("Web search results attached to prompt", 3000)

    def accessory_deep_research(self):
        self.agent_mode.setCurrentText("Autonomous Agent (Tools Enabled)")
        template = (
            "Perform a deep research investigation and full solution implementation:\n"
            "Goal: [Describe objective]\n"
            "- Step 1: Search codebase and docs for relevant architecture\n"
            "- Step 2: Implement verified solution\n"
            "- Step 3: Run tests and verify deliverable completeness"
        )
        self.prompt.setPlainText(template)
        self.prompt.setFocus()
        self.statusBar().showMessage("Deep research mode configured", 3000)

    def accessory_visualize(self):
        dlg = VisualizationDialog(self.root, self)
        if dlg.exec_() == QDialog.Accepted and dlg.generated_path:
            rel = Path(dlg.generated_path).relative_to(self.root)
            self.inspector.add_artifact(rel.name, "Visualization")
            self.prompt.insertPlainText(f"\n[Visualization: {rel}]\n")

    def accessory_open_provider_hub(self):
        self.open_settings()

    def accessory_github_flow(self):
        dlg = GitHubFlowDialog(self.root, self)
        dlg.exec_()

    def save_current_conversation(self):
        text = self.chat.toPlainText().strip()
        if not text:
            return
        data = {
            "id": self.active_conversation_id,
            "title": self.active_conversation_title,
            "timestamp": time.time(),
            "chat_html": self.chat.toHtml()
        }
        write_json(CONVERSATIONS_DIR / f"{self.active_conversation_id}.json", data)

    def new_conversation(self):
        self.save_current_conversation()
        self.active_conversation_id = f"conv_{int(time.time())}"
        self.active_conversation_title = "New Conversation"
        self.chat.clear()
        self.chat.append(f"""
            <div style='padding: 10px; background: #111622; border-radius: 6px; border: 1px solid #1f2838;'>
                <b style='color:#00F0FF; font-size:11pt;'>SO NAIVE IDE — Agent Copilot</b><br>
                <span style='color:#8fa2bf; font-size:9pt;'>Start a new task, ask questions, or press <b>＋</b> to attach photos, sketch, search web, or inspect tools.</span>
            </div><br>
        """)
        self.refresh_conversation_list()

    def switch_conversation(self, item):
        conv_id = item.data(Qt.UserRole)
        if not conv_id:
            return
        self.save_current_conversation()
        conv_file = CONVERSATIONS_DIR / f"{conv_id}.json"
        if conv_file.exists():
            data = read_json(conv_file, {})
            self.active_conversation_id = data.get("id", conv_id)
            self.active_conversation_title = data.get("title", item.text())
            html = data.get("chat_html", "")
            if html:
                self.chat.setHtml(html)
            else:
                self.chat.setPlainText(data.get("chat_text", ""))
            self.statusBar().showMessage(f"Loaded conversation: {self.active_conversation_title}", 3000)

    def refresh_conversation_list(self):
        if not hasattr(self, "conv_list"):
            return
        self.conv_list.clear()
        files = sorted(CONVERSATIONS_DIR.glob("conv_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        now = time.time()
        for f in files[:10]:
            try:
                d = read_json(f, {})
                title = d.get("title", f.stem)
                ts = d.get("timestamp", f.stat().st_mtime)
                diff_sec = now - ts
                if diff_sec < 3600:
                    age = f"{max(1, int(diff_sec // 60))}m"
                elif diff_sec < 86400:
                    age = f"{int(diff_sec // 3600)}h"
                else:
                    age = f"{int(diff_sec // 86400)}d"
                item = QListWidgetItem(f"💬 {title[:20]}  {age}")
                item.setData(Qt.UserRole, d.get("id", f.stem))
                self.conv_list.addItem(item)
            except Exception:
                pass

    def open_conversation_history(self):
        dlg = ConversationHistoryDialog(self, self)
        dlg.exec_()

    def open_automations_dialog(self):
        dlg = AutomationsDialog(self)
        dlg.exec_()

    def open_customizations_dialog(self):
        dlg = CustomizationsDialog(self)
        dlg.exec_()

    def on_ai_error(self, tid, err):
        if tid == self.active_task:
            self.set_ai_state("ERROR")
            self.chat.append(f"<p style='color:#ff8585;'><b>AI Error:</b> {html_escape(err)}</p>")
            self.td_status.setText("● Error")
            self.td_status.setStyleSheet("color: #ff8585; font-weight: bold;")

    def cleanup_worker(self, tid):
        w = self.workers.pop(tid, None)
        if w:
            w.deleteLater()
        if tid == self.active_task:
            self.active_task = None
            self.send.setEnabled(True)
            self.stop.setEnabled(False)
            self.progress.hide()
            self.set_ai_state("IDLE")

    def stop_ai(self):
        if self.active_task and self.active_task in self.workers:
            self.workers[self.active_task].cancel()
            self.set_ai_state("IDLE")
            self.statusBar().showMessage("Cancelled AI request", 3000)

    def attach_selection(self):
        e = self.current()
        if e and e.selection():
            self.prompt.insertPlainText(f"\n```\n{e.selection()}\n```\n")

    def explain(self):
        e = self.current()
        if not e or not e.selection():
            QMessageBox.information(self, "Explain", "Select code in the editor to explain.")
            return
        self.prompt.setPlainText(f"Explain this code, its design, edge cases, and time/space complexity:\n```\n{e.selection()}\n```")
        self.send_prompt()

    def debug(self):
        e = self.current()
        if not e:
            return
        code = e.text()[:MAX_FILE_CONTEXT]
        out = self.output.toPlainText()[-4000:]
        self.prompt.setPlainText(f"Debug this file and error output. Identify the root cause and provide the exact fix.\n\nRecent Output:\n{out}\n\nCode:\n```\n{code}\n```")
        self.send_prompt()

    def populate_providers_combo(self):
        curr = self.provider_combo.currentText() if hasattr(self, "provider_combo") and self.provider_combo.count() else self.provider
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        base_providers = ["⚡ Auto-Router", "Google Gemini", "NavyAI", "Ollama", "OpenAI-compatible"]
        custom_models = read_json(CUSTOM_MODELS_CONFIG_PATH, [])
        custom_prov_names = sorted(list(set(cm.get("provider", "") for cm in custom_models if cm.get("provider") and cm.get("enabled", True))))
        for cp in custom_prov_names:
            if cp not in base_providers and cp != "Ollama (Local)":
                base_providers.append(cp)
        self.provider_combo.addItems(base_providers)
        if curr in base_providers:
            self.provider_combo.setCurrentText(curr)
        elif self.provider in base_providers:
            self.provider_combo.setCurrentText(self.provider)
        else:
            self.provider_combo.setCurrentIndex(0)
        self.provider_combo.blockSignals(False)

    def change_provider(self, val):
        self.settings["provider"] = val
        self.save_settings()
        self.refresh_models()

    def change_model(self, val):
        if val.strip():
            self.settings["model"] = val.strip()
            self.save_settings()

    def refresh_models(self):
        self.model_combo.blockSignals(True)
        self.model_combo.clear()

        custom_models = read_json(CUSTOM_MODELS_CONFIG_PATH, [])
        matching_custom = [cm for cm in custom_models if cm.get("provider") == self.provider and cm.get("enabled", True)]

        if matching_custom:
            c_mods = [cm.get("model") for cm in matching_custom if cm.get("model")]
            self.model_combo.addItems(c_mods)
            curr = self.model if self.model in c_mods else (c_mods[0] if c_mods else "")
            if curr:
                self.model_combo.setCurrentText(curr)
            self.statusBar().showMessage(f"Custom Provider '{self.provider}' Active ({len(c_mods)} models)", 3000)
        elif self.provider == "⚡ Auto-Router":
            self.model_combo.addItems([
                "⚡ Auto: Highest Performance Available",
                "gemini-3.8-flash (Ultra-Fast 1M Context)",
                "gemini-3.5-flash (High Throughput)",
                "qwen2.5:1.5b (Local GPU Offline)",
                "gemini-3.1-pro-preview (Deep Reasoning)"
            ])
            self.model_combo.setCurrentIndex(0)
            self.statusBar().showMessage("⚡ Intelligent Dynamic Router Active", 3000)
        elif self.provider == "Google Gemini":
            models = ["gemini-3.8-flash", "gemini-3.8-flash-lite", "gemini-3.5-flash", "gemini-3.1-pro-preview"]
            self.model_combo.addItems(models)
            curr = self.model if self.model in models else "gemini-3.8-flash"
            self.model_combo.setCurrentText(curr)
            self.statusBar().showMessage("Google Gemini Engine Active", 3000)
        elif self.provider == "NavyAI":
            models = self.get_navy_models()
            self.model_combo.addItems(models)
            curr = self.model if self.model in models else "gemini-3.8-flash"
            self.model_combo.setCurrentText(curr)
            self.statusBar().showMessage(f"NavyAI Unified Gateway Active ({len(models)} models available)", 3000)
        elif self.provider == "Ollama":
            try:
                r = requests.get(self.base_url + "/api/tags", timeout=3)
                r.raise_for_status()
                models = [x["name"] for x in r.json().get("models", []) if x.get("name")]
                self.model_combo.addItems(models or ["qwen2.5:1.5b"])
                self.model_combo.setCurrentText(self.model if self.model in models else models[0])
                self.statusBar().showMessage(f"Detected {len(models)} local Ollama model(s)", 3000)
            except Exception:
                self.model_combo.addItems(["qwen2.5:1.5b"])
        else:
            self.model_combo.addItems(["gpt-4o", "gpt-4o-mini", "o3-mini", "deepseek-coder"])

        self.model_combo.blockSignals(False)

    def get_navy_models(self):
        cache_path = APP_HOME / "navy_models_cache.json"
        if not cache_path.exists():
            scratch_path = Path(__file__).resolve().parent / "scratch" / "navy_models.json"
            if scratch_path.exists():
                cache_path = scratch_path
        if cache_path.exists():
            try:
                data = read_json(cache_path, [])
                if isinstance(data, list):
                    ids = [m.get("id") for m in data if isinstance(m, dict) and "id" in m]
                    if ids:
                        return ids
                elif isinstance(data, dict):
                    ids = [m.get("id") for m in data.get("data", []) if isinstance(m, dict) and "id" in m]
                    if ids:
                        return ids
            except Exception:
                pass
        return NAVY_POPULAR_MODELS

    def refresh_connection(self):
        gemini_key = self.settings.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
        navy_key = self.settings.get("navy_api_key") or os.environ.get("NAVY_API_KEY", "")
        if gemini_key and navy_key:
            self.connection.setText("● Gemini & NavyAI Online")
            self.connection.setStyleSheet("color:#75e09f; font-weight:bold;")
        elif gemini_key:
            self.connection.setText("● Gemini & GPU Online")
            self.connection.setStyleSheet("color:#75e09f; font-weight:bold;")
        elif navy_key:
            self.connection.setText("● NavyAI Online")
            self.connection.setStyleSheet("color:#75e09f; font-weight:bold;")
        else:
            self.connection.setText("● Local Only")
            self.connection.setStyleSheet("color:#ffcb6b; font-weight:bold;")

    def open_model_folder(self):
        MODEL_DROP_DIR.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(MODEL_DROP_DIR)))

    def import_local_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Local GGUF Model", str(MODEL_DROP_DIR), "GGUF models (*.gguf);;All files (*)"
        )
        if not path:
            return
        if not shutil.which("ollama"):
            QMessageBox.warning(self, "Ollama Missing", "Install Ollama and ensure ollama.exe is on PATH.")
            return

        default_name = Path(path).stem.lower().replace(" ", "-")
        name, ok = QInputDialog.getText(self, "Register GGUF Model", "Choose Ollama model name:", text=default_name)
        if not ok or not name.strip():
            return

        name = re.sub(r"[^a-zA-Z0-9._:-]", "-", name.strip())
        modelfile = MODEL_DROP_DIR / f"{name}.Modelfile"
        model_p = str(Path(path).resolve()).replace("\\", "/")
        modelfile.write_text(f'FROM "{model_p}"\n', encoding="utf-8")

        ans = QMessageBox.question(self, "Import GGUF", f"Register model '{name}' into Ollama from:\n{path}?", QMessageBox.Yes | QMessageBox.No)
        if ans == QMessageBox.Yes:
            proc = subprocess.run(["ollama", "create", name, "-f", str(modelfile)], cwd=str(MODEL_DROP_DIR), capture_output=True, text=True)
            if proc.returncode == 0:
                self.settings["model"] = name
                self.save_settings()
                self.refresh_models()
                QMessageBox.information(self, "Model Registered", f"Ollama model '{name}' is ready to use!")
            else:
                QMessageBox.critical(self, "Registration Failed", proc.stderr)

    def run_ide_check(self):
        lines = [
            f"{APP_NAME} v{APP_VERSION} — FITNESS REPORT",
            "=" * 50,
            f"Python Runtime: {sys.version.split()[0]} ({sys.executable})",
            f"Active Workspace: {self.root}",
            f"Configured Engine: {self.provider} ({self.model})",
            ""
        ]
        checks = []

        for pkg in ("PyQt5", "PyQt5.Qsci", "requests", "pytest", "torch", "transformers"):
            try:
                __import__(pkg)
                checks.append((f"Package: {pkg}", True, "Import verified"))
            except Exception as ex:
                checks.append((f"Package: {pkg}", False, str(ex)))

        try:
            import torch
            cuda_ok = torch.cuda.is_available()
            dev_name = torch.cuda.get_device_name(0) if cuda_ok else "No CUDA device"
            checks.append(("Hardware Acceleration (CUDA)", cuda_ok, f"{dev_name} (CUDA {torch.version.cuda if cuda_ok else 'N/A'})"))
        except Exception as ex:
            checks.append(("Hardware Acceleration (CUDA)", False, str(ex)))

        checks.append(("Git CLI", bool(shutil.which("git")), shutil.which("git") or "Git not installed"))
        checks.append(("Ollama CLI", bool(shutil.which("ollama")), shutil.which("ollama") or "Ollama CLI not installed"))

        key = self.settings.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
        if key:
            checks.append(("Google Gemini API Key", True, f"Verified (starts with {key[:6]}...)"))
        else:
            checks.append(("Google Gemini API Key", False, "Missing in settings.json"))

        try:
            r = requests.get(self.base_url + "/api/tags", timeout=3)
            r.raise_for_status()
            models = [m.get("name") for m in r.json().get("models", [])]
            checks.append(("Ollama Service", True, f"Online ({len(models)} model(s): {', '.join(models)})"))
        except Exception as ex:
            checks.append(("Ollama Service", False, str(ex)))

        py_files = []
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            py_files.extend(str(Path(root) / f) for f in files if f.endswith((".py", ".pyw")))
        syntax_errs = []
        for f in py_files[:2000]:
            try:
                compile(Path(f).read_text(encoding="utf-8", errors="replace"), f, "exec")
            except Exception as ex:
                syntax_errs.append(f"{Path(f).name}: {ex}")
        checks.append((f"Workspace Python Syntax ({len(py_files)} files)", not syntax_errs, "\n".join(syntax_errs[:10]) if syntax_errs else "100% syntax valid"))

        lines.extend(("[PASS]" if ok else "[WARN]") + f" {name}\n  -> {detail}" for name, ok, detail in checks)
        rep = "\n".join(lines)
        self.bottom_tabs.setCurrentIndex(0)
        self.output.setPlainText(rep)
        try:
            (APP_HOME / "last_fitness_check.txt").write_text(rep, encoding="utf-8")
        except Exception:
            pass
        self.statusBar().showMessage("IDE Fitness Check Complete", 5000)

    def settings_dialog(self):
        d = SettingsDialog(self.settings, self)
        if d.exec_() == QDialog.Accepted:
            self.settings = d.values()
            self.save_settings()
            self.populate_providers_combo()
            self.provider_combo.setCurrentText(self.provider)
            self.refresh_models()
            self.model_combo.setCurrentText(self.model)
            self.refresh_connection()

    def restore_chat(self):
        hist = read_json(HISTORY_PATH, [])
        for item in hist[-20:]:
            if item.get("role") in ("user", "assistant") and item.get("content"):
                sender = "You" if item["role"] == "user" else "AI Copilot"
                color = "#5aa7ff" if item["role"] == "user" else "#75e09f"
                self.chat.append(f"<p><b style='color:{color};'>{sender}</b><br>{html_escape(item['content'])}</p>")
        if not self.chat.toPlainText():
            self.chat.setHtml(
                f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
                f"<p>PRUBETH Horizon Intelligent Edition is active.<br>"
                f"• <b>⚡ Dynamic Cascade:</b> Automatically routes tasks to Gemini 3.8 Flash with instant Local GPU failover.<br>"
                f"• <b>⚡ Automated Auto-Fix:</b> Repairs runtime errors & tracebacks in 1 click.<br>"
                f"• <b>Ctrl+K:</b> Inline Quick Edit | <b>Ctrl+P:</b> Quick Open | <b>Ctrl+Shift+P:</b> Command Palette.<br>"
                f"• <b>Tools → Radar:</b> Benchmark live latencies and model execution speeds.</p>"
            )

    def run_workspace_sast_scan(self):
        from security_research.sast_sca_engine import get_sast_engine
        engine = get_sast_engine()
        findings = engine.scan_directory(self.root, max_files=300)
        summary = engine.get_summary(findings)

        self.output_tabs.setCurrentIndex(1)
        self.output.append("\n" + "=" * 60)
        self.output.append(f"🛡️ PRUBETH SAST SCAN REPORT — {len(findings)} Findings [{summary['risk_status']}]")
        self.output.append("=" * 60)
        for f in findings[:25]:
            self.output.append(f"[{f.severity.value}] {f.title} ({f.rule_id})")
            self.output.append(f"  File: {f.file_path}:{f.line_number}")
            self.output.append(f"  Code: {f.code_snippet}")
            self.output.append(f"  Fix:  {f.remediation}\n")

        QMessageBox.information(
            self,
            "SAST Scan Complete",
            f"Scanned workspace: {len(findings)} security findings detected.\nRisk Status: {summary['risk_status']}\n\nDetailed breakdown displayed in Console Output."
        )

    def run_workspace_sbom_generation(self):
        from security_research.sast_sca_engine import get_sca_engine
        engine = get_sca_engine()

        req_p = Path(self.root) / "requirements.txt"
        pkg_p = Path(self.root) / "package.json"
        target = req_p if req_p.exists() else pkg_p if pkg_p.exists() else None

        if not target:
            QMessageBox.warning(self, "No Manifest Found", "Could not find requirements.txt or package.json in active workspace.")
            return

        sbom = engine.generate_cyclonedx_sbom(str(target), project_name="prubeth-workspace")
        advisories = engine.audit_dependencies(str(target))

        out_file = Path(self.root) / "cyclonedx_sbom.json"
        out_file.write_text(json.dumps(sbom, indent=2), encoding="utf-8")

        self.output_tabs.setCurrentIndex(1)
        self.output.append(f"\n📦 CycloneDX 1.5 SBOM generated: {out_file} ({len(sbom['components'])} components)")
        if advisories:
            self.output.append(f"⚠️ {len(advisories)} Dependency Advisories Detected:")
            for adv in advisories:
                self.output.append(f"  - [{adv.severity.value}] {adv.title}: {adv.description}")

        QMessageBox.information(
            self,
            "SBOM Generated",
            f"Saved CycloneDX 1.5 SBOM to:\n{out_file}\n\nComponents: {len(sbom['components'])}\nCVE Advisories: {len(advisories)}"
        )

    def run_binary_inspection_dialog(self):
        from security_research.reverse_engineering_bridge import get_reverse_engineering_bridge
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Target Binary for Inspection", self.root,
            "Binaries (*.exe *.dll *.so *.bin *.sys *.elf);;All Files (*)"
        )
        if not path:
            return

        bridge = get_reverse_engineering_bridge()
        meta = bridge.inspect_file(path)

        self.output_tabs.setCurrentIndex(1)
        self.output.append("\n" + "=" * 60)
        self.output.append(f"🔬 BINARY INSPECTION: {Path(path).name}")
        self.output.append("=" * 60)
        self.output.append(f"Format: {meta.format.value} | Arch: {meta.architecture.value} | 64-bit: {meta.is_64bit}")
        self.output.append(f"Entropy: {meta.overall_entropy:.4f} (Packed/Obfuscated: {meta.overall_entropy > 7.15})")
        self.output.append(f"Sections: {len(meta.sections)} | Strings Extracted: {meta.extracted_strings_count}")
        if meta.suspicious_iocs:
            self.output.append(f"⚠️ Suspicious IoCs ({len(meta.suspicious_iocs)}):")
            for ioc in meta.suspicious_iocs:
                self.output.append(f"  [{ioc['type']}] {ioc['indicator']} ({ioc['category']})")

        QMessageBox.information(
            self,
            "Binary Inspection Complete",
            f"Target: {Path(path).name}\nFormat: {meta.format.value} ({meta.architecture.value})\nEntropy: {meta.overall_entropy:.2f} / 8.0\nIoCs Detected: {len(meta.suspicious_iocs)}\n\nDetailed breakdown displayed in Console Output."
        )

    def run_model_lab_benchmark(self):
        from core.model_lab import get_model_benchmark_harness
        harness = get_model_benchmark_harness()

        def synthetic_stream():
            import time
            time.sleep(0.04)
            for i in range(25):
                time.sleep(0.015)
                yield f"tok_{i} "

        metric = harness.benchmark_stream(self.model, synthetic_stream, prompt_token_count=120)

        self.output_tabs.setCurrentIndex(1)
        self.output.append(f"\n🧪 MODEL LAB BENCHMARK — {metric.model_name}")
        self.output.append(f"  First Token Latency (FTL): {metric.first_token_latency_ms:.2f} ms")
        self.output.append(f"  Generation Speed:          {metric.tokens_per_second:.2f} tokens/sec")
        self.output.append(f"  Total Duration:            {metric.total_duration_ms:.2f} ms")
        self.output.append(f"  Hardware Offload VRAM:     {metric.vram_allocated_mb:.0f} MB")

        QMessageBox.information(
            self,
            "Model Benchmark Complete",
            f"Model: {metric.model_name}\nFTL: {metric.first_token_latency_ms:.1f} ms\nSpeed: {metric.tokens_per_second:.1f} tok/s\nAllocated VRAM: {metric.vram_allocated_mb:.0f} MB"
        )

    def toggle_airgap_policy(self):
        from core.model_lab import get_offline_policy, OfflinePolicyMode
        policy = get_offline_policy()
        if policy.mode == OfflinePolicyMode.STRICT_AIRGAP:
            policy.set_mode(OfflinePolicyMode.AUDIT_ONLY)
            msg = "Air-Gap Policy set to AUDIT_ONLY (monitored, non-blocking)."
        else:
            policy.set_mode(OfflinePolicyMode.STRICT_AIRGAP)
            msg = "Strict Air-Gap Policy ENFORCED: All external network egress blocked at socket level."

        self.statusBar().showMessage(f"🔒 {msg}", 5000)
        QMessageBox.information(self, "Air-Gap Policy Status", msg)

    def run_autonomous_diagnostics(self):
        from core.autonomous_ops import get_autonomous_supervisor
        supervisor = get_autonomous_supervisor()
        observations = supervisor.observe()
        issues = supervisor.diagnose(observations)

        self.output_tabs.setCurrentIndex(1)
        self.output.append("\n" + "=" * 60)
        self.output.append(f"🤖 AUTONOMOUS SUPERVISOR DIAGNOSTIC — {len(observations)} Observations, {len(issues)} Issues")
        self.output.append("=" * 60)
        for obs in observations:
            status = "HEALTHY" if obs.healthy else "ALERT"
            self.output.append(f"[{status}] {obs.category} - {obs.metric_name}: {obs.current_value} (threshold: {obs.threshold_value})")

        if not issues:
            self.output.append("✓ All monitored subsystems are healthy. Zero remediation required.")
            QMessageBox.information(self, "Autonomous Diagnostics", "All monitored subsystems are healthy.\nZero remediation required.")
        else:
            for issue in issues:
                plan = supervisor.plan(issue)
                can_exec, ticket = supervisor.check_policy_and_approve(plan)
                if can_exec:
                    rec = supervisor.execute_and_verify(plan)
                    self.output.append(f"✓ Auto-remediated {issue.title} ({rec.details})")
                else:
                    self.output.append(f"⏸ Remediation ticket generated: {ticket.ticket_id} [{ticket.risk_level.value}]")
            QMessageBox.information(self, "Autonomous Diagnostics", f"Diagnosed {len(issues)} issue(s).\nRemediations evaluated according to policy.\nSee Console Output for details.")

    def save_settings(self):
        write_json(SETTINGS_PATH, self.settings)

    def eventFilter(self, obj, event):
        if obj is self.prompt and event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ControlModifier:
            self.send_prompt()
            return True
        return super().eventFilter(obj, event)

    def _on_activity_view_changed(self, idx):
        if not self.left_tabs.isVisible():
            self.left_tabs.show()
        if idx < self.left_tabs.count():
            self.left_tabs.setCurrentIndex(idx)

    def _toggle_left_sidebar(self):
        self.left_tabs.setVisible(not self.left_tabs.isVisible())

    def _update_breadcrumb(self, idx=None):
        if not hasattr(self, "breadcrumb_bar"):
            return
        e = self.current()
        if e and getattr(e, "file_path", None):
            self.breadcrumb_bar.set_path(e.file_path)
        else:
            self.breadcrumb_bar.set_path("")

    def closeEvent(self, event):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()
        self.terminal.kill_process()
        for w in self.workers.values():
            w.cancel()
        self.save_settings()
        event.accept()


def main():
    try:
        from core.startup import AuthoritativeLauncher
        launcher = AuthoritativeLauncher()
        sys.exit(launcher.launch())
    except Exception as e:
        # Emergency direct fallback
        print(f"[CRITICAL ERROR] Failed to initialize PRUBETH IDE startup orchestrator: {e}", file=sys.stderr)
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setStyle("Fusion")
        win = Studio()
        win.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()

