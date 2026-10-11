# PRUBETH IDE — Developer & Extension Authoring Guide
## Extensibility Architecture, Custom Tools, Model Integration & Plugin Ecosystem

> **PRUBETH IDE (v3.0.0)** is designed from the foundation as an extensible, AI-native developer environment.
> This guide provides step-by-step documentation for engineers building **plugins**, **autonomous agent tools**, **custom AI model providers**, **LSP language servers**, **DAP debug adapters**, and **UI mods**.

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Plugin & Extension System](#2-plugin--extension-system)
   - [Plugin Directory & Manifest (`plugin.json`)](#plugin-directory--manifest-pluginjson)
   - [Sandboxed Permissions](#sandboxed-permissions)
   - [Lifecycle Hooks & Events](#lifecycle-hooks--events)
   - [Complete Plugin Example](#complete-plugin-example)
3. [Autonomous Tool Dispatcher (`horizon_engine/tool_dispatcher.py`)](#3-autonomous-tool-dispatcher)
   - [Defining Tool Schemas](#defining-tool-schemas)
   - [Registering Custom Tools](#registering-custom-tools)
   - [Approval Gates & Risk Levels](#approval-gates--risk-levels)
4. [Custom AI Models & Provider Integration](#4-custom-ai-models--provider-integration)
   - [Connecting OpenAI-Compatible Inference Servers](#connecting-openai-compatible-inference-servers)
   - [Registering Custom Ollama Models & Local Weights](#registering-custom-ollama-models--local-weights)
   - [Custom Model Routing Tier](#custom-model-routing-tier)
5. [Language Services (LSP) & Syntax Lexers](#5-language-services-lsp--syntax-lexers)
   - [Adding an LSP Language Server](#adding-an-lsp-language-server)
   - [Custom QScintilla Syntax Highlighting](#custom-qscintilla-syntax-highlighting)
6. [Debugging (DAP) Adapters](#6-debugging-dap-adapters)
7. [UI Themes & Mod Hub Panes](#7-ui-themes--mod-hub-panes)
8. [Testing, Quality Assurance & Packaging](#8-testing-quality-assurance--packaging)

---

## 1. Architecture Overview

PRUBETH IDE is divided into modular, loosely coupled subsystems:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRUBETH IDE HORIZON UI                          │
│        (Obsidian Glassmorphic Aesthetic · Beacon · Mod Hub)            │
├───────────────────────────────────┬────────────────────────────────────┤
│         EDITOR & LANGUAGE         │         AGENT & INFERENCE          │
│   • QScintilla Polyglot Lexers    │   • Intelligent Model Cascade      │
│   • Multi-Root Workspace Guard    │   • Horizon Context Engine         │
│   • LSP Client & DAP Debugger     │   • Autonomous Tool Dispatcher     │
├───────────────────────────────────┴────────────────────────────────────┤
│                       EXTENSIBILITY FOUNDATION                         │
│   • Plugin Manager & Sandbox (`plugins/`)                              │
│   • Structured Tool Dispatcher (`horizon_engine/tool_dispatcher.py`)   │
│   • Model Provider Connector (`horizon_engine/connector_gateway.py`)   │
│   • Hardware Autotuner & Scaling Engine (`horizon_engine/`)            │
│   • Task Engine & Transactional Checkpoints (`core/`)                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Plugin & Extension System

The PRUBETH IDE plugin system isolates extensions in an audited, permission-governed environment (`plugins/manager.py` and `plugins/sandbox.py`).

### Plugin Directory & Manifest (`plugin.json`)

Extensions reside in either:
- **Built-in Plugins:** `plugins/` in the IDE root.
- **User Plugins:** `%USERPROFILE%\.local_ai_studio_pro\plugins\` (Windows) or `~/.local_ai_studio_pro/plugins/` (Linux/macOS).

Each extension is a directory containing a `plugin.json` manifest and an entry point script (e.g., `main.py`):

```json
{
  "plugin_id": "com.developer.git_blame_lens",
  "name": "Git Blame Lens",
  "version": "1.0.0",
  "description": "Displays inline git blame annotations and commit telemetry in the active editor buffer.",
  "author": "Engineering Lead <dev@example.com>",
  "entry_point": "main.py",
  "permissions": [
    "read_workspace",
    "exec_command",
    "ui_panel"
  ],
  "enabled": true,
  "dependencies": []
}
```

### Sandboxed Permissions

PRUBETH enforces least-privilege security using the `PluginPermission` enum:

| Permission | Description |
| :--- | :--- |
| `read_workspace` | Read files inside the active workspace boundaries. |
| `write_workspace` | Modify files inside the active workspace (subject to atomic backup). |
| `exec_command` | Execute shell commands in the terminal environment. |
| `network` | Perform outbound HTTP/WebSocket network calls. |
| `ai_inference` | Dispatch queries directly to the active AI Model Cascade. |
| `ui_panel` | Inject custom widgets, panels, or statusbar elements into the GUI. |

### Lifecycle Hooks & Events

Extensions subscribe to lifecycle events via the `HookRegistry`:

- `HookEvent.APP_STARTUP`: Fired when the IDE completes initialization.
- `HookEvent.WORKSPACE_OPEN`: Fired when a workspace or project root is opened.
- `HookEvent.FILE_SAVE`: Fired before and after a file is committed to disk.
- `HookEvent.AGENT_PRE_TOOL`: Fired before an autonomous agent executes a tool.
- `HookEvent.AGENT_POST_TOOL`: Fired after a tool completes execution.
- `HookEvent.TEST_RUN`: Fired when tests are executed or auto-fixed.

### Complete Plugin Example

Create a folder named `plugins/quick_metrics/` with:

**`plugins/quick_metrics/plugin.json`**:
```json
{
  "plugin_id": "com.prubeth.quick_metrics",
  "name": "Quick Code Metrics",
  "version": "1.0.0",
  "description": "Calculates SLOC, cyclomatic complexity, and test coverage on save.",
  "author": "PRUBETH Systems",
  "entry_point": "main.py",
  "permissions": ["read_workspace", "ui_panel"],
  "enabled": true
}
```

**`plugins/quick_metrics/main.py`**:
```python
"""Quick Code Metrics Plugin Entry Point."""
from plugins.hooks import HookRegistry, HookEvent
from plugins.sandbox import PluginContext

def on_file_saved(data: dict, context: PluginContext):
    file_path = data.get("file_path")
    if not file_path or not file_path.endswith(".py"):
        return

    # Safe read via sandboxed context
    content = context.read_file(file_path)
    lines = content.splitlines()
    loc = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
    
    print(f"[QuickMetrics] {file_path}: {loc} physical lines of code.")

def activate(context: PluginContext, hooks: HookRegistry):
    """Called by PluginManager upon IDE startup or plugin enable."""
    print(f"[+] Activating {context.manifest.name} (v{context.manifest.version})")
    hooks.register(HookEvent.FILE_SAVE, lambda data: on_file_saved(data, context))

def deactivate(context: PluginContext, hooks: HookRegistry):
    """Called on IDE shutdown or when the plugin is disabled."""
    print(f"[-] Deactivating {context.manifest.name}")
```

---

## 3. Autonomous Tool Dispatcher

PRUBETH IDE features a structured, risk-gated tool dispatcher (`horizon_engine/tool_dispatcher.py`). Tools can be registered by plugins or core modules to grant autonomous AI agents new capabilities.

### Defining Tool Schemas

Use `ToolSchema` and `ToolParameter` to declare typed tool inputs:

```python
from horizon_engine.tool_dispatcher import ToolSchema, ToolParameter, ToolRegistry

def create_weather_tool(registry: ToolRegistry):
    schema = ToolSchema(
        name="fetch_weather",
        description="Retrieves current weather and meteorological conditions for a city.",
        parameters=[
            ToolParameter("city", "string", "City name, e.g. London or Tokyo", required=True),
            ToolParameter("units", "string", "Unit format: metric or imperial", required=False, default="metric"),
        ],
        returns="string",
        category="external_apis",
        requires_approval=False  # Set to True for destructive actions (e.g. drop database)
    )

    def execute_weather(city: str, units: str = "metric"):
        # Implementation logic
        return f"Weather in {city}: 21°C, Clear Sky (Units: {units})"

    registry.register(schema, execute_weather)
```

### Approval Gates & Risk Levels

If `requires_approval=True`, the IDE pauses execution and displays a modal prompt in the GUI or CLI asking the developer to approve or deny the action before any code runs:

```python
schema = ToolSchema(
    name="deploy_to_kubernetes",
    description="Deploys image to production cluster.",
    parameters=[ToolParameter("manifest", "string", "K8s YAML manifest", required=True)],
    returns="string",
    category="devops",
    requires_approval=True  # Developer confirmation enforced
)
```

---

## 4. Custom AI Models & Provider Integration

PRUBETH IDE uses a **3-Tier Priority Model Cascade** (`Tier 1 Cloud Flagship`, `Tier 2 Fast Cloud`, `Tier 3 Local CUDA GPU`). You can add custom inference backends via the `ConnectorGateway` (`horizon_engine/connector_gateway.py`).

### Connecting OpenAI-Compatible Inference Servers

You can connect local or remote inference engines (vLLM, Ollama, LocalAI, LM Studio, TextGenWebUI):

In `settings.json` (`~/.local_ai_studio_pro/settings.json`):

```json
{
  "model_router": {
    "custom_providers": [
      {
        "provider_id": "local_vllm",
        "name": "Local vLLM Server (RTX 4090)",
        "api_base": "http://127.0.0.1:8000/v1",
        "api_key": "EMPTY",
        "model_id": "meta-llama/Llama-3.1-70B-Instruct",
        "context_window": 131072,
        "temperature": 0.2,
        "tier": 1
      }
    ]
  }
}
```

### Programmatic Provider Registration

```python
from horizon_engine.connector_gateway import ConnectorGateway, ProviderConfig

gateway = ConnectorGateway()
gateway.register_provider(ProviderConfig(
    name="mistral_large",
    endpoint="https://api.mistral.ai/v1/chat/completions",
    auth_header="Bearer {MISTRAL_API_KEY}",
    max_context_tokens=128000,
    supports_streaming=True
))
```

---

## 5. Language Services (LSP) & Syntax Lexers

### Adding an LSP Language Server

PRUBETH IDE includes a universal Language Server Protocol client (`language_services/lsp_client.py`). To attach a language server for a new programming language (e.g. Rust, Go, Zig):

In `language_services/config.json`:

```json
{
  "servers": {
    "rust": {
      "command": "rust-analyzer",
      "args": [],
      "file_extensions": [".rs"],
      "root_markers": ["Cargo.toml"]
    },
    "go": {
      "command": "gopls",
      "args": ["serve"],
      "file_extensions": [".go"],
      "root_markers": ["go.mod"]
    },
    "zig": {
      "command": "zls",
      "args": [],
      "file_extensions": [".zig"],
      "root_markers": ["build.zig"]
    }
  }
}
```

### Custom QScintilla Syntax Highlighting

To add custom lexers or styles, configure `language_services/lexers.py`. Custom keywords, comments, and operator tokens inherit the Obsidian Hologram palette (`#00F0FF`, `#D946EF`, `#76B900`).

---

## 6. Debugging (DAP) Adapters

The debugging subsystem (`debugging/`) communicates over Debug Adapter Protocol:

1. **Python (`debugpy`)**: Pre-configured out of the box.
2. **Node.js (`vscode-js-debug`)**: Connects over WebSocket or TCP port `9229`.
3. **C/C++ / Rust (`lldb-vscode` / `gdb`)**: Integrated through GDB/LLDB adapters.

To configure a new debugger, register the adapter launch configuration in `.prubeth/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Rust: Debug Binary",
      "type": "lldb",
      "request": "launch",
      "program": "${workspaceFolder}/target/debug/app",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

---

## 7. UI Themes & Mod Hub Panes

Developers can create interactive side-pane widgets and visual modulations through PyQt5 extension hooks:

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

class DeveloperStatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("🚀 Custom Telemetry Mod")
        label.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 14px;")
        layout.addWidget(label)

def install_ui_panel(ide_window):
    """Called during plugin initialization."""
    panel = DeveloperStatusPanel()
    ide_window.right_dock_tabs.addTab(panel, "Telemetry")
```

---

## 8. Testing, Quality Assurance & Packaging

All extensions and core contributions must maintain PRUBETH IDE's **100% test pass rate**.

### Running Automated Verification

```powershell
# Run the complete test suite (254 verification gates)
pytest -v

# Run plugin-specific tests
pytest tests/test_plugins.py tests/test_gate11_plugin_host_sandbox.py -v
```

### Building the Distribution

```powershell
# Compile the unified setup wizard with your custom plugins bundled
python build_setup_exe.py
```

---

<div align="center">
  <p><b>PRUBETH IDE Extensibility Engine · Engineered for Sovereign Developer Flow</b></p>
  <p><a href="https://www.bsvr.work/">Official Website</a> · <a href="https://github.com/imyouiamyou/prubeth-ide">GitHub Repository</a></p>
</div>
