# SUKHI IDE — Horizon Edition
## COMPREHENSIVE FEATURE CAPABILITY MATRIX

**Document ID:** ENG-FEAT-001  
**Target Release:** Horizon Edition v3.0.0+  
**Audit Baseline:** October 10, 2026  
**Status:** Living Engineering Matrix

---

### Status Definitions
- **Fully Integrated:** Production code implemented in core/ui, connected to runtime flows, and verified by passing automated tests.
- **In Core (Decoupled):** Implemented in `core/` and tested by unit tests, but awaiting UI binding.
- **In Progress:** Actively under implementation in current sprint.
- **Planned / Missing:** Defined in architecture; scheduled in roadmap.

---

### 1. Code Editing & Editor Core (`editor/` & `ui/`)

| Feature / Capability | Target Subsystem | Current Status | Milestone | Verification Reference |
| :--- | :--- | :---: | :---: | :--- |
| **Multi-tab buffer management** | `editor/` | **Fully Integrated** | Baseline | `local_ai_studio_pro.py:TabWidget` |
| **QScintilla Polyglot Lexers (15+ langs)** | `editor/` | **Fully Integrated** | Baseline | `local_ai_studio_pro.py:LexerFactory` |
| **Dirty state tracking & auto-save** | `editor/` | **Fully Integrated** | Baseline | `tests/test_studio.py:test_editor_functionality` |
| **Quick Open Fuzzy Search (`Ctrl+P`)** | `ui/` | **Fully Integrated** | Baseline | `local_ai_studio_pro.py:QuickOpenDialog` |
| **Command Palette (`Ctrl+Shift+P`)** | `ui/` | **Fully Integrated** | Baseline | `local_ai_studio_pro.py:CommandPaletteDialog` |
| **Inline AI Quick Edit (`Ctrl+K`)** | `ui/` | **Fully Integrated** | Baseline | `local_ai_studio_pro.py:QuickEditDialog` |
| **Visual Diff Review & Patching** | `ui/` | **Fully Integrated** | Baseline | `tests/test_studio.py:test_visual_diff_dialog` |

---

### 2. Language Intelligence & Diagnostics (`language_services/`)

| Feature / Capability | Target Subsystem | Current Status | Milestone | Verification Reference |
| :--- | :--- | :---: | :---: | :--- |
| **LSP JSON-RPC 2.0 Stdio Client** | `language_services/` | **In Progress** | M05 | `language_services/lsp_client.py` |
| **Language Server Lifecycle Manager** | `language_services/` | **Planned** | M05 | Pyright / pylsp detection |
| **Go to Definition (`F12`)** | `language_services/` | **Planned** | M05 | Cross-file symbol resolution |
| **Find All References (`Shift+F12`)** | `language_services/` | **Planned** | M05 | Symbol usage indexing |
| **Live Diagnostics & Linter Squiggles**| `language_services/` | **Planned** | M05 | Real-time diagnostic parser |

---

### 3. Debugging & Testing (`debugging/` & `testing/`)

| Feature / Capability | Target Subsystem | Current Status | Milestone | Verification Reference |
| :--- | :--- | :---: | :---: | :--- |
| **Crash Traceback Auto-Fix AST Compiler**| `ai/` | **Fully Integrated** | Baseline | `local_ai_studio_pro.py:AutoFixCompiler` |
| **Headless Pytest Runner Tool** | `testing/` | **Fully Integrated** | Baseline | `<tool:run_tests>` in `ToolGateway` |
| **DAP Protocol Client (Debugpy)** | `debugging/` | **In Progress** | M06 | `debugging/dap_client.py` |
| **Clickable Gutter Breakpoints** | `debugging/` | **Planned** | M06 | QScintilla margin marker toggle |
| **Call Stack & Variables Inspection** | `debugging/` | **Planned** | M06 | Debug scope tree widget |

---

### 4. Source Control & Versioning (`source_control/`)

