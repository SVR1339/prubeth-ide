# SUKHI IDE — Horizon Edition v3.0.0
## ARCHITECTURAL DECISION LOG (ADR) & GOVERNANCE RECORD

**Governance Framework:** PRINCE2 7 Project Management & Agile V2 Iterative Engineering  
**Date of Record:** October 10, 2026  
**Document Status:** RATIFIED & APPROVED

---

### ADR-001: Product Identity Rebranding to SUKHI IDE — Horizon Edition v3.0.0

- **Context:** The IDE was previously branded as "SO NAIVE IDE" and "Local AI Studio Pro". To establish a cohesive, market-ready identity while adhering to the user's directive, a permanent identity is required.
- **Decision:** Officially rebrand the product to **SUKHI IDE — Horizon Edition v3.0.0** across all UI surfaces, window titles, splash screens, dialogs, installers, launchers, and documentation.
- **Backward Compatibility:** Retain `SoNaive.bat` and legacy configuration path migration (`~/.local_ai_studio_pro`) to ensure existing installations upgrade without breaking user data or shortcuts.
- **Consequences:** Unified branding; zero regression for legacy scripts.

---

### ADR-002: Zero-Plaintext Cryptographic Credential Vault (`core/credentials.py`)

- **Context:** Storing API keys in plaintext `.env` files or JSON configurations poses a severe security risk of credential leakage in git repositories and disk forensic scans.
- **Decision:** Implement `CredentialStore` using native Windows Data Protection API (DPAPI via `CryptProtectData`) for Windows, and authenticated symmetric Fernet (AES-128-CBC + HMAC-SHA256) for Linux. Implement automatic transparent migration that encrypts legacy keys and scrubs plaintext from disk. Implement real-time regex secret redaction across all logs.
- **Consequences:** Eliminates plaintext secrets at rest and in memory logs. Provides cross-platform compatibility across Windows and Linux.

---

### ADR-003: Workspace Jail & Boundary Enforcement (`core/workspace.py`)

- **Context:** Autonomous AI agents executing file write or patch operations could potentially escape the project directory via `../` path traversal, absolute drive references, or symbolic link resolution.
- **Decision:** Mandate that all file operations pass through `WorkspaceGuard.canonicalize()`. The guard resolves relative paths to absolute canonical forms, enforces `is_relative_to(project_root)`, and throws a `PermissionError` on path traversal or symlink escapes.
- **Consequences:** Guarantees directory isolation. Prevents accidental or malicious modification of files outside the active workspace.

---

### ADR-004: Centralized Risk-Classified Tool Gateway (`core/tool_gateway.py`)

- **Context:** Direct invocation of arbitrary shell commands with `subprocess.Popen(cmd, shell=True)` exposes the IDE to shell injection and uncontrolled execution of destructive commands.
- **Decision:** Route all terminal and agent command executions through `ToolGateway`. Classify commands into risk tiers (`SAFE`, `MEDIUM`, `DANGEROUS`). Enforce working directory restrictions, scrub secrets from stdout/stderr, and prompt for confirmation on destructive patterns (`rm -rf`, `rmdir /s /q`).
- **Consequences:** Controlled execution surface; full visibility into agent commands.

---

### ADR-005: Modular Dynamic Model Registry & Router Architecture (`core/`)

- **Context:** Model configurations were previously hardcoded in monolithic UI classes, making it difficult to extend to new providers or adapt routing strategies.
- **Decision:** Decouple AI model management into `core/model_registry.py` and `core/router.py`. Introduce task-profile routing (`speed`, `complex_code`, `chat`, `cheap`, `agent`) with automatic latency/context-aware fallbacks.
- **Consequences:** Extensible multi-model platform supporting Google Gemini, Ollama, NavyAI, Anthropic, OpenAI, and Groq with clean separation of concerns.

---

### ADR-006: Dual Packaging & Cross-Platform Launch Engine

- **Context:** Users require both a zero-dependency standalone Windows setup executable and a native Linux/Ubuntu launcher script.
- **Decision:**
  1. Build `SukhiIDE-v3.0.0-Setup.exe` with PyInstaller, embedding the complete application payload, core modules, assets, and tests, with copies to `setup.exe` and `SoNaive-v3.0.0-Setup.exe`.
  2. Implement `run_ide.sh` for Linux, providing automatic virtualenv detection and package bootstrapping.
  3. Package `SukhiIDE-v3.0.0-Universal-Portable.zip` containing all code, assets, and launchers.
- **Consequences:** Turnkey installation for Windows users; native shell execution for Linux users.
