# PRUBETH IDE — Full Design Infrastructure Specification
**Version:** 1.89.0 / v1.89 (Horizon Edition)  
**Author:** BSVR & PRUBETH Horizon Autonomous Systems  
**Live Showcase:** [https://www.bsvr.work/](https://www.bsvr.work/)  
**Target Platform:** Windows 10/11 x64 (Native CUDA / Hybrid Cloud / Fully Air-Gapped)

---

## 🏛️ 1. High-Level System Architecture & Topology

PRUBETH IDE is engineered as an ultra-fast, polyglot development environment combining a reactive desktop GUI, a deterministic multi-agent autonomy loop, a zero-downtime dual-inference cascade, and local GPU acceleration with unrestricted offline inference.

```
+----------------------------------------------------------------------------------------------------+
|                                    PRUBETH IDE WORKSPACE GUI                                       |
|               (Obsidian Slate Theme · QScintilla Polyglot Lexers · 5-Zone Docking Engine)           |
+----------------------------------------------------------------------------------------------------+
        |                                       |                                    |
        v                                       v                                    v
+-------------------------------+   +-------------------------------+   +----------------------------+
|      File & Project Tree      |   |   Dedicated Settings & Mods   |   |   Blinking Sine AI Beacon  |
|  - Real-time QFileSystemModel |   |   - Top Nav Bar (10 Subsystems)|  |   - 25 FPS sin(θ) breathing|
|  - Git Status Decoration      |   |   - Pill Sub-Nav (8 Mod Panes)|   |   - Online/Streaming/AutoFix|
|  - Context-Menu Tool Actions  |   |   - Hardware Presets (GTX1050)|   |   - Hex Color State Strobe |
+-------------------------------+   +-------------------------------+   +----------------------------+
        |                                       |                                    |
        +---------------------------------------+------------------------------------+
                                                |
                                                v
+----------------------------------------------------------------------------------------------------+
|                                  INTELLIGENT ROUTER & GATEWAY                                      |
|                               (Dynamic Dynamic Priority Fallback)                                  |
+----------------------------------------------------------------------------------------------------+
       |                                |                               |                     |
       v (Tier 1)                       v (Tier 2)                      v (Tier 3)            v (Tier 4)
+-----------------------+     +-----------------------+     +-----------------------+     +----------+
|  Google Gemini 3.8    |     |  Google Gemini 3.5    |     | Local CUDA GPU Ollama |     | Custom   |
|  Flash (1M Context)   |     |  Flash (Fast Cloud)   |     | (RedSage-8B, DeepSeek)|     | Gateways |
+-----------------------+     +-----------------------+     +-----------------------+     +----------+
       |                                |                               |                     |
       +--------------------------------+-------------------------------+---------------------+
                                                |
                                                v
+----------------------------------------------------------------------------------------------------+
|                               AUTONOMOUS MULTI-AGENT DAG ENGINE                                    |
|              Planner  ──>  Code Architect  ──>  Test Fixer  ──>  AST Critic Engine                 |
|                                                                                                    |
|   10-Tool Native Protocol:                                                                         |
|   • <tool:read_file>         • <tool:write_file>        • <tool:patch_file>   • <tool:list_files>      |
|   • <tool:search_code>       • <tool:run_command>       • <tool:run_tests>    • <tool:call_mcp>        |
|   • <tool:create_checkpoint> • <tool:rollback_checkpoint>                                          |
+----------------------------------------------------------------------------------------------------+
        |                                       |                                    |
        v                                       v                                    v
+-------------------------------+   +-------------------------------+   +----------------------------+
|    AST Traceback Compiler     |   |   Transactional Checkpoints   |   |  Security & Jail Guard     |
|  - Intercepts stderr frames   |   |   - 2-Phase Shadow Commit     |   |  - DPAPI/Fernet Secret Box |
|  - Surgical Markdown patch    |   |   - Delta File Backups (.bak) |   |  - Path Traversal Blocker  |
|  - Visual Side-by-Side Diff   |   |   - Single-Click Undo/Restore |   |  - API Key Masking/Redactor|
+-------------------------------+   +-------------------------------+   +----------------------------+
```

---

## 🎨 2. Layer 1: Presentation & Design System Infrastructure

### 2.1 Design Tokens & Palette

The user interface uses an **Obsidian Slate Glassmorphism** design token system engineered for high contrast, minimal eye strain, and cybernetic aesthetic precision:

| Token Name | Hex Code | Visual Role |
| :--- | :--- | :--- |
| `--bg-base` | `#12141a` | Deep obsidian backdrop of the entire application |
| `--bg-surface` | `#181c25` | Card surface, docking panels, dialog shells |
| `--bg-card-alt` | `#1e222d` | Elevated inner containers, code blocks, active hover |
| `--border-subtle` | `#282d3b` | 1px clean slate dividers and card borders |
| `--border-focus` | `#3b82f6` | Active input outline, selected tab highlight |
| `--accent-cyan` | `#00f0ff` | Electric primary accent, AI pulse beacon, live stream indicators |
| `--accent-magenta`| `#d946ef`| Secondary gradient, branding accents, agent highlights |
| `--accent-emerald`| `#10b981`| Success states, active green badges, diff additions |
| `--accent-coral`  | `#ef4444`| Error states, security alerts, diff deletions |
| `--accent-amber`  | `#f59e0b`| Warnings, rate limit triggers, autofix stroboscopic alerts |
| `--text-primary`  | `#f1f5f9`| Crisp white header text and primary titles |
| `--text-secondary`| `#94a3b8`| Subtitles, helper text, timestamps, parameter badges |
| `--text-muted`    | `#64748b`| Disabled text, placeholder strings, border lines |

### 2.2 Typography Stack
- **Interface Font:** `Segoe UI`, `Inter`, `-apple-system`, `sans-serif` (smoothed with anti-aliasing rendering hints).
- **Code & Monospace Font:** `Cascadia Code`, `Consolas`, `JetBrains Mono`, `monospace` (ligature support enabled, tab width 4).
- **Font Scale Hierarchy:**
  - Header 1 (Dialog & View Titles): `18px`, Weight 700 / Bold
  - Header 2 (Section Groupings): `13px`, Weight 700 / Semi-Bold
  - Body Text (Inputs, Labels, Buttons): `11px - 12px`, Weight 500 / Regular
  - Badges & Micro-Labels: `9px - 10px`, Weight 700 / Bold uppercase tracking `0.5px`
  - Code Editor & Terminal: `12px`, Cascadia Code regular

### 2.3 5-Zone Docking Workspace Architecture
The main window implements a five-zone layout using native Qt dock widgets:
1. **Zone 1 (Left Dock): File Explorer & Tree**
   - High-performance `QFileSystemModel` with lazy directory loading.
   - Real-time Git status decoration (modified, untracked, ignored).
   - Context-menu shortcuts for autonomous agent targeting (`Explain`, `Refactor`, `Generate Tests`).
2. **Zone 2 (Center Canvas): Multi-Tab Polyglot Code Editor**
   - Built on QScintilla / custom code editor with syntax highlighting for Python, C/C++, Rust, JavaScript, HTML/CSS, JSON, YAML, SQL, Shell.
   - Code folding, line numbering, bracket auto-matching, and visual margin glyphs for breakpoints and diff changes.
3. **Zone 3 (Right Dock): Autonomous Agent Autopilot & Chat**
   - Real-time markdown streaming view with syntax-highlighted code blocks.
   - Quick-action buttons (`Analyze Workspace`, `Auto-Fix Bug`, `Run Test Suite`, `Create Checkpoint`).
   - Token counter, elapsed latency counter, and model badge indicator.
4. **Zone 4 (Bottom Dock): Multi-Tab Terminal & Execution Engine**
   - Polyglot execution console (PowerShell, Bash, Command Prompt).
   - Test runner dashboard (`pytest` live output parsing).
   - AST traceback interceptor and visual diff inspection tab.
5. **Zone 5 (Status & Beacon Bar): Real-Time Telemetry**
   - Cybernetic sine breathing beacon.
   - Hardware telemetry (GPU VRAM usage, CPU RAM usage).
   - Active Model Indicator with instantaneous failover tooltip.
   - Current Git branch and dirty state badge.

### 2.4 Dedicated Settings & Subsystem Mod Control Center
Accessible via `Ctrl+,` or the gear icon, the Settings Control Center (`ui/settings_dialog.py`) provides centralized management for all IDE subsystems:

- **Level 1 Top Navigation Bar (10 Primary Subsystems):**
  1. `Agents`: Autonomy loop limits, execution depth, timeout intervals.
  2. `Providers`: Cloud and gateway providers (Gemini, Anthropic, OpenAI, Groq, Mistral, Ollama).
  3. `Gateway`: Port configuration, reverse proxies, bearer tokens, headers.
  4. `Routing`: Priority cascades, fallback triggers, temperature and top-p settings.
  5. `Local Models`: Unrestricted offline LLM management, CUDA GPU offload layers, VRAM budgeting.
  6. `Editor Mods`: Font rendering, ligatures, indentation, auto-closing, mini-map, Myers diff engine.
  7. `Terminal`: Shell selection (PowerShell/CMD/WSL), buffer length, ANSI color palette.
  8. `Sync & Backup`: Two-phase checkpoints, automatic snapshots, Git synchronization.
  9. `Plugins`: MCP servers, third-party hooks, language server protocol (LSP) daemons.
  10. `Observability`: Logging level, token telemetry, latency tracking, exportable JSON audit trails.

- **Level 2 Sub-Nav Pill Bar (8 Mod Panes):**
  - `GENERAL`, `ALLOWANCES`, `NETWORK AND SHARING`, `MODELS`, `PRIVACY`, `OBSERVABILITY`, `SYNC AND BACKUP`, `ABOUT`.

- **Component Primitives:**
  - `SettingsCard`: Rounded glass containers (`#181c25`) with subtle border (`#282d3b`) encapsulating related options.
  - `PillBadge`: High-contrast capsule pills displaying active routing states, model types, or tier status.
  - `SegmentedPillSwitch`: Toggle controls switching between operational modes (e.g., `Model Search` vs `Search APIs`).
  - `Hardware Quick Presets`:
    - `Gaming Laptop (GTX 1050 Ti 4GB)`: Optimizes for 4GB VRAM (33 layers offloaded, 8k context).
    - `Cybersecurity Research Lab`: 100% offline, uncensored, zero cloud telemetry.
    - `Maximum Privacy Air-Gapped`: Disables all outbound sockets.
    - `Frontier Cloud 1M`: Routes all large context queries to Gemini 3.8 Flash.

### 2.5 Cybernetic AI Sine Breathing Beacon
The beacon provides non-distracting peripheral awareness of the AI's internal cognitive state:
$$\text{glow} = 0.65 + 0.35 \cdot \sin(\theta)$$
- Updates every $40\text{ ms}$ ($25\text{ FPS}$) using `QTimer`.
- State transitions:
  - `ONLINE`: Gentle cyan wave (`#00f0ff`).
  - `STREAMING`: Chromatic alternating pulse between electric violet (`#a855f7`) and cyan (`#00f0ff`).
  - `AUTOFIX`: Stroboscopic emerald (`#10b981`) and amber (`#f59e0b`).
  - `ALERT`: Steady ruby red (`#ef4444`).

---

## ⚙️ 3. Layer 2: Core Engine & Policy Infrastructure

### 3.1 Intelligent Router & Zero-Downtime Cascade
The router (`core/intelligent_router.py`) handles dynamic routing across local and remote inference targets:

```
[User Prompt / Agent Request]
              |
              v
     [Health & Latency Check]
              |
     +--------+--------+
     |                 |
(Online)           (Offline / Rate Limited)
     |                 |
     v                 v
[Tier 1: Gemini 3.8]  [Tier 3: Local CUDA Ollama]
     |                 |
(On HTTP 429/Timeout)  |
     v                 |
[Tier 2: Gemini 3.5]   |
     |                 |
     +--------+--------+
              |
              v
[Streaming Token Response Engine]
```

### 3.2 Model Registry
Defined in `core/model_registry.py`, the registry tracks models across tiers with capability flags:
- `redsage-8b:latest`: Local CUDA (4GB VRAM footprint), Q3_K_S quant, 8k context, zero network traffic.
- `deepseek-r1:latest`: Local CUDA reasoning model.
- `gemini-3.8-flash`: Cloud Tier 1, 1,000,000 token context window, multimodal vision support.
- `gemini-3.5-flash`: Cloud Tier 2, low latency code generation.
- `claude-3-7-sonnet`: Frontier cloud code architecture.

### 3.3 Security & Boundary Guard Engine
- **Secret Vault:** Windows Data Protection API (DPAPI) via `CryptProtectData` with AES-256 Fernet fallback for cross-platform portability.
- **Log Masking:** Automatically redacts `AIza...`, `sk-...`, `ghp_...`, and bearer tokens from logs, UI displays, and agent traces.
- **Path Jail:** Enforces workspace root containment; rejects path traversal attempts (`../`, `..\\`) and system directory access (`C:\Windows`, `/etc`).

---

## 🤖 4. Layer 3: Autonomous Multi-Agent & Execution Infrastructure

### 4.1 DAG Multi-Agent Orchestration
The multi-agent loop coordinates four distinct sub-agent roles:
1. **Planner Agent:** Deconstructs user objectives into actionable step sequences and tool invocations.
2. **Code Architect Agent:** Synthesizes code, manages imports, and performs surgical search-and-replace patches.
3. **Test Fixer Agent:** Executes test suites, analyzes failures, and generates targeted regression patches.
4. **AST Critic Agent:** Validates syntax validity via Python `ast.parse` and style invariants before disk writes.

### 4.2 Native 10-Tool Agent Protocol
The autonomy loop communicates with the host environment using an XML-tagged tool protocol:

```xml
<!-- File Operations -->
<tool:read_file path="src/main.py" />
<tool:write_file path="src/main.py">contents</tool:write_file>
<tool:patch_file path="src/main.py">
  <search>def old():</search>
  <replace>def new():</replace>
</tool:patch_file>
<tool:list_files dir="." />
<tool:search_code query="class IntelligentRouter" />

<!-- Execution & Verification -->
<tool:run_command cmd="git status" />
<tool:run_tests />
<tool:call_mcp server="filesystem" tool="list_directory" />

<!-- Safety & Recovery -->
<tool:create_checkpoint description="Before refactor" />
<tool:rollback_checkpoint id="chk_20261011_01" />
```

### 4.3 Self-Healing Traceback Compiler
When runtime exceptions occur:
1. Intercepts standard error stream from `QProcess`.
2. Extracts traceback frames, file paths, and line numbers.
3. Packages the traceback with surrounding code context into an emergency fix prompt.
4. Synthesizes a patch and presents a side-by-side visual diff for user confirmation.
5. Re-executes the command automatically upon applying the fix.

---

## 🚀 5. Layer 4: Dual Inference Pipeline & Local Offload

### 5.1 Local GPU Pipeline (CUDA 12.6)
For full privacy, air-gapped environments, and zero-token-cost operation:
- **Local Runtime:** Ollama backend serving GGUF models on localhost (`http://127.0.0.1:11434/api/generate`).
- **Hardware Profile:** Optimized for 4GB VRAM GPUs (e.g., NVIDIA GeForce GTX 1050 Ti):
  - Model: `redsage-8b:latest` (Q3_K_S, 3.77 GB).
  - VRAM Offload: 33 GPU layers placed in VRAM; remainder in system RAM.
  - Context Window: 8,192 tokens.
  - Zero outbound telemetry or external API calls.

### 5.2 Frontier Cloud Fallback Cascade
- Automatic seamless switch to cloud endpoints when large context windows (>8k tokens) or multi-modal analysis are required.
- SSE (Server-Sent Events) streaming with live token-by-token UI updates.

---

## 🔌 6. Layer 5: Tool & Protocol Gateway Infrastructure

### 6.1 Model Context Protocol (MCP) Client
- Implements standard MCP client communication over `stdio`.
- JSON-RPC 2.0 protocol with `Content-Length:` header framing.
- Auto-discovers tool schemas and binds them dynamically into the agent's tool namespace.

### 6.2 Process Execution & Terminal Gateway
- Process execution managed via non-blocking `QProcess` instances.
- Workspace sandboxing with command whitelisting/blacklisting.
- Captures standard output and standard error with real-time ANSI escape code colorization.

---

## 💾 7. Layer 6: State Storage, Persistence & Packaging Layout

### 7.1 Local Persistence Schema
User state and settings are stored locally under `~/.local_ai_studio_pro/`:

```
~/.local_ai_studio_pro/
├── accounts.json          # Provider configurations & active account profiles
├── extensions.json        # Installed plugins, MCP servers, and tool integrations
├── mod_settings.json      # IDE settings, theme tokens, and hardware presets
├── checkpoints/           # Transactional rollback snapshots and shadow diffs
│   ├── manifest.json
│   └── 20261011_072000/
└── logs/                  # Audit trails and execution logs
    └── studio.log
```

### 7.2 Packaging Pipeline & Self-Bootstrapping Launchers
- **Build Pipeline (`build_setup_exe.py`):** Bundles source code, dependencies, and assets into `app_payload.zip`, compiling an embedded installer via PyInstaller.
- **`setup.exe`:** Extracts the payload to `%LOCALAPPDATA%\Programs\PrubethIDE`, validates Python and Qt runtime prerequisites, and registers desktop shortcuts.
- **`run_ide.bat`:** Self-healing launcher for source execution; automatically provisions virtual environments and installs dependencies from `requirements.txt` if absent.
- **`PrubethIDE.bat`:** Production launcher with built-in runtime diagnostic checks and GUI error notifications via `mshta`.

---

## 📊 Summary Architecture Matrix

| Dimension | Specification |
| :--- | :--- |
| **GUI Framework** | PyQt6 / QScintilla (Hardware-accelerated rendering) |
| **Design Language** | Obsidian Slate Glassmorphic (`#12141a`, `#181c25`, `#00f0ff`) |
| **Local Inference** | Ollama CUDA 12.6 (`redsage-8b:latest`, Q3_K_S) |
| **Cloud Inference** | Google Gemini 3.8 Flash (1M tokens), Claude 3.7 Sonnet |
| **Multi-Agent Engine** | 4-Role DAG (Planner, Architect, Test Fixer, AST Critic) |
| **Agent Tool Protocol** | 10 XML Tool Tags with 2-Phase Transactional Rollback |
| **Secret Encryption** | Windows DPAPI with AES-256 Fernet fallback |
| **Test Suite Coverage** | 303/303 pytest tests passing (100%) across 22 subsystems (Evolution: 107 Gate 1 Baseline -> 287 Gate 10 Full-Stack -> 301 Gate 12 Packaging -> 303 v1.12.0 Hardened Security Release) |