| Feature / Capability | Target Subsystem | Current Status | Milestone | Verification Reference |
| :--- | :--- | :---: | :---: | :--- |
| **Git Status & Branch Detection Engine** | `source_control/` | **In Progress** | M04 | `source_control/git_service.py` |
| **Changed-Files Staging / Unstaging** | `source_control/` | **In Progress** | M04 | `source_control/git_service.py` |
| **Visual Git Sidebar Dock Widget** | `ui/` | **In Progress** | M04 | `ui/git_sidebar.py` |
| **Commit Message Composer** | `source_control/` | **In Progress** | M04 | Git commit execution with validation |
| **Branch Switching & Status Watcher** | `source_control/` | **Planned** | M04 | Background branch monitor |

---

### 5. AI Models, Router & Agent Orchestration (`ai/`, `core/`, `providers/`)

| Feature / Capability | Target Subsystem | Current Status | Milestone | Verification Reference |
| :--- | :--- | :---: | :---: | :--- |
| **Dynamic Model Registry** | `core/` | **In Core (Decoupled)**| M02 | `core/model_registry.py` (Tested) |
| **Task-Profile Multi-Model Router** | `core/` | **In Core (Decoupled)**| M02 | `core/router.py` (Tested) |
| **Agent Task State Machine** | `core/` | **In Core (Decoupled)**| M02 | `core/task_engine.py` (Tested) |
| **Google Gemini SSE Streaming** | `providers/` | **Fully Integrated** | Baseline | `local_ai_studio_pro.py:GeminiWorker` |
| **Ollama Local CUDA GPU Inference** | `providers/` | **Fully Integrated** | Baseline | `local_ai_studio_pro.py:OllamaWorker` |
| **Universal Provider Hub Dialog** | `ui/` | **Fully Integrated** | Baseline | `local_ai_studio_pro.py:UniversalProviderHub`|
| **Multi-File Transactional Checkpoints**| `workspace/` | **In Progress** | M03 | `workspace/checkpoints.py` |
| **Semantic Codebase Search (Vector RAG)**| `ai/rag/` | **In Progress** | M07 | `ai/rag/code_indexer.py` |

---

### 6. Security, Sandboxing & Credential Vault (`core/`, `workspace/`, `tools/`)

| Feature / Capability | Target Subsystem | Current Status | Milestone | Verification Reference |
| :--- | :--- | :---: | :---: | :--- |
| **Zero-Plaintext Windows DPAPI Vault** | `core/credentials` | **Fully Integrated** | Baseline | `core/credentials.py:CredentialStore` |
| **POSIX Fernet AES-GCM Encrypted Fallback**| `core/credentials` | **Fully Integrated** | Baseline | `tests/test_studio.py:test_dpapi` |
| **Regex Secret Redaction Filter** | `core/credentials` | **Fully Integrated** | Baseline | `core/credentials.py:redact_secrets` |
| **Workspace Jail Boundary Enforcement** | `core/workspace` | **Fully Integrated** | Baseline | `core/workspace.py:WorkspaceGuard` |
| **Risk-Classified Tool Gateway** | `core/tool_gateway` | **Fully Integrated** | Baseline | `core/tool_gateway.py:ToolGateway` |

---

### 7. Packaging, Installers & Distribution (`packaging/`)

| Feature / Capability | Target Subsystem | Current Status | Milestone | Verification Reference |
| :--- | :--- | :---: | :---: | :--- |
| **Standalone Windows Setup Installer** | `packaging/` | **Fully Integrated** | Baseline | `dist/SukhiIDE-v3.0.0-Setup.exe` (38.5MB) |
| **Universal Portable ZIP Distribution**| `packaging/` | **Fully Integrated** | Baseline | `SukhiIDE-v3.0.0-Universal-Portable.zip` |
| **Cross-Platform Linux Shell Launcher**| `packaging/` | **Fully Integrated** | Baseline | `run_ide.sh` (POSIX auto-bootstrap) |
| **Dual Windows Batch Launchers** | `packaging/` | **Fully Integrated** | Baseline | `run_ide.bat`, `run_local_ai_studio_pro.bat`|
