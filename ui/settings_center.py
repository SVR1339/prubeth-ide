"""
PRUBETH IDE — Unified Settings & Subsystem Control Center
Pillar 4, 6 & 7: Design System, Quality Engineering & Release Governance

Integrates the 14-category comprehensive Settings Center with:
- Obsidian Slate (#0B0D13) & Electric Cyan (#00F0FF) Design System
- Universal Hardware Auto-Tuner (One-click device profiling & VRAM/concurrency synthesis)
- Universal Connector Gateway (Live probing of Ollama, LM Studio, vLLM, toolchains)
- Two-way backward-compatibility adapter with flat legacy settings
"""

from __future__ import annotations

import copy
import json
import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QDoubleSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.design_system import DesignTokens, ComponentStyles
from horizon_engine.hardware_autotuner import HardwareAutoTuner, TuningResult
from horizon_engine.connector_gateway import ConnectorGateway

APP_NAME = "PRUBETH IDE"
SCHEMA_VERSION = 1

DEFAULT_SETTINGS_PATH = Path.home() / ".local_ai_studio_pro" / "settings.json"

DEFAULTS: Dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "profile": "Default",
    "hardware_tier": "Auto-Detect",
    "appearance": {
        "theme": "Dark",
        "accent": DesignTokens.ACCENT_CYAN,
        "density": "Comfortable",
        "font_family": "Segoe UI",
        "font_size": 10,
        "ui_scale": 100,
        "animations": True,
        "show_icons": True,
        "high_contrast": False,
        "remember_layout": True,
        "restore_last_workspace": True,
    },
    "editor": {
        "font_family": "Cascadia Code",
        "font_size": 11,
        "tab_size": 4,
        "insert_spaces": True,
        "word_wrap": False,
        "line_numbers": True,
        "minimap": True,
        "bracket_matching": True,
        "auto_indent": True,
        "format_on_save": False,
        "trim_trailing_whitespace": True,
        "insert_final_newline": True,
        "autosave": True,
        "autosave_seconds": 30,
        "encoding": "UTF-8",
        "default_newline": "Platform default",
    },
    "workspace": {
        "default_projects_dir": str(Path.home() / "Projects"),
        "exclude_patterns": ["**/.git/**", "**/.venv/**", "**/node_modules/**",
                             "**/__pycache__/**", "**/dist/**", "**/build/**"],
        "follow_symlinks": False,
        "file_watcher": True,
        "restore_open_files": True,
        "confirm_delete": True,
        "max_file_mb": 20,
    },
    "terminal": {
        "shell": "PowerShell",
        "font_family": "Cascadia Mono",
        "font_size": 10,
        "scrollback_lines": 10000,
        "inherit_environment": True,
        "confirm_destructive_commands": True,
        "working_directory": "workspace",
    },
    "models": {
        "default_model_id": "ollama-qwen",
        "fallback_model_ids": [],
        "request_timeout_seconds": 180,
        "connect_timeout_seconds": 15,
        "max_retries": 2,
        "retry_backoff_seconds": 2,
        "stream_responses": True,
        "temperature": 0.2,
        "top_p": 0.9,
        "max_output_tokens": 4096,
        "context_policy": "Automatic",
        "allow_cloud_providers": True,
        "allow_local_providers": True,
        "require_confirmation_for_cloud": True,
        "models": [
            {
                "id": "ollama-qwen",
                "name": "Qwen 2.5 (Ollama)",
                "provider": "Ollama",
                "model": "qwen2.5:1.5b",
                "base_url": "http://localhost:11434",
                "api_key_env": "",
                "enabled": True,
                "capabilities": ["chat", "code"],
                "notes": "Fast local instruction model."
            }
        ],
    },
    "agents": {
        "mode": "Balanced",
        "max_parallel_agents": 2,
        "max_task_steps": 30,
        "max_tool_calls": 40,
        "task_timeout_minutes": 30,
        "auto_plan": True,
        "auto_test": True,
        "auto_review": True,
        "auto_apply_safe_edits": False,
        "require_approval_for_file_deletes": True,
        "require_approval_for_shell": True,
        "require_approval_for_network": True,
        "require_approval_for_dependency_install": True,
        "max_context_files": 40,
        "max_context_chars": 120000,
        "subagent_roles": ["Planner", "Implementer", "Reviewer", "Tester"],
        "fallback_on_provider_error": True,
    },
    "tools": {
        "enabled_tools": ["read_file", "search_files", "list_files", "apply_patch",
                          "run_tests", "git_status"],
        "plugin_dirs": [],
        "allow_mcp": True,
        "allow_extensions": True,
        "allow_workspace_scripts": False,
        "extension_trust": "Ask before enabling",
    },
    "security": {
        "safe_mode": True,
        "workspace_boundary": True,
        "redact_secrets_in_logs": True,
        "store_api_keys_in_os_keyring": True,
        "allow_telemetry": False,
        "allow_crash_reports": False,
        "scan_dependencies": True,
        "warn_on_untrusted_workspace": True,
        "block_shell_by_default": False,
        "network_policy": "Ask for external connections",
    },
    "privacy": {
        "save_chat_history": True,
        "save_prompts": True,
        "save_agent_traces": False,
        "local_index_only": True,
        "exclude_secrets_from_context": True,
        "clear_history_on_exit": False,
    },
    "performance": {
        "background_workers": 2,
        "indexing_enabled": True,
        "index_max_file_mb": 2,
        "max_indexed_files": 50000,
        "cache_mb": 512,
        "gpu_policy": "Automatic",
        "cuda_vram_limit_mb": 4096,
        "gguf_gpu_layers": 33,
        "low_memory_mode": False,
        "pause_indexing_on_battery": True,
    },
    "git": {
        "enabled": True,
        "auto_fetch": False,
        "show_diff_before_ai_apply": True,
        "create_checkpoint_before_agent_changes": True,
        "default_branch": "main",
    },
    "language": {
        "python_interpreter": "",
        "formatters": {"python": "ruff", "javascript": "prettier"},
        "linters": {"python": "ruff", "javascript": "eslint"},
        "test_command": "",
    },
    "updates": {
        "check_automatically": True,
        "channel": "Stable",
        "include_prereleases": False,
    },
    "advanced": {
        "log_level": "INFO",
        "diagnostic_mode": False,
        "feature_flags": {},
        "extra_json": {},
    },
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class SettingsStore:
    """Atomic JSON settings store with two-way legacy key bridging."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_SETTINGS_PATH
        self.data: Dict[str, Any] = copy.deepcopy(DEFAULTS)
        self.load()

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            self.data = copy.deepcopy(DEFAULTS)
            return self.data
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data = deep_merge(DEFAULTS, loaded)
                # Bridge flat legacy keys if present
                self._sync_legacy_keys_to_nested()
        except Exception:
            self.data = copy.deepcopy(DEFAULTS)
        return self.data

    def _sync_legacy_keys_to_nested(self):
        """Populates nested sections from flat legacy keys if needed."""
        d = self.data
        if "local_model" in d and d["local_model"]:
            d.setdefault("models", {})["default_model_id"] = d["local_model"]
        if "max_agent_steps" in d:
            d.setdefault("agents", {})["max_task_steps"] = int(d["max_agent_steps"])
        if "editor_tab_size" in d:
            d.setdefault("editor", {})["tab_size"] = int(d["editor_tab_size"])
        if "editor_font_size" in d:
            d.setdefault("editor", {})["font_size"] = int(d["editor_font_size"])

    def _sync_nested_to_legacy_flat(self):
        """Exports flat keys to root dictionary for zero-breakage consumption by local_ai_studio_pro."""
        d = self.data
        # Performance & GPU
        perf = d.get("performance", {})
        d["cuda_vram_limit_mb"] = perf.get("cuda_vram_limit_mb", 4096)
        d["gguf_gpu_layers"] = perf.get("gguf_gpu_layers", 33)
        d["background_workers"] = perf.get("background_workers", 2)
        d["cache_mb"] = perf.get("cache_mb", 512)
        d["low_memory_mode"] = perf.get("low_memory_mode", False)

        # Agent & Step budgets
        agents = d.get("agents", {})
        d["max_agent_steps"] = agents.get("max_task_steps", 30)
        d["allow_agent_commands"] = not agents.get("require_approval_for_shell", True)
        d["allow_agent_edits"] = True

        # Editor
        ed = d.get("editor", {})
        d["editor_tab_size"] = ed.get("tab_size", 4)
        d["editor_font_size"] = ed.get("font_size", 11)
        d["editor_font_family"] = ed.get("font_family", "Cascadia Code")
        d["editor_line_numbers"] = ed.get("line_numbers", True)
        d["editor_word_wrap"] = ed.get("word_wrap", False)

        # Terminal
        term = d.get("terminal", {})
        d["terminal_shell"] = term.get("shell", "PowerShell")
        d["terminal_buffer_lines"] = term.get("scrollback_lines", 10000)

        # Models & Ollama
        models = d.get("models", {})
        d["local_model"] = models.get("default_model_id", "qwen2.5:1.5b")
        d["ollama_url"] = "http://localhost:11434"

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._sync_nested_to_legacy_flat()
        payload = json.dumps(self.data, indent=2, ensure_ascii=False)
        fd, temp_name = tempfile.mkstemp(prefix="settings-", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


class SettingsPage(QWidget):
    """Clean form page adhering to the Obsidian Slate Design System."""

    def __init__(self, title: str, description: str = "", parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(14)
        
        heading = QLabel(title)
        heading.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.TEXT_PRIMARY};")
        outer.addWidget(heading)
        
        if description:
            sub = QLabel(description)
            sub.setWordWrap(True)
            sub.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: {DesignTokens.FONT_SIZE_BASE};")
            outer.addWidget(sub)
            
        self.form = QFormLayout()
        self.form.setHorizontalSpacing(24)
        self.form.setVerticalSpacing(14)
        self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        outer.addLayout(self.form)
        outer.addStretch(1)

    def add_row(self, label: str, widget: QWidget, help_text: str = ""):
        if help_text:
            widget.setToolTip(help_text)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {DesignTokens.TEXT_SECONDARY}; font-weight: 600; font-size: {DesignTokens.FONT_SIZE_BASE};")
        self.form.addRow(lbl, widget)


class SettingsCenterDialog(QDialog):
    """Unified 14-Category Settings Center with Hardware Auto-Tuning and Software Probing."""

    settings_applied = pyqtSignal(dict)

    CATEGORIES = [
        ("Appearance", "Appearance & Themes"),
        ("Editor", "Editor & Code-OSS"),
        ("Workspace", "Workspace & Files"),
        ("Terminal", "Terminal & Shell"),
        ("Models", "Models & AI Runtimes"),
        ("Agents", "Agents & Orchestration"),
        ("Tools", "Tools, Plugins & MCP"),
        ("Security", "Security & Guardrails"),
        ("Privacy", "Privacy & Data Policy"),
        ("Performance", "Performance & Hardware"),
        ("Git", "Git & Checkpoints"),
        ("Language", "Languages & Toolchains"),
        ("Updates", "Updates & Release"),
        ("Advanced", "Advanced & Diagnostics"),
    ]

    def __init__(self, store: Optional[SettingsStore] = None, parent=None):
        super().__init__(parent)
        self.store = store or SettingsStore()
        self.working = copy.deepcopy(self.store.data)
        self.controls: Dict[str, QWidget] = {}
        
        self.setWindowTitle(f"{APP_NAME} — Settings Center")
        self.resize(1120, 760)
        self.setMinimumSize(880, 620)
        
        self._build_ui()
        self._load_controls()
        self._apply_obsidian_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Header with Auto-Tune & Profile
        top = QHBoxLayout()
        title = QLabel("⚙ Settings Center")
        title.setStyleSheet(f"font-size: 22px; font-weight: 750; color: {DesignTokens.ACCENT_CYAN};")
        top.addWidget(title)
        top.addStretch()

        self.btn_autotune = QPushButton("⚡ Auto-Tune My Device")
        self.btn_autotune.setStyleSheet(ComponentStyles.primary_button())
        self.btn_autotune.clicked.connect(self._run_hardware_autotune)
        top.addWidget(self.btn_autotune)

        top.addWidget(QLabel("Profile:"))
        self.profile = QComboBox()
        self.profile.addItems(["Default", "Development", "Low Resource", "Secure", "Custom"])
        top.addWidget(self.profile)
        root.addLayout(top)

        # Search bar
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search settings… (e.g. model, GPU, VRAM, terminal, MCP, theme)")
        self.search.setStyleSheet(ComponentStyles.input_field())
        self.search.textChanged.connect(self._filter_categories)
        root.addWidget(self.search)

        # Splitter with category list and pages
        split = QSplitter(Qt.Horizontal)
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(240)
        self.category_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.stack = QStackedWidget()
        self.pages: Dict[str, QWidget] = {}

        for key, label in self.CATEGORIES:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.category_list.addItem(item)
            page = self._create_page(key)
            self.pages[key] = page
            self.stack.addWidget(page)

        self.category_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.category_list.setCurrentRow(0)
        split.addWidget(self.category_list)
        split.addWidget(self.stack)
        split.setStretchFactor(1, 1)
        root.addWidget(split, 1)

        # Status & Action Buttons
        self.status = QLabel(f"Configuration file: {self.store.path}")
        self.status.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")
        root.addWidget(self.status)

        buttons = QDialogButtonBox()
        self.apply_button = buttons.addButton("Apply", QDialogButtonBox.ApplyRole)
        self.save_button = buttons.addButton("Save & Close", QDialogButtonBox.AcceptRole)
        self.cancel_button = buttons.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.reset_button = buttons.addButton("Reset Defaults", QDialogButtonBox.ResetRole)

        self.apply_button.setStyleSheet(ComponentStyles.primary_button())
        self.save_button.setStyleSheet(ComponentStyles.primary_button())
        self.cancel_button.setStyleSheet(ComponentStyles.secondary_button())
        self.reset_button.setStyleSheet(ComponentStyles.danger_button())

        self.apply_button.clicked.connect(self._apply)
        self.save_button.clicked.connect(self._save_and_close)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self._reset)
        root.addWidget(buttons)

    def _create_page(self, key: str) -> QWidget:
        p = SettingsPage(key)
        self._populate_page(key, p)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(p)
        return scroll

    def _add(self, page: SettingsPage, path: str, label: str, widget: QWidget, help_text: str = ""):
        self.controls[path] = widget
        page.add_row(label, widget, help_text)

    def _populate_page(self, key: str, p: SettingsPage):
        if key == "Appearance":
            self._combo(p, "appearance.theme", "Theme", ["Dark", "Light", "High Contrast"])
            self._text(p, "appearance.accent", "Accent Color", DesignTokens.ACCENT_CYAN)
            self._combo(p, "appearance.density", "Interface Density", ["Compact", "Comfortable", "Spacious"])
            self._text(p, "appearance.font_family", "UI Font", "Segoe UI")
            self._spin(p, "appearance.font_size", "UI Font Size", 8, 24, " pt")
            self._spin(p, "appearance.ui_scale", "UI Scale", 75, 200, "%")
            for fld, lbl in [("animations", "Enable Animations"), ("show_icons", "Show Interface Icons"),
                             ("remember_layout", "Remember Window Layout"),
                             ("restore_last_workspace", "Restore Last Workspace")]:
                self._check(p, f"appearance.{fld}", lbl)

        elif key == "Editor":
            self._text(p, "editor.font_family", "Editor Font", "Cascadia Code")
            self._spin(p, "editor.font_size", "Editor Font Size", 8, 36, " pt")
            self._spin(p, "editor.tab_size", "Tab Size", 1, 16)
            for fld, lbl in [
                ("insert_spaces", "Insert Spaces"), ("word_wrap", "Word Wrap"),
                ("line_numbers", "Show Line Numbers"), ("minimap", "Show Minimap"),
                ("bracket_matching", "Bracket Matching"), ("auto_indent", "Auto-Indent"),
                ("format_on_save", "Format on Save"), ("trim_trailing_whitespace", "Trim Trailing Whitespace"),
                ("insert_final_newline", "Insert Final Newline"), ("autosave", "Enable Autosave")
            ]:
                self._check(p, f"editor.{fld}", lbl)
            self._spin(p, "editor.autosave_seconds", "Autosave Interval", 5, 600, " seconds")

        elif key == "Workspace":
            self._text(p, "workspace.default_projects_dir", "Projects Folder", str(Path.home() / "Projects"))
            self._text(p, "workspace.exclude_patterns", "Exclude Patterns", "**/.git/**, **/.venv/**, **/node_modules/**")
            self._check(p, "workspace.file_watcher", "Watch for External File Changes")
            self._check(p, "workspace.confirm_delete", "Confirm File Deletions")
            self._spin(p, "workspace.max_file_mb", "Max Editable File Size", 1, 500, " MB")

        elif key == "Terminal":
            self._combo(p, "terminal.shell", "Default Shell", ["PowerShell", "Command Prompt", "Git Bash", "WSL"])
            self._text(p, "terminal.font_family", "Terminal Font", "Cascadia Mono")
            self._spin(p, "terminal.font_size", "Terminal Font Size", 8, 30, " pt")
            self._spin(p, "terminal.scrollback_lines", "Scrollback Buffer", 100, 100000, " lines")
            self._check(p, "terminal.confirm_destructive_commands", "Confirm Destructive Shell Commands")

        elif key == "Models":
            self._text(p, "models.default_model_id", "Default Model ID", "ollama-qwen")
            self._spin(p, "models.request_timeout_seconds", "Request Timeout", 5, 3600, " s")
            self._double(p, "models.temperature", "Temperature", 0.0, 2.0, 0.1)
            self._double(p, "models.top_p", "Top-p", 0.0, 1.0, 0.05)
            self._spin(p, "models.max_output_tokens", "Max Tokens", 128, 131072)
            self._check(p, "models.allow_local_providers", "Allow Local Runtimes (Ollama, LM Studio, GGUF)")
            self._check(p, "models.allow_cloud_providers", "Allow Cloud Providers (Gemini, Claude, OpenAI)")
            
            probe_btn = QPushButton("🔍 Auto-Probe Local Engines & Toolchains")
            probe_btn.setStyleSheet(ComponentStyles.secondary_button())
            probe_btn.clicked.connect(self._run_connector_scan)
            p.form.addRow("Service Discovery", probe_btn)

            self.model_table = QTableWidget(0, 5)
            self.model_table.setHorizontalHeaderLabels(["ID", "Name", "Provider", "Model Tag", "Base URL"])
            self.model_table.horizontalHeader().setStretchLastSection(True)
            self.model_table.setMinimumHeight(160)
            self.model_table.setStyleSheet(ComponentStyles.table_view())
            p.form.addRow("Configured Models", self.model_table)

        elif key == "Agents":
            self._combo(p, "agents.mode", "Execution Mode", ["Fast", "Balanced", "Thorough", "User controlled"])
            self._spin(p, "agents.max_parallel_agents", "Max Parallel Subagents", 1, 32)
            self._spin(p, "agents.max_task_steps", "Max Steps per Task", 5, 500)
            self._spin(p, "agents.max_tool_calls", "Max Tool Calls", 5, 1000)
            for fld, lbl in [
                ("auto_plan", "Create Plans Automatically"),
                ("auto_test", "Run Verification Tests After Changes"),
                ("auto_review", "Review Changes Before Finalizing"),
                ("require_approval_for_shell", "Require Approval for Shell Commands"),
                ("require_approval_for_file_deletes", "Require Approval for File Deletion"),
                ("require_approval_for_network", "Require Approval for Network Requests")
            ]:
                self._check(p, f"agents.{fld}", lbl)

        elif key == "Tools":
            self._text(p, "tools.enabled_tools", "Enabled Tools", "read_file, search_files, apply_patch, run_tests")
            self._check(p, "tools.allow_mcp", "Enable Model Context Protocol (MCP)")
            self._check(p, "tools.allow_extensions", "Enable VS Code / Open VSX Extensions")
            self._combo(p, "tools.extension_trust", "Extension Trust Policy",
                        ["Ask before enabling", "Trusted publishers only", "Allow all"])

        elif key == "Security":
            self._check(p, "security.safe_mode", "Enable Safe Mode")
            self._check(p, "security.workspace_boundary", "Confine Edits to Workspace Directory")
            self._check(p, "security.redact_secrets_in_logs", "Redact API Keys & Passwords in Logs")
            self._check(p, "security.store_api_keys_in_os_keyring", "Store Credentials in Windows DPAPI / OS Keyring")
            self._check(p, "security.allow_telemetry", "Allow Telemetry (Disabled by Default)")
            self._check(p, "security.allow_crash_reports", "Allow Crash Reports (Disabled by Default)")

        elif key == "Privacy":
            self._check(p, "privacy.save_chat_history", "Save Chat History Locally")
            self._check(p, "privacy.local_index_only", "Keep AST Code Index 100% Local")
            self._check(p, "privacy.exclude_secrets_from_context", "Exclude Likely Secrets from Model Context")

        elif key == "Performance":
            self._combo(p, "performance.gpu_policy", "GPU Acceleration Policy",
                        ["Automatic", "Prefer GPU", "CPU only", "GPU required"])
            self._spin(p, "performance.cuda_vram_limit_mb", "CUDA VRAM Limit", 0, 98304, " MB")
            self._spin(p, "performance.gguf_gpu_layers", "GGUF GPU Offload Layers", 0, 120, " layers")
            self._spin(p, "performance.background_workers", "Background CPU Workers", 1, 64)
            self._spin(p, "performance.cache_mb", "Cache Memory Budget", 64, 65536, " MB")
            self._check(p, "performance.low_memory_mode", "Low-Memory Mode (For <= 8GB RAM)")
            self._check(p, "performance.pause_indexing_on_battery", "Pause Heavy Tasks on Battery")

        elif key == "Git":
            self._check(p, "git.enabled", "Enable Git Version Control Integration")
            self._check(p, "git.show_diff_before_ai_apply", "Show Visual Diff Before Applying AI Edits")
            self._check(p, "git.create_checkpoint_before_agent_changes", "Create Checkpoint Snapshot Before Edits")
            self._text(p, "git.default_branch", "Default Branch", "main")

        elif key == "Language":
            self._text(p, "language.python_interpreter", "Python Path", sys.executable)
            self._text(p, "language.test_command", "Test Command", "pytest")

        elif key == "Updates":
            self._check(p, "updates.check_automatically", "Check for Updates Automatically")
            self._combo(p, "updates.channel", "Release Channel", ["Stable", "Beta", "Nightly"])

        elif key == "Advanced":
            self._combo(p, "advanced.log_level", "Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"])
            self._check(p, "advanced.diagnostic_mode", "Enable Diagnostic Logging")

    def _check(self, p, path, label):
        w = QCheckBox(label)
        self._add(p, path, "", w)

    def _combo(self, p, path, label, choices):
        w = QComboBox()
        w.addItems(choices)
        self._add(p, path, label, w)

    def _spin(self, p, path, label, low, high, suffix=""):
        w = QSpinBox()
        w.setRange(low, high)
        if suffix:
            w.setSuffix(suffix)
        self._add(p, path, label, w)

    def _double(self, p, path, label, low, high, step):
        w = QDoubleSpinBox()
        w.setRange(low, high)
        w.setSingleStep(step)
        w.setDecimals(2)
        self._add(p, path, label, w)

    def _text(self, p, path, label, val=""):
        w = QLineEdit()
        w.setText(str(val))
        self._add(p, path, label, w)

    def _get_path(self, path: str):
        node = self.working
        for part in path.split("."):
            node = node[part]
        return node

    def _set_path(self, target: Dict[str, Any], path: str, value: Any):
        parts = path.split(".")
        node = target
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def _load_controls(self):
        for path, widget in self.controls.items():
            try:
                val = self._get_path(path)
            except Exception:
                continue
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(val))
            elif isinstance(widget, QComboBox):
                idx = widget.findText(str(val))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(val)
            elif isinstance(widget, QLineEdit):
                if isinstance(val, list):
                    val = ", ".join(map(str, val))
                widget.setText(str(val))
        self._load_model_table()

    def _load_model_table(self):
        if not hasattr(self, "model_table"):
            return
        models = self.working.get("models", {}).get("models", [])
        self.model_table.setRowCount(len(models))
        for r, m in enumerate(models):
            for c, k in enumerate(["id", "name", "provider", "model", "base_url"]):
                self.model_table.setItem(r, c, QTableWidgetItem(str(m.get(k, ""))))

    def _collect_controls(self) -> Dict[str, Any]:
        result = copy.deepcopy(self.working)
        for path, widget in self.controls.items():
            if isinstance(widget, QCheckBox):
                val = widget.isChecked()
            elif isinstance(widget, QComboBox):
                val = widget.currentText()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                val = widget.value()
            elif isinstance(widget, QLineEdit):
                raw = widget.text().strip()
                if path.endswith(("exclude_patterns", "fallback_model_ids", "enabled_tools")):
                    val = [x.strip() for x in raw.split(",") if x.strip()]
                else:
                    val = raw
            else:
                continue
            self._set_path(result, path, val)

        result["profile"] = self.profile.currentText()
        return result

    def _run_hardware_autotune(self):
        """Auto-detects host hardware and synthesizes optimal tuning parameters live."""
        res = HardwareAutoTuner.synthesize_tuning()
        self.working = HardwareAutoTuner.apply_to_settings(self.working, res)
        self._load_controls()
        
        info = (
            f"Hardware Tuned Successfully!\n\n"
            f"Detected Tier: {res.suggested_tier}\n"
            f"CPU: {res.profile.cpu_threads} threads ({res.profile.cpu_model})\n"
            f"RAM: {res.profile.ram_total_mb} MB\n"
            f"GPU: {res.profile.gpu_name} ({res.profile.vram_total_mb} MB VRAM)\n\n"
            f"Summary: {res.diagnostic_summary}\n\n"
            f"Settings updated live in the dialog. Click 'Save & Close' to persist."
        )
        QMessageBox.information(self, "Hardware Auto-Tuning Complete", info)

    def _run_connector_scan(self):
        """Scans local ports and developer toolchains, adding active engines to model table."""
        scan = ConnectorGateway.full_system_scan()
        models = self.working.setdefault("models", {}).setdefault("models", [])
        
        added = []
        for svc in scan["services"]:
            if svc["category"] == "local_ai" and svc["status"] == "online":
                # Check if already in model list
                existing = [m for m in models if m.get("id") == svc["service_id"]]
                if not existing:
                    models.append({
                        "id": svc["service_id"],
                        "name": svc["name"],
                        "provider": svc["name"],
                        "model": "qwen2.5:1.5b",
                        "base_url": svc["endpoint_or_path"],
                        "api_key_env": "",
                        "enabled": True,
                        "capabilities": ["chat", "code"],
                        "notes": "Auto-discovered active local AI engine."
                    })
                    added.append(svc["name"])

        self._load_model_table()
        msg = f"Discovered {scan['available_toolchains_count']} toolchains and {scan['active_local_ai_count']} active AI engine(s)."
        if added:
            msg += f"\nAdded to model list: {', '.join(added)}"
        QMessageBox.information(self, "Connector Scan Results", msg)

    def _apply(self):
        updated = self._collect_controls()
        self.store.data = updated
        self.store.save()
        self.working = copy.deepcopy(updated)
        self.settings_applied.emit(copy.deepcopy(updated))
        self.status.setText(f"Applied and saved: {self.store.path}")

    def _save_and_close(self):
        self._apply()
        self.accept()

    def _reset(self):
        if QMessageBox.question(self, "Reset Settings", "Reset all settings to application defaults?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.working = copy.deepcopy(DEFAULTS)
            self._load_controls()

    def _filter_categories(self, query: str):
        query = query.casefold().strip()
        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            key = item.data(Qt.UserRole)
            searchable = key + " " + item.text()
            item.setHidden(bool(query) and query not in searchable.casefold())

    def _apply_obsidian_styles(self):
        t = DesignTokens
        self.setStyleSheet(f"""
            QDialog {{ background: {t.CANVAS_BG}; color: {t.TEXT_PRIMARY}; }}
            QWidget {{ color: {t.TEXT_PRIMARY}; font-family: {t.FONT_FAMILY_UI}; }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
                background: {t.SURFACE_ELEVATED};
                border: 1px solid {t.BORDER_MUTED};
                border-radius: {t.RADIUS_SM};
                padding: 6px;
                color: {t.TEXT_PRIMARY};
                selection-background-color: {t.ACCENT_CYAN};
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border-color: {t.ACCENT_CYAN};
            }}
            QListWidget {{
                background: {t.SURFACE_PANEL};
                border: 1px solid {t.BORDER_SUBTLE};
                border-radius: {t.RADIUS_MD};
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: {t.RADIUS_SM};
                color: {t.TEXT_SECONDARY};
            }}
            QListWidget::item:selected {{
                background: {t.SURFACE_HOVER};
                color: {t.ACCENT_CYAN};
                font-weight: bold;
                border-left: 3px solid {t.ACCENT_CYAN};
            }}
            QScrollArea {{ border: none; background: transparent; }}
        """)
