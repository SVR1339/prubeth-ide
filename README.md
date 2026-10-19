<div align="center">

<img src="assets/brand_banner.png" alt="PRUBETH IDE — Horizon Edition" width="960" />

<br/><br/>

<img src="assets/logo.png" alt="PRUBETH IDE Blooming Flower Logo" width="130" />

# PRUBETH IDE
### Multi-Model AI Developer Workstation · Horizon Edition (v1.91.0)

> *"Bloom, ideas unfolding."*  
> PRUBETH IDE brings high-speed polyglot code editing, multi-model AI routing, autonomous self-healing agent workflows, and verified systems reliability into one unified desktop environment.

<br/>

[![Release](https://img.shields.io/badge/Release-v1.91.0--Horizon-7059E2?style=for-the-badge&logo=rocket)](https://github.com/imyouiamyou/prubeth-ide/releases/tag/v1.91)
[![Tests Passing](https://img.shields.io/badge/Tests-303%20%2F%20303%20Passed-70D6A0?style=for-the-badge&logo=pytest)](FINAL_RELEASE_VERIFICATION.md)
[![Security Verification](https://img.shields.io/badge/Security-Ed25519%20Signed%20%26%20TLS-00F0FF?style=for-the-badge&logo=shield)](installer/release_config.py)
[![Platforms](https://img.shields.io/badge/Platform-Windows%2010%2F11%20%7C%20Linux%20%7C%20macOS-1D2028?style=for-the-badge&logo=windows)](INSTALL.md)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=for-the-badge&logo=python)](https://python.org)
[![CUDA](https://img.shields.io/badge/CUDA-12.6%20Accelerated-76B900?style=for-the-badge&logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/License-MIT%20Commercial-F7A07E?style=for-the-badge)](LICENSE)

<br/>

<!-- ================================================================= -->
<!-- VIP ONE-CLICK DOWNLOAD BUTTONS                                    -->
<!-- ================================================================= -->

### 🚀 Direct Release Downloads (v1.91.0)

<p align="center">
  <a href="https://github.com/imyouiamyou/prubeth-ide/releases/download/v1.91/PrubethIDE-v1.91.0-Setup.exe">
    <img src="https://img.shields.io/badge/⬇️_DOWNLOAD_SETUP.EXE-Windows_Installer_(240_MB)-7059E2?style=for-the-badge&logo=windows&logoColor=white" alt="Download Windows Setup.exe" height="42" />
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/imyouiamyou/prubeth-ide/releases/download/v1.91/Prubeth-Payload-1.91.0-windows-x64.zip">
    <img src="https://img.shields.io/badge/📦_DOWNLOAD_PORTABLE_ZIP-All--in--One_Folder_(3.0_MB)-4ECDC4?style=for-the-badge&logo=files&logoColor=white" alt="Download Portable Zip" height="42" />
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/imyouiamyou/prubeth-ide/releases/tag/v1.91">
    <img src="https://img.shields.io/badge/🛡️_VERIFY_RELEASE-Signatures_&_SBOM-F7A07E?style=for-the-badge&logo=github&logoColor=white" alt="View Release Assets" height="42" />
  </a>
</p>

[**🌐 Official Website**](https://www.bsvr.work/) · [**🚀 GitHub Releases**](https://github.com/imyouiamyou/prubeth-ide/releases/tag/v1.91) · [**📖 Architecture**](ARCHITECTURE.md) · [**🗺️ Architecture Map**](docs/ARCHITECTURE_MAP.md) · [**⚖️ Comparison vs Reference IDEs**](docs/REFERENCE_IDE_COMPARISON.md) · [**🛠️ Installation Manual**](INSTALL.md) · [**🧩 Extensions Guide**](DEVELOPER_EXTENSIONS_GUIDE.md)

</div>

---

## 📑 Table of Contents

- [1. Product Overview & Identity](#1-product-overview--identity)
- [2. Main Interface & Visual Showcase](#2-main-interface--visual-showcase)
- [3. Why PRUBETH IDE Exists](#3-why-prubeth-ide-exists)
- [4. Core Capabilities & Key Features](#4-core-capabilities--key-features)
- [5. Feature Implementation Matrix](#5-feature-implementation-matrix)
- [6. Screenshots & Interface Tour](#6-screenshots--interface-tour)
- [7. Installation & VIP Download Center](#7-installation--vip-download-center)
- [8. First-Launch Instructions](#8-first-launch-instructions)
- [9. Model & AI Provider Configuration](#9-model--ai-provider-configuration)
- [10. Typical Workflows & Agent Execution](#10-typical-workflows--agent-execution)
- [11. Subsystem Architecture Overview](#11-subsystem-architecture-overview)
- [12. Security, Integrity & Cryptographic Privacy](#12-security-integrity--cryptographic-privacy)
- [13. Hardware & System Requirements](#13-hardware--system-requirements)
- [14. Testing, Chaos & Quality Assurance](#14-testing-chaos--quality-assurance)
- [15. Build & Packaging Pipeline](#15-build--packaging-pipeline)
- [16. Official Downloadable Releases](#16-official-downloadable-releases)
- [17. Engineering Roadmap](#17-engineering-roadmap)
- [18. Known Limitations & Tested Boundaries](#18-known-limitations--tested-boundaries)
- [19. Contribution Guidelines](#19-contribution-guidelines)
- [20. License & Third-Party Notices](#20-license--third-party-notices)
- [21. Support & Vulnerability Disclosure](#21-support--vulnerability-disclosure)
- [22. Acknowledgments](#22-acknowledgments)

---

## 1. Product Overview & Identity

**PRUBETH IDE** is an AI-assisted development workstation designed to bring code editing, local and cloud AI model orchestration, autonomous agent execution, and systems reliability engineering into one cohesive desktop application.

Unlike generic code editors that bolt a chat modal onto an external webview, PRUBETH IDE integrates language lexers, AST analysis, process execution supervision, hardware-aware model routing, and transactional rollback mechanisms into a single native process.

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | PRUBETH IDE (Horizon Edition) |
| **Current Release** | v1.91.0 (Git Tag: `v1.91` / `v1.91.0`) |
| **Primary Platform** | Windows 10 & 11 (64-bit x64 native) |
| **Cross-Platform Support** | Linux (Ubuntu, Debian, Fedora, Arch) & macOS (Apple Silicon / Intel) via source runtime |
| **UI Framework** | PyQt5 / Qt 5.15 / QScintilla 2.14.1 with Native Dark Obsidian Design System |
| **Supported Runtimes** | Python 3.10, 3.11, 3.12, 3.13 |
| **Hardware Acceleration** | NVIDIA CUDA 12.x, DirectML, Apple Metal (MPS), CPU Fallback |
| **License** | Permissive Open Developer License (Dual MIT / Apache 2.0 terms) |

---

## 2. Main Interface & Visual Showcase

The PRUBETH IDE interface is designed around an **Obsidian Glassmorphic** theme optimized for high-cadence development sessions:

<p align="center">
  <img src="assets/screenshot_workspace.png" alt="PRUBETH IDE Main Workspace Interface" width="960" />
  <br/>
  <em>PRUBETH IDE Workspace: QScintilla polyglot editor, active project file tree, multi-root navigation, integrated run output/test tabs, and autonomous AI Agent Copilot with live VRAM and model telemetry.</em>
</p>

---

## 3. Why PRUBETH IDE Exists

Modern developers face three major friction points with current AI tooling:

1. **Vendor Lock-In and Cloud Downtime:** Cloud-only AI tools stop working when offline, during network partition events, or when cloud provider rate limits trigger. PRUBETH IDE features an **Intelligent 3-Tier Model Router** that cascades seamlessly to local GPU Ollama models without losing workspace state.
2. **Context Amnesia and Tool Hallucination:** Chat plugins rarely understand project file hierarchies, running processes, or test suites. PRUBETH IDE equips its built-in agent with verified local tools (`read_file`, `write_file`, `patch_file`, `run_tests`, `run_command`, `search_code`) operating inside a secure workspace jail.
3. **Fragile Process Lifecycles:** IDE crashes during heavy builds or memory-intensive agent loops cause lost work. PRUBETH IDE introduces an **Out-of-Process Crash Supervisor** and **Transactional State Checkpoints** to ensure zero data loss.

---

## 4. Core Capabilities & Key Features

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRUBETH IDE ARCHITECTURE                        │
│            (Obsidian Dark Foundation · Cybernetic AI Beacon)           │
├───────────────────────────────────┬────────────────────────────────────┤
│         EDITOR & LANGUAGE         │         AGENT & INFERENCE          │
│   • QScintilla Polyglot Lexers    │   • Intelligent Model Cascade      │
│   • Multi-Root Workspace Guard    │   • Horizon Context Engine         │
│   • LSP Client & DAP Debugger     │   • Autonomous Tool Dispatcher     │
├───────────────────────────────────┴────────────────────────────────────┤
│                       RELIABILITY & PLATFORM                           │
│   • Out-of-Process Crash Supervisor (`core/crash_supervisor.py`)       │
│   • PRINCE2 7 Reliability Assurance (`core/reliability_engine.py`)     │
│   • Universal Polyglot Engine (`core/polyglot_assurance_engine.py`)    │
│   • Asymmetric Ed25519 Cryptographic Verification (`installer/`)       │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. ⚡ Intelligent Model Router & Zero-Downtime Cascade
- **Tier 1 (Flagship Cloud Inference):** Google Gemini 3.8 Flash via Server-Sent Events (SSE) streaming for complex reasoning, architectural refactoring, and multi-file code generation.
- **Tier 2 (High-Volume Cloud):** Google Gemini 3.5 Flash for rapid iterative tasks.
- **Tier 3 (Local CUDA GPU Edge):** Ollama (`qwen2.5:1.5b`, `DeepHat-7B`, custom GGUFs) accelerated on local NVIDIA GeForce GTX 1050 Ti or RTX hardware for private, zero-latency completions.
- **Zero-Downtime Auto-Failover:** If network connectivity drops or quota triggers, the router automatically fails over to your local GPU without losing editor buffers or conversation history.

### 2. 🛡️ Self-Healing Traceback Auto-Fix Engine
When running scripts (**`F5`**) or executing test suites (**`pytest`**), unhandled exceptions trigger the **`⚡ Auto-Fix`** engine:
1. Extracts the exact traceback and parses the AST of affected files.
2. Surgically produces a patch without hallucinating untouched code.
3. Opens the **Visual Diff Review Dialog** showing colorized additions and deletions.
4. Automatically re-runs tests to verify the fix before saving to disk.

### 3. 🤖 Sandboxed Autonomous Agent Tools
The built-in agent loop operates through a risk-gated Tool Gateway:
- `read_file`: Inspects file contents with workspace boundary enforcement.
- `write_file`: Atomic file creation with automatic `.bak` backups.
- `patch_file`: Surgical search-and-replace edits.
- `search_code`: Workspace-wide grep for symbols and definitions.
- `run_command`: Sandboxed command execution inside the integrated terminal.
- `run_tests`: Automated test runner execution with feedback loop.

### 4. 🔒 Zero-Plaintext Credential Vault
- **Windows DPAPI Encryption:** API keys are encrypted at rest using native Windows Data Protection API (`CryptProtectData`), with Fernet AES-GCM on Linux/macOS. Plaintext `.env` keys are automatically imported and scrubbed.
- **Secret Redaction Pipeline:** Real-time regex scrubbing prevents credentials and bearer tokens from leaking into agent transcripts, console logs, or crash dumps.
- **Workspace Jail (`WorkspaceGuard`):** Strict boundary checks prevent directory traversal (`../`) or symlink escapes outside the project root.

---

## 5. Feature Implementation Matrix

| Subsystem | Verified Capability | Test Coverage | Status |
| :--- | :--- | :---: | :---: |
| **Code Editor** | QScintilla polyglot lexers (25 languages), line folding, multi-cursor | 16 tests | ✅ Production |
| **Model Router** | Gemini SSE cloud streaming, Ollama local CUDA failover, key rotation | 24 tests | ✅ Production |
| **Agent Copilot** | Autonomous tool dispatch, approval gates, auto-repair loops | 32 tests | ✅ Production |
| **Workspace Guard** | Directory traversal jail, atomic writes, automatic `.bak` rollbacks | 18 tests | ✅ Production |
| **Crash Supervisor** | Out-of-process watchdog, exit code translation, bounded restarts | 15 tests | ✅ Production |
| **Reliability Engine** | 10 workload test profiles, chaos injection, memory telemetry | 54 tests | ✅ Production |
| **Polyglot Engine** | Multi-language toolchain discovery, sanitized runtime sandboxes | 42 tests | ✅ Production |
| **Credential Vault** | Windows DPAPI / Fernet AES-GCM encryption, secret log scrubber | 14 tests | ✅ Production |
| **Installer & Releases** | Ed25519 asymmetric verification, strict TLS, resume support | 22 tests | ✅ Production |
| **Full Test Suite** | Ground-truth meta-tests, zero-skip CI validation | **303 / 303** | ✅ 100% Passed |

---

## 6. Screenshots & Interface Tour

### Autonomous Agent Allowances & Mod Hub
The Mod Hub provides deep control over agent autonomy, abliterated vector adjustments, and local hardware allocation:

<p align="center">
  <img src="assets/screenshot_settings.png" alt="PRUBETH IDE Mod Hub & Agent Allowances" width="960" />
  <br/>
  <em>Mod Hub: Autonomous agent allowances, shell command execution toggles, multi-file write permissions, self-healing loop configuration, and hardware performance presets.</em>
</p>

---

## 7. Installation & VIP Download Center

### 🎯 Which File Should I Download?

| Asset | File Type | Size | Recommended For | Direct Download Link |
| :--- | :--- | :---: | :--- | :--- |
| 🚀 **`PrubethIDE-v1.91.0-Setup.exe`** | **Windows Full Desktop Installer** | **~240 MB** | **All Windows 10/11 users.** Automated installation wizard with Desktop shortcut, Start Menu registration, and uninstaller. | [**⬇️ Download Setup**](https://github.com/imyouiamyou/prubeth-ide/releases/download/v1.91/PrubethIDE-v1.91.0-Setup.exe) |
| 📦 **`Prubeth-Payload-1.91.0-windows-x64.zip`** | **All-in-One Portable Archive** | **~3.0 MB** | **Users who want a ready-to-run folder.** Extract anywhere, double-click `run_local_ai_studio_pro.bat`, zero installation required. | [**⬇️ Download Portable ZIP**](https://github.com/imyouiamyou/prubeth-ide/releases/download/v1.91/Prubeth-Payload-1.91.0-windows-x64.zip) |
| 🪟 **`Prubeth-Offline-Setup-1.91.0.exe`** | **Offline Standalone Installer** | **~48 MB** | Fully air-gapped standalone installer with zero internet dependencies. | [**⬇️ Download Offline Setup**](https://github.com/imyouiamyou/prubeth-ide/releases/download/v1.91/Prubeth-Offline-Setup-1.91.0.exe) |
| 🌐 **`Prubeth-Setup-1.91.0.exe`** | **Online Bootstrap Installer** | **~45 MB** | Lightweight installer that verifies and streams the latest verified payload. | [**⬇️ Download Online Setup**](https://github.com/imyouiamyou/prubeth-ide/releases/download/v1.91/Prubeth-Setup-1.91.0.exe) |
| 🛡️ **`Prubeth-Manifest-1.91.0.sig`** + **`.json`** | **Cryptographic Signatures** | **< 1 KB** | **Security engineers & release verification.** Ed25519 signature receipts. (Not needed for standard IDE usage). | [**View Release Assets**](https://github.com/imyouiamyou/prubeth-ide/releases/tag/v1.91) |

---

### Instant One-Line Installation

#### 🪟 Windows 10 / 11 (PowerShell One-Liner)
Run PowerShell as Administrator or regular user:
```powershell
irm https://raw.githubusercontent.com/imyouiamyou/prubeth-ide/master/install.ps1 | iex
```

#### 🐧 Linux & 🍎 macOS (Terminal One-Liner)
Run in bash or zsh:
```bash
curl -fsSL https://raw.githubusercontent.com/imyouiamyou/prubeth-ide/master/install.sh | bash
```

---

## 8. First-Launch Instructions

### Launching on Windows
1. **Installed Edition:** Double-click the **PRUBETH IDE** desktop icon or launch from Start Menu.
2. **Portable Edition:** Extract `Prubeth-Payload-1.91.0-windows-x64.zip` and double-click `run_local_ai_studio_pro.bat`.
3. **Developer / Source Launch:**
   ```powershell
   git clone https://github.com/imyouiamyou/prubeth-ide.git
   cd prubeth-ide
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   python local_ai_studio_pro.py
   ```

---

## 9. Model & AI Provider Configuration

PRUBETH IDE supports both local offline LLMs and cloud APIs through its settings dialog or `~/.local_ai_studio_pro/settings.json`:

### 1. Local Models via Ollama (Zero Cloud Dependency)
Ensure Ollama is installed and running (`ollama serve`). Pull your preferred model:
```bash
ollama run qwen2.5:1.5b
# Or larger models for workstations with 8GB+ VRAM:
ollama run deepseek-coder:6.7b
```
PRUBETH IDE automatically discovers active Ollama models on `http://127.0.0.1:11434` and provisions them as Tier 3 local fallbacks.

### 2. Cloud AI Providers
Configure your API keys in the IDE Settings dialog (stored securely via DPAPI / encrypted vault):
- **Google Gemini:** `GEMINI_API_KEY` (Gemini 3.8 Flash, Gemini 3.5 Flash)
- **OpenAI:** `OPENAI_API_KEY` (GPT-4o, GPT-4o-mini)
- **Anthropic:** `ANTHROPIC_API_KEY` (Claude 3.5 Sonnet)
- **OpenRouter / Mistral:** Custom base URLs and endpoint keys supported.

---

## 10. Typical Workflows & Agent Execution

### Workflow 1: Inline AI Code Transformation (`Ctrl+K`)
1. Open any file in the editor.
2. Highlight a function or block of code.
3. Press `Ctrl+K` to invoke the floating inline prompt bar.
4. Enter your instruction (e.g., *"Convert this synchronous loop into an async generator with retry logic"*).
5. Review the side-by-side visual diff and click **Accept** (`Enter`) or **Reject** (`Esc`).

### Workflow 2: Autonomous Bug Investigation & Auto-Fix
1. Press `F5` to execute the active file, or run tests via the bottom tab.
2. If an exception occurs, click **`⚡ Auto-Fix`** in the Run Output panel.
3. The Autonomous Agent parses the traceback, inspects related files, creates an atomic `.bak` backup, applies the fix, and re-executes tests to verify resolution.

---

## 11. Subsystem Architecture Overview

PRUBETH IDE's architecture decouples UI rendering, language services, agent reasoning, and process supervision:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                            │
│    PyQt5 / QScintilla 2.14.1 · Obsidian Dark Design · Mod Hub GUI      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Events & Commands
┌───────────────────────────────────▼────────────────────────────────────┐
│                       CORE APPLICATION ENGINE                          │
│  • Universal Inventory (`universal_inventory.py`)                     │
│  • Capability Gap Engine (`capability_gap_engine.py`)                  │
│  • Crash Supervisor (`crash_supervisor.py`)                            │
│  • Reliability Engine (`reliability_engine.py`)                        │
└───────────────┬───────────────────┬───────────────────┬────────────────┘
                │                   │                   │
┌───────────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│   LANGUAGE SERVICES    │ │  AGENT DISPATCH │ │  MODEL ROUTER   │
│ • QScintilla Lexers    │ │ • read_file     │ │ • Tier 1 Gemini │
│ • Polyglot Runtime     │ │ • write_file    │ │ • Tier 2 Cloud  │
│ • 25 Languages         │ │ • patch_file    │ │ • Tier 3 Ollama │
│ • AST Code Analysis    │ │ • run_command   │ │ • Auto-Failover │
└────────────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 12. Security, Integrity & Cryptographic Privacy

PRUBETH IDE v1.12.0 incorporates comprehensive security controls:

1. **Strict TLS Certificate Verification:** Downloads in `installer/download_engine.py` mandate `ssl.create_default_context()`. Insecure context overrides and `CERT_NONE` are eliminated.
2. **Asymmetric Ed25519 Release Manifest Signing:** Release manifests are cryptographically verified using Ed25519 public key pinning:
   ```
   Trusted Public Verification Key:
   4290a6bf8ef8045d53657eddfcc7839bbf08b3ee2ecc83eedc64d32f54d63129
   ```
   The private signing key (`release_signing.key`) is strictly isolated outside the public repository and is never embedded in compiled binaries.
3. **Download Pipeline Unification:** All downloads verify signed release manifests, SHA-256 digests, file sizes, and archive path safety before decompression.
4. **Zero Plaintext Storage:** API tokens are encrypted using Windows DPAPI (`CryptProtectData`) or Fernet AES-GCM.
5. **Real-Time Secret Scrubbing:** Transcripts, logs, and error outputs are sanitized to remove API tokens.

---

## 13. Hardware & System Requirements

| Resource | Minimum | Recommended | GPU-Accelerated Workstation |
| :--- | :--- | :--- | :--- |
| **OS** | Windows 10 (64-bit), Ubuntu 20.04+, macOS 12+ | Windows 11 (64-bit) | Windows 11 (64-bit) |
| **CPU** | Dual-core x86_64 / Apple Silicon | Quad-core Intel i5 / Ryzen 5 | 8-core Intel i7 / Ryzen 7 |
| **RAM** | 4 GB | 8 GB | 16 GB+ |
| **Disk Space** | 500 MB (Core IDE) | 2 GB | 10 GB+ (with local LLM weights) |
| **GPU** | Not required (CPU mode) | Dedicated GPU | NVIDIA GeForce GTX 1050 Ti (4GB) or RTX Series |

---

## 14. Testing, Chaos & Quality Assurance

PRUBETH IDE is validated by an automated test suite comprising **303 passing tests** with 100% pass rate:

```powershell
# Run full automated test suite (303 tests)
pytest tests/ -v

# Run reliability, chaos and meta-testing suite (69 tests)
pytest tests/reliability/ -v

# Run installer verification and download engine tests (22 tests)
pytest tests/installer/ tests/test_installer_modes.py tests/test_installer_github_download.py -v

# Run Horizon Continuous Verification Doctor
python local_ai_studio_pro.py --verify doctor
```

### Verified Test Breakdown
- **Gate 1 Core Architecture:** 107 tests passing
- **Gate 10 Reliability & Polyglot:** 180 tests passing
- **Gate 12 Release & Packaging:** 14 tests passing
- **Security & Ed25519 Integrity:** 2 tests passing
- **Total Ground-Truth Verified:** **303 / 303 (100% Pass Rate in ~214s)**

---

## 15. Build & Packaging Pipeline

To reproduce the release build and package official distributable assets:

```powershell
# 1. Package payload, generate manifest, and sign cryptographically
python scripts/build_release_artifacts.py

# 2. Compile lightweight Setup.exe bootstrap installer
python build_setup_exe.py

# 3. Verify installer in silent test mode
.\dist\Setup.exe --verify-only
```

---

## 16. Official Downloadable Releases

Current Release: **v1.91.0 (Horizon Edition)**

| Release Asset | Size | SHA-256 Digest | Purpose |
| :--- | :---: | :--- | :--- |
| **`PrubethIDE-v1.91.0-Setup.exe`** | 251 MB | `bfac4f1ac2fd6c79c35d35ae1192f7e31a6d8c5bcfa8bb18600af13e1d549a3c` | Official Windows Full Standalone Desktop Installer |
| **`Prubeth-Payload-1.91.0-windows-x64.zip`** | 3.0 MB | `1e5aa1f03506bbbd18e8fbfa8d29f2581befe2ecd76699f1ee52f2cb556dba40` | Complete Application Payload (Portable & Auto-Update) |
| **`Prubeth-Offline-Setup-1.91.0.exe`** | 48 MB | `22b156e1b43ebbbe4258886bd020540901221f8eae52db997359393245819250` | Standalone Air-Gapped Offline Installer |
| **`Prubeth-Setup-1.91.0.exe`** | 45 MB | `24d598d72480310f169fe928afe36e3a4e9c82513f2f60afd7c1b48333f97025` | Online Verified Bootstrap Installer |
| **`Prubeth-Manifest-1.91.0.json`** | 682 B | `c6fd59ebdef587b261e5230ff6994d698850723988ff9eb56d05116e814b9522` | Canonical Release Manifest |
| **`Prubeth-Manifest-1.91.0.sig`** | 130 B | `3143e4152e1ef6771005cae80ba307180c07844dad8ba8e741ddad6e1bffc248` | Ed25519 Cryptographic Signature |
| **`Prubeth-SHA256SUMS.txt`** | 488 B | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | SHA-256 Checksum Manifest |
| **`Prubeth-SBOM-1.91.0.json`** | 582 B | `01061464e51c81f26634f7dce1dc23de65c499104ac07af4dadd560a980131dc` | CycloneDX Software Bill of Materials |

---

## 17. Engineering Roadmap

- [x] Horizon Architecture: 12 verified subsystems with universal inventory mapping.
- [x] Out-of-process Crash Supervisor and PRINCE2 7 reliability engines.
- [x] Asymmetric Ed25519 cryptographic release signing and strict TLS context verification.
- [x] Dual-mode lightweight installer (Mode A threshold / Mode B offline).
- [ ] Language Server Protocol (LSP) language server auto-installer for Rust and Go.
- [ ] Model Context Protocol (MCP) dynamic remote server manager GUI.
- [ ] Native Linux AppImage and macOS DMG release builds.

---

## 18. Known Limitations & Tested Boundaries

- **Single Active Window:** The current UI runs as a single primary window with dockable side panels; multi-window detached layouts are not yet supported.
- **Local Model VRAM:** Local LLM execution requires sufficient VRAM (4 GB for 1.5B/3B models, 8 GB+ for 7B models). CPU fallback is functional but slower.
- **Windows-First Features:** DPAPI credential storage and registry integration are native to Windows; Linux/macOS use Fernet file-based keyrings.

---

## 19. Contribution Guidelines

Contributions are welcome! Please follow these standards:
1. **Fork & Branch:** Create a feature branch (`git checkout -b feat/your-feature`).
2. **Code Style:** Adhere to PEP 8 standards with type annotations.
3. **Tests Required:** Add pytest unit tests under `tests/` for all new features.
4. **Verification:** Ensure all 303 tests pass (`pytest tests/ -q`) before submitting PR.
5. **Security First:** Never commit plain text credentials, tokens, or private signing keys.

---

## 20. License & Third-Party Notices

PRUBETH IDE is licensed under the **BSVR Permissive Open Developer License (Dual MIT / Apache 2.0 terms)**:
- **Commercial Use:** Permitted for proprietary software, internal enterprise deployment, and SaaS backends.
- **Modification & Distribution:** Permitted with attribution preservation.
- **Third-Party Components:**
  - PyQt5 / Qt 5.15 (GPL/LGPL)
  - QScintilla 2.14.1 (GPL)
  - Requests / Cryptography (Apache 2.0 / BSD)

See [LICENSE](LICENSE) for the full legal text.

---

## 21. Support & Vulnerability Disclosure

- **Issue Tracker:** [GitHub Issues](https://github.com/imyouiamyou/prubeth-ide/issues)
- **Security Vulnerability Reporting:** Send reports to `security@bsvr.work` with reproduction steps. Do not open public issues for security vulnerabilities.
- **Official Website:** [https://www.bsvr.work/](https://www.bsvr.work/)

---

## 22. Acknowledgments

- The **Qt Project** and **Riverbank Computing** for PyQt5 and QScintilla.
- The **Ollama Team** for enabling high-performance local LLM execution.
- The open-source community for pytest, cryptography, and Python packaging tools.

---

<div align="center">
  <p>© 2025–2026 BSVR Technologies. Engineered for clean developer flow.</p>
  <p><a href="https://www.bsvr.work/">bsvr.work</a> · <a href="https://github.com/imyouiamyou/prubeth-ide">github.com/imyouiamyou/prubeth-ide</a></p>
</div>
