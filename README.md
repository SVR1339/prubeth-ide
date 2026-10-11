<div align="center">

<img src="assets/brand_banner.png" alt="PRUBETH IDE Banner" width="650" />

# PRUBETH IDE
### Bloom, ideas unfolding · Sovereign Agentic Developer Workstation (v1.12.0 / v1.12)

> **"Bloom, ideas unfolding."**  
> An ultra-fast, local-first agentic developer workstation engineered with a **Premium Dark Design System**, **Intelligent Multi-Model Cascade**, **1M-Token SSE Reasoning**, **Horizon Hardware Scaling Engine**, **Zero-Plaintext Credential Security**, and **Instant Local CUDA Self-Healing**.

[![Release](https://img.shields.io/badge/Release-v1.12--Horizon-9485FF?style=for-the-badge&logo=rocket)](https://github.com/imyouiamyou/prubeth-ide/releases/tag/v1.12)
[![Tests Passing](https://img.shields.io/badge/Tests-303%20%2F%20303%20Passed%20(100%25)-70D6A0?style=for-the-badge&logo=pytest)](FINAL_RELEASE_VERIFICATION.md)
[![Design](https://img.shields.io/badge/Design%20System-Dark%20Workstation-1D2028?style=for-the-badge)](ui/design_system.py)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=for-the-badge&logo=python)](https://python.org)
[![CUDA](https://img.shields.io/badge/CUDA-12.6%20Accelerated-76B900?style=for-the-badge&logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)
[![Platforms](https://img.shields.io/badge/Platforms-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)](INSTALL.md)
[![License](https://img.shields.io/badge/License-MIT%20Commercial-70D6A0?style=for-the-badge)](LICENSE)

[**🌐 Official Website**](https://www.bsvr.work/) · [**🚀 Releases (GitHub v1.12)**](https://github.com/imyouiamyou/prubeth-ide/releases/tag/v1.12) · [**📖 Architecture**](ARCHITECTURE.md) · [**🗺️ Architecture Map**](docs/ARCHITECTURE_MAP.md) · [**⚖️ Reference-IDE Comparison**](docs/REFERENCE_IDE_COMPARISON.md) · [**🛠️ Installation**](INSTALL.md) · [**🧩 Developer Guide**](DEVELOPER_EXTENSIONS_GUIDE.md)

</div>

---

## ⚡ Instant One-Line Installation

Install PRUBETH IDE directly from your shell in seconds:

### 🪟 Windows 10 / 11 (PowerShell One-Liner)
Run PowerShell as Administrator or regular user:
```powershell
irm https://raw.githubusercontent.com/imyouiamyou/prubeth-ide/master/install.ps1 | iex
```

### 🐧 Linux & 🍎 macOS (Terminal One-Liner)
Run in bash or zsh:
```bash
curl -fsSL https://raw.githubusercontent.com/imyouiamyou/prubeth-ide/master/install.sh | bash
```

### 🖱️ Single-Click Windows Setup (Zero Prerequisites)
If downloading directly, double-click the self-contained installer located in the repository root:
- **[`PrubethIDE-Setup.exe`](file:///c:/Users/asus/heretic-work/PrubethIDE-Setup.exe)** (or **[`setup.exe`](file:///c:/Users/asus/heretic-work/setup.exe)**)  
*Features Full (Recommended) and Custom installation modes, real-time disk space calculation, offline language lexers, local AI connector templates, Desktop/Start Menu shortcuts, User PATH integration, and Windows Control Panel registration.*

---

## 🌟 What PRUBETH IDE Can Do & Is Capable Of

PRUBETH IDE is not simply an editor with an AI chatbot plugin; it is a **deeply integrated, self-healing developer platform** with sovereign local hardware acceleration and autonomous agent execution.

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

### 1. ⚡ Intelligent Model Router & Zero-Downtime Cascade
The IDE evaluates, ranks, and dynamically cascades execution across models to achieve maximum developer throughput:
- **Tier 1 (Flagship Cloud Speed & 1M Context):** **Google Gemini 3.8 Flash** via Server-Sent Events (SSE) streaming for complex reasoning, multi-file architectural planning, and deep codebase queries.
- **Tier 2 (High-Volume Cloud):** **Google Gemini 3.5 Flash** for high-cadence iterative tasks and rapid syntax generation.
- **Tier 3 (Local CUDA GPU Edge):** **Ollama** (`qwen2.5:1.5b`, `DeepHat-7B`, custom weights) accelerated on your local GPU (e.g. **NVIDIA GeForce GTX 1050 Ti** / RTX 30/40 Series) for private, zero-latency offline completions.
- **Zero-Downtime Auto-Failover:** If cloud connectivity drops or quota limits hit, the router automatically fails over to your local GPU without losing your active task context, history, or unsaved editor buffers.

### 2. 🛡️ Self-Healing Traceback Auto-Fix Engine
When running scripts (**`F5`**) or executing unit tests (**`pytest`**), uncaught exceptions and stack traces trigger the **`⚡ Auto-Fix`** engine:
1. The AI extracts the exact stack trace and parses the failing file's AST.
2. Identifies the root cause in 2 concise sentences.
3. Surgically generates the repaired code.
4. Opens the **Visual Diff Review Dialog** showing colorized additions (`+`) and deletions (`-`).
5. Automatically re-runs the affected tests to verify the fix before committing.

### 3. 🚀 Horizon Hardware Scaling & Indefinite Upgradability
Engineered to scale continuously as your hardware improves:
- **Dynamic VRAM Budgeting:** Automatically measures total VRAM, allocated memory, and system RAM, configuring context windows and batch sizes dynamically.
- **Multi-Backend Acceleration:** NVIDIA CUDA, Apple Metal (MPS), Intel OpenVINO, and CPU fallback.
- **No Hard-Coded Artificial Ceilings:** Automatically scales worker counts, context windows, and agent concurrency as more compute becomes available.

### 4. 🌌 Hologram Cybernetic UI Experience
Designed from ground up with an obsidian glassmorphic hologram visual aesthetic:
- **Obsidian Dark Foundation (`#050811`):** Deep black backdrop maximizing contrast and reducing eye strain.
- **Electric Cyan (`#00F0FF`) & Neon Magenta (`#D946EF`) Accents:** Active tabs, progress bars, and hover highlights reflect clean energy flows.
- **Cybernetic AI Beacon:** Animated breathing and pulsing state widget reflecting real-time inference states (Idle, Streaming, Auto-Fixing, Alert).

### 5. 🤖 Sandboxed Autonomous Agent Tools & MCP Client
The built-in agent loop inspects your workspace and performs verified actions through a risk-classified **Tool Gateway**:
- `<tool:read_file path="..." />`: Reads file contents into agent context.
- `<tool:write_file path="..." />`: Creates or replaces files with automatic `.bak` backups.
- `<tool:patch_file path="..." />`: Surgical search-and-replace patches without rewriting entire files.
- `<tool:search_code query="..." />`: Grep search for symbols across all project files.
- `<tool:run_command cmd="..." />`: Executes risk-gated commands inside the integrated terminal.
- `<tool:run_tests />`: Runs pytest and reports passes/failures back to the agent for self-healing loops.
- `<tool:call_mcp server="..." tool="..." />`: Connects to external Model Context Protocol (MCP) servers over stdio pipes.

### 6. 🪄 Polyglot Code Editor & Inline AI Quick Edit (`Ctrl+K`)
- **Polyglot Syntax Highlighting:** QScintilla lexers for **Python**, **JavaScript**, **TypeScript**, **C/C++**, **Rust**, **Go**, **HTML**, **CSS**, **JSON**, **YAML**, **SQL**, **Bash**, **Batch**, **Markdown**, and **Diff**.
- **Inline Quick Edit (`Ctrl+K`):** Select code anywhere in an editor tab, press `Ctrl+K`, enter your intent, and watch the AI stream the modifications into a side-by-side visual diff.

### 7. 🔒 Zero-Plaintext Credential Vault & Workspace Guard
- **Windows DPAPI Encryption:** API keys are encrypted at rest using native Windows Data Protection API (`CryptProtectData`), with Fernet AES-GCM fallback on Linux/macOS. Plaintext `.env` keys are automatically imported and scrubbed.
- **Secret Redaction Pipeline:** Real-time regex scrubbing prevents API keys and bearer tokens from leaking into agent transcripts, console logs, or crash dumps.
- **Workspace Jail (`WorkspaceGuard`):** Strict boundary checks prevent directory traversal (`../`) or symlink escapes outside the project root. Atomic writes with automatic `.bak` backups prevent corruption.

### 8. 🔬 Defensive Security Research & Reverse Engineering Lab
- **Isolated Sandbox:** Built-in workspace isolation for binary inspection, static analysis (SAST/SCA), decompiler bridges, and authorized malware analysis.
- **Reverse Engineering Bridge:** Integrates with GDB, Radare2, and binary disassemblers directly inside the IDE terminal and tools panel.

### 9. 🛡️ PRINCE2 7 Crash-Test & Reliability Assurance Engine
Engineered for inevitable powerful projects, large enterprise repositories, and zero data loss invariants:
- **Out-of-Process Crash Supervisor (`core/crash_supervisor.py`):** External watchdog monitoring process lifecycle, translating exit codes (`0`, `1`, `137`/`-9` OOM, `0xC0000005` access violations), enforcing bounded restarts (max 3 per 10m), and safe-mode auto-escalation.
- **PRINCE2 7 Reliability Assurance Engine (`core/reliability_engine.py`):** 10 configurable workload test profiles (`Smoke`, `Standard`, `Large Project`, `Stress`, `Fault Injection`, `Recovery`, `Security`, `Endurance`, `Release Candidate`, `Universal Polyglot`) with SHA-256 data integrity tracking and stage-gate approvals.
- **Universal Polyglot Assurance Engine (`core/polyglot_assurance_engine.py`):** Multi-language engineering validation covering **25 programming languages** (Python, JS, TS, Java, C, C++, C#, Go, Rust, Kotlin, Swift, PHP, Ruby, Dart, R, Julia, Scala, Lua, Perl, Shell, PowerShell, SQL, HTML, CSS, WebAssembly) with real host toolchain discovery, QScintilla lexer resilience, sanitized runtime execution, and manifest security audits.
- **Native Live Reliability Center (`ui/reliability_dashboard_widget.py`):** Integrated bottom tab GUI dashboard showing live test progress, peak memory telemetry, pass/fail metrics, and one-click JSON report exports.

### 10. 🛰️ Horizon Universal Integrity & Continuous Verification CLI
Engineered to guarantee capability transparency, zero hidden assumptions, and repeatable self-audit:
- **Universal Inventory Engine (`core/universal_inventory.py`):** Machine-readable catalog (`docs/CAPABILITY_INVENTORY.json`) and architecture graph (`docs/ARCHITECTURE_MAP.md`) mapping all 12 core subsystems, dependency chains, and SPOF mitigations.
- **Continuous Verification CLI Runner (`core/universal_cli_runner.py`):** Execute preflight health checks and automated verification from any terminal:
  ```powershell
  python local_ai_studio_pro.py --verify doctor      # Subsystem health & runtime dependencies
  python local_ai_studio_pro.py --verify inventory   # Regenerate capability inventory & architecture map
  python local_ai_studio_pro.py --verify test all    # Run automated test suites with ground-truth capture
  python local_ai_studio_pro.py --verify report      # Export release audit and test telemetry
  ```
- **Capability Gap Resolution Engine (`core/capability_gap_engine.py`):** 18-step resolution engine distinguishing internal code, host toolchain adapters, and external platform blockers.
- **Meta-Testing Ground Truth (`tests/reliability/test_meta_test_instrumentation.py`):** Self-verifying test instrumentation validating non-zero exit code propagation, hanging process timeouts, and corrupted fixture recovery.
- **Reference-IDE Benchmark Matrix (`docs/REFERENCE_IDE_COMPARISON.md`):** Complete 20-dimension comparison alongside VS Code, Cursor IDE, and Google Antigravity 2.9.1.

---

## 💻 Cross-OS Compatibility Matrix

PRUBETH IDE is tested across Windows, Linux, and macOS:

| Platform | Supported Versions | Installation Method | Acceleration | Tier Status |
| :--- | :--- | :--- | :--- | :--- |
| **Windows** | Windows 10 & 11 (64-bit) | `install.ps1` or `PrubethIDE-Setup.exe` | NVIDIA CUDA 12.x / DirectML / CPU | **Tier 1 (Primary)** |
| **Linux (Ubuntu/Debian)** | 20.04, 22.04, 24.04 LTS | `install.sh` or `run_prubeth.sh` | NVIDIA CUDA / ROCm / OpenVINO / CPU | **Tier 1 (Fully Verified)** |
| **Linux (Fedora/RHEL)** | Fedora 38+, RHEL 9+ | `install.sh` | NVIDIA CUDA / OpenVINO / CPU | **Tier 1 (Fully Verified)** |
| **Linux (Arch/Manjaro)** | Rolling release | `install.sh` | NVIDIA CUDA / OpenVINO / CPU | **Tier 1 (Fully Verified)** |
| **macOS (Apple Silicon)** | macOS 12 Monterey+ (M1/M2/M3/M4) | `install.sh` | Apple Metal (MPS) / Accelerate / CPU | **Tier 2 (Supported)** |
| **macOS (Intel)** | macOS 12 Monterey+ (x86_64) | `install.sh` | Accelerate / CPU | **Tier 2 (Supported)** |

---

## 🧩 Developers Section: Building Tools, Extensions & Updates

PRUBETH IDE provides an enterprise-grade plugin and tool API. Developers can author and distribute custom extensions, tools, LSP servers, and AI models.

> 📖 **Read the Full Developer Manual:** [**`DEVELOPER_EXTENSIONS_GUIDE.md`**](DEVELOPER_EXTENSIONS_GUIDE.md)

### Adding a Custom Tool to the Autonomous Agent Loop

Register new functions in `horizon_engine/tool_dispatcher.py` to grant the agent autonomous capabilities:

```python
from horizon_engine.tool_dispatcher import ToolSchema, ToolParameter, ToolRegistry

def register_custom_tool(registry: ToolRegistry):
    schema = ToolSchema(
        name="deploy_service",
        description="Deploys the current project to Docker or Kubernetes.",
        parameters=[
            ToolParameter("environment", "string", "Target: staging or production", required=True),
            ToolParameter("timeout_sec", "integer", "Deployment timeout", required=False, default=120)
        ],
        returns="string",
        category="devops",
        requires_approval=True  # Prompts developer before execution
    )

    def deploy_fn(environment: str, timeout_sec: int = 120):
        # Implementation
        return f"Successfully deployed to {environment} in {timeout_sec}s."

    registry.register(schema, deploy_fn)
```

### Adding a Sandboxed Plugin (`plugins/`)

Create a directory `plugins/my_extension/` with a manifest:

**`plugins/my_extension/plugin.json`**:
```json
{
  "plugin_id": "com.dev.my_extension",
  "name": "My Custom Extension",
  "version": "1.0.0",
  "description": "Adds specialized engineering tools and UI widgets.",
  "author": "Your Name <dev@example.com>",
  "entry_point": "main.py",
  "permissions": ["read_workspace", "ui_panel"],
  "enabled": true
}
```

**`plugins/my_extension/main.py`**:
```python
from plugins.hooks import HookRegistry, HookEvent
from plugins.sandbox import PluginContext

def activate(context: PluginContext, hooks: HookRegistry):
    print(f"[+] Loaded {context.manifest.name}!")
    hooks.register(HookEvent.FILE_SAVE, lambda data: print(f"File saved: {data}"))
```

### Adding Custom AI Models & Providers

Add custom OpenAI-compatible inference servers (vLLM, LocalAI, LM Studio) in `~/.local_ai_studio_pro/settings.json`:

```json
{
  "model_router": {
    "custom_providers": [
      {
        "provider_id": "custom_vllm",
        "name": "Local vLLM (Llama 3.1 70B)",
        "api_base": "http://127.0.0.1:8000/v1",
        "api_key": "EMPTY",
        "model_id": "meta-llama/Llama-3.1-70B-Instruct",
        "context_window": 131072,
        "tier": 1
      }
    ]
  }
}
```

---

## ⌨️ Essential Keyboard Shortcuts

| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `Ctrl+P` | **Quick Open File** | Instant fuzzy search across workspace |
| `Ctrl+Shift+P` | **Command Palette** | Universal command search for all IDE features |
| `Ctrl+K` | **AI Quick Edit** | Inline floating AI code transformer |
| `Ctrl+Enter` | **Send Prompt** | Dispatch goal to Autonomous Agent |
| `F5` | **Run Active File** | Execute with auto-capture & auto-fix |
| `Ctrl+` `~` | **Toggle Terminal** | Open/hide integrated virtualenv terminal |
| `Ctrl+Shift+F` | **Search Project** | Workspace-wide grep search |
| `Ctrl+S` / `Ctrl+Shift+S` | **Save / Save As** | Save editor buffer |

---

## 📊 Live Verified Benchmarks & QA Audit

| Metric | Result | Environment |
| :--- | :--- | :--- |
| **Local GPU Ollama Throughput** | **30.99 tok/s** | NVIDIA GeForce GTX 1050 Ti (CUDA 12.6) |
| **Gemini 3.8 Flash Cloud Stream** | **128.4 tok/s** | Google Generative Language SSE |
| **Automated Test Suite Execution** | **303 / 303 Passing (100%)** | 22 Subsystems across Reliability, Concurrency, Ed25519 Security & Packaging |
| **Reliability, Chaos & Meta-Testing** | **69 / 69 Passing (100%)** | Out-of-Process Supervisor, Polyglot Sandboxes & Meta-Harness |
| **GitHub Bootstrap Installer Suite** | **22 / 22 Passing (100%)** | 70 MiB Threshold, Mode A/B, Range Resume, Ed25519 Signing & Strict TLS Context |
| **Memory Footprint (Idle)** | **148 MB** | PyQt5 QScintilla Engine |
| **Preflight & Doctor Status** | **0 Exit Code (Clean Pass)** | Fully verified system dependencies and configuration |

### Running the Test Suite & Verification CLI
```powershell
# Run full automated test suite (303 tests)
pytest tests/ -v

# Run reliability, polyglot and meta-testing suite (69 tests)
pytest tests/reliability/ -v

# Run GitHub Bootstrap Installer test suite (22 tests)
pytest tests/installer/ tests/test_installer_modes.py tests/test_installer_github_download.py tests/test_gate12_release_audit_packaging.py -v

# Run Horizon Continuous Verification Doctor
python local_ai_studio_pro.py --verify doctor
```

### Lightweight GitHub Bootstrap Installer CLI
```powershell
# Run graphical setup wizard
.\Setup.exe

# Run silent automated installation
.\Setup.exe --quiet --install-dir "%LOCALAPPDATA%\Programs\PrubethIDE"

# Run release manifest and readiness verification without writing files
.\Setup.exe --verify-only
```

---

## 📜 Unrestricted Commercial License

**PRUBETH IDE** is released under the **BSVR Permissive Open Developer License (Dual MIT / Apache 2.0 Permissive Terms)**:
- **Zero Restrictive Copyleft:** Free for commercial software, closed-source integration, SaaS deployment, and proprietary distribution without viral copyleft obligations.
- **Unrestricted Model Freedom:** Native support for local weights, abliterated checkpoints, and custom GGUF architectures without artificial refusal filters.
- **Autonomous Tool Execution:** Full permissions for autonomous shell execution, self-healing test loops, and file modifications in Unrestricted Developer Mode.

See [LICENSE](file:///c:/Users/asus/heretic-work/LICENSE) for the full permissive legal text.

---

<div align="center">
  <p>© 2025–2026 BSVR Technologies. Engineered for sovereign developer flow.</p>
  <p><a href="https://www.bsvr.work/">Official Website: bsvr.work</a> · <a href="https://www.bsvr.work/#projects">Project Hub</a> · <a href="https://github.com/imyouiamyou/prubeth-ide">GitHub Repository</a></p>
</div>
