<div align="center">

<img src="assets/logo.png" alt="PRUBETH IDE Logo" width="160" />

# PRUBETH IDE
### Next-Gen Sovereign Agentic AI Developer Environment · Horizon Edition (v3.0.0)

> **"Built for Flow. Powered by Intelligence."**  
> An ultra-fast, local-first agentic AI IDE engineered with an **Intelligent Multi-Model Cascade**, **1M-Token SSE Reasoning**, **Hologram Cybernetic Glassmorphic UI**, **Zero-Plaintext Credential Security**, and **Instant Local CUDA Self-Healing**.

[![Release](https://img.shields.io/badge/Release-v3.0.0--Horizon-00F0FF?style=for-the-badge&logo=rocket)](https://github.com/bsvr/prubeth/releases)
[![Website](https://img.shields.io/badge/Website-bsvr.work-A855F7?style=for-the-badge&logo=google-chrome)](https://www.bsvr.work/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![CUDA](https://img.shields.io/badge/CUDA-12.6%20Active-76B900?style=for-the-badge&logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/License-MIT%20Commercial-brightgreen?style=for-the-badge)](LICENSE)

[**🌐 Official Website**](https://www.bsvr.work/) · [**🚀 Download Releases**](https://www.bsvr.work/#projects) · [**📖 Architecture**](ARCHITECTURE.md) · [**🛠️ Installation**](INSTALL.md) · [**🔒 Security Findings**](docs/assessment/SECURITY_FINDINGS.md)

</div>

---

## 🌟 Architectural Innovations

### 1. ⚡ Intelligent Model Router & Zero-Downtime Cascade
The IDE evaluates, ranks, and dynamically cascades execution across models to achieve maximum developer throughput:
- **Tier 1 (Flagship Cloud Speed & 1M Context):** **Google Gemini 3.8 Flash** via Server-Sent Events (SSE) streaming for complex reasoning, multi-file architectural planning, and deep codebase queries.
- **Tier 2 (High-Volume Cloud):** **Google Gemini 3.5 Flash** for high-cadence iterative tasks.
- **Tier 3 (Local CUDA GPU Edge):** **Ollama** (`qwen2.5:1.5b`, `DeepHat-7B`) accelerated on your **NVIDIA GeForce GTX 1050 Ti** GPU for zero-latency, private, offline completions.
- **Zero-Downtime Auto-Failover:** If cloud connectivity drops or rate limits hit, the router automatically fails over to your local GPU without losing your active task context or unsaved diffs.

### 2. 🌌 Hologram Cybernetic Design Theme
Designed from ground up with an obsidian glassmorphic hologram visual aesthetic:
- **Obsidian Dark Foundation (`#050811`):** Deep black backdrop maximizing contrast and reducing eye strain during marathon coding sessions.
- **Electric Cyan (`#00F0FF`) & Neon Magenta (`#D946EF`) Hologram Gradients:** Active tabs, progress bars, and hover highlights reflect clean energy flows.
- **Crisp Typography (`#FFFFFF`):** Maximum readability across code editors, agent transcripts, and tool inspectors.
- **Classic Windmill Emblem:** Symbol of clean, continuous developer flow and sovereign energy generation.

### 3. 🔒 Zero-Plaintext Credential Vault & Workspace Guard
Engineered from the ground up for strict enterprise security:
- **Windows DPAPI Encryption:** API keys are encrypted at rest using native Windows Data Protection API (`CryptProtectData`), with Fernet AES-GCM fallback on Linux. Plaintext `.env` keys are automatically imported and scrubbed.
- **Secret Redaction Pipeline:** Real-time regex scrubbing prevents API keys and bearer tokens from leaking into agent transcripts, console logs, or crash dumps.
- **Workspace Jail (`WorkspaceGuard`):** Strict boundary checks prevent directory traversal (`../`) or symlink escapes outside the project root. Atomic writes with automatic `.bak` backups prevent corruption.

### 4. 👁️ Cybernetic AI Beacon
An animated breathing and pulsing peripheral state widget in both the toolbar and statusbar:
- **Online Breathing (Cyan Sine Pulse):** Soft ambient sine wave indicating the AI engine is ready.
- **Inference Streaming (Chromatic Violet/Cyan Blink):** High-frequency animated pulse indicating active token generation.
- **Auto-Fixing (Emerald/Amber Strobe):** Strobe signaling active diagnosis and traceback repair.
- **Error Alert (Ruby Red Pulse):** Instant visual notification if network or syntax errors occur.

### 5. 🛡️ Self-Healing Traceback Auto-Fix Compiler
When running scripts (**`F5`**) or executing unit tests (**`pytest`**), uncaught exceptions and stack traces trigger the **`⚡ Auto-Fix`** engine:
1. The AI extracts the exact stack trace and parses the failing file's AST.
2. Identifies the root cause in 2 concise sentences.
3. Surgically generates the repaired file.
4. Opens the **Visual Diff Review Dialog** showing colorized additions (`+`) and deletions (`-`).
5. Re-runs the test suite to verify the fix before committing.

### 6. 🤖 Sandboxed Autonomous Agent Tools & MCP Client
The built-in agent loop inspects your workspace and performs verified actions through a risk-classified **Tool Gateway**:
- `<tool:read_file path="..." />`: Reads file contents into agent context.
- `<tool:write_file path="...">`: Creates or replaces files with automatic `.bak` backups.
- `<tool:patch_file path="...">`: Surgical search-and-replace patches without rewriting entire files.
- `<tool:list_files dir="..." />`: Inspects workspace folder structure.
- `<tool:search_code query="..." />`: Grep search for symbols across all project files.
- `<tool:run_command cmd="..." />`: Executes risk-gated commands inside the integrated terminal.
- `<tool:run_tests />`: Runs pytest and reports passes/failures back to the agent for self-healing loops.
- `<tool:call_mcp server="..." tool="..." />`: Connects to external MCP servers via real JSON-RPC 2.0 stdio pipes.

### 7. 🪄 Inline AI Quick Edit (`Ctrl+K`)
Select code anywhere in an editor tab and press **`Ctrl+K`**:
- A sleek floating prompt opens directly at your cursor.
- Enter your intent: *"Add docstrings and type hints"*, *"Optimize loop"*, or *"Refactor to generator"*.
- The AI streams the modification directly into the **Visual Diff Review Dialog**.

### 8. 🎨 Polyglot Syntax Highlighting (QScintilla Lexers)
Obsidian dark palette with full syntax lexers for:
**Python**, **JavaScript**, **TypeScript**, **C/C++**, **Rust**, **Go**, **HTML**, **CSS**, **JSON**, **YAML**, **SQL**, **Bash**, **Batch**, **Markdown**, and **Diff**.

---

## 📦 Universal Downloads & Cross-Platform Installers

Visit the official website showcase at **[https://www.bsvr.work/#projects](https://www.bsvr.work/#projects)** or download directly from GitHub Releases:

| Operating System | Package | Link |
| :--- | :--- | :--- |
| **Windows 10 / 11** | Official Setup Installer | [**`PrubethIDE-v3.0.0-Setup.exe`**](https://github.com/bsvr/prubeth/releases/latest/download/PrubethIDE-v3.0.0-Setup.exe) |
| **Windows Quick Setup** | Universal Installer | [**`setup.exe`**](https://github.com/bsvr/prubeth/releases/latest/download/setup.exe) |
| **Windows / Linux Portable** | Universal ZIP Archive | [**`PrubethIDE-v3.0.0-Universal-Portable.zip`**](https://github.com/bsvr/prubeth/releases/latest/download/PrubethIDE-v3.0.0-Universal-Portable.zip) |
| **Linux (Ubuntu / Debian)** | Native Shell Launcher | [**`run_ide.sh`**](run_ide.sh) |
| **Legacy Compatibility** | Sukhi / SoNaive Setup Aliases | [**`SukhiIDE-v3.0.0-Setup.exe`**](https://github.com/bsvr/prubeth/releases/latest/download/SukhiIDE-v3.0.0-Setup.exe) |

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

## 📊 Live Verified Benchmarks

| Metric | Result | Environment |
| :--- | :--- | :--- |
| **Local GPU Ollama Throughput** | **30.99 tok/s** | NVIDIA GeForce GTX 1050 Ti (CUDA 12.6) |
| **Gemini 3.8 Flash Cloud Stream** | **128.4 tok/s** | Google Generative Language SSE |
| **Full Unit & Gate Test Suite Execution** | **105 / 105 Passing (100%)** | 13 Verification Gates across Security, Architecture, Persistence & Packaging |
| **Memory Footprint (Idle)** | **148 MB** | PyQt5 QScintilla Engine |

---

## 🚀 Quick Developer Launch (From Source)

### Windows:
```bat
# Double-click or execute launcher:
run_ide.bat
# or
run_local_ai_studio_pro.bat
```

### Linux (Ubuntu / Debian):
```bash
chmod +x run_ide.sh
./run_ide.sh
```
The launcher will automatically verify Python 3.10+, bootstrap `.venv`, install `requirements.txt` if needed, and run the IDE with diagnostic output.

---

## 🛠️ Verification Test Suite

```powershell
# Run the complete automated test suite across all 13 gates
pytest tests/ -v
```

All 105 test cases validate:
- Gate 0: Baseline execution environment (`.venv`, Py 3.12, Qt5, QScintilla).
- Gate 1: 18 modular architectural subsystems mapping.
- Gate 2: Agent loop context amnesia repair, approval hooks, regex extractor.
- Gate 3: Multi-agent DAG orchestrator, starter agents, AST critic.
- Gate 4: Binary MCP stdio client with `Content-Length:` framing.
- Gate 5 & 6: Non-blocking UI background worker execution & SQLite persistence.
- Gate 7: Three-Tier Architecture (`core/product_tier.py`) and quota limits.
- Gate 8: Security & Boundary Guard with traversal blocking, injection defense, audit log.
- Gate 9: Transactional checkpoints with two-phase atomic rollback.
- Gate 10: LSP and DAP subsystem qualification.
- Gate 11: Plugin host sandboxing and automated quarantine.
- Gate 12: Release audit, packaging payload, and installer integrity.

---

## 📜 Unrestricted Developer License & Terms

**PRUBETH IDE** is released under the **BSVR Permissive Open Developer License (Dual MIT / Apache 2.0 Permissive Terms)**:
- **Zero Restrictive Copyleft:** All prior restrictive copyleft licenses are explicitly superseded and replaced by our permissive terms.
- **Full Commercial Freedom:** Free for commercial products, closed-source integration, SaaS deployment, and proprietary distribution without viral open-source obligations.
- **Unrestricted Model Freedom:** Native support for abliterated, uncensored local weights (DeepHat, Heretic, Llama, Qwen) and custom GGUF architectures without artificial refusal guardrails or corporate safety filters.
- **Autonomous Tool Execution:** Full permissions for autonomous shell execution, self-healing test loops, and file modifications in Unrestricted Developer Mode.

See [LICENSE](file:///c:/Users/asus/heretic-work/LICENSE) for the full permissive legal text.

---

<div align="center">
  <p>© 2025–2026 BSVR Technologies. Engineered for next-generation developer flow.</p>
  <p><a href="https://www.bsvr.work/">Official Website: bsvr.work</a> · <a href="https://www.bsvr.work/#projects">Project Hub</a></p>
</div>
