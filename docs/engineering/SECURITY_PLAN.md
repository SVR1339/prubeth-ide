# SUKHI IDE — Horizon Edition
## APPLICATION SECURITY PLAN & DEFENSE-IN-DEPTH SPECIFICATION

**Security Standard:** ENG-SEC-001  
**Classification:** Restricted Engineering Document  
**Status:** Approved & Active  
**Effective Date:** October 10, 2026

---

### 1. Security Philosophy & Defense-in-Depth

SUKHI IDE operates under the principle that AI agents must be treated as untrusted actors operating within strictly bounded, observable environments. No prompt instruction or model assertion is accepted as an architectural security boundary. Security is enforced exclusively by the deterministic host platform.

---

### 2. STRIDE Threat Model & Mitigations

```
Threat Category          Specific Threat Scenario                     Enforced Architectural Safeguard
-----------------        --------------------------------             ---------------------------------
Spoofing                 Forged JSON-RPC requests from MCP servers    Schema validation & isolated stdio pipes
Tampering                Agent writes corrupting source files         Atomic writes with temporary files & .bak backups
Repudiation              Unaccounted autonomous agent shell commands  Structured action logs with timestamp & user ID
Information Disclosure   Plaintext API keys leaked in repositories    DPAPI / Fernet encrypted vault with auto-scrub
Denial of Service        Infinite loops or destructive commands       Bounded execution steps, timeouts & danger flags
Elevation of Privilege   Agent traversing workspace via '../'         WorkspaceGuard canonical path jail & symlink block
```

---

### 3. Core Security Pillars

#### 3.1 Zero-Plaintext Credential Management (`core/credentials.py`)
- **Windows:** Protected using Windows Data Protection API (`CryptProtectData`), tethered to the authenticated Windows logon session.
- **Linux:** Protected using Fernet authenticated symmetric encryption (AES-128-CBC + HMAC-SHA256) with restricted POSIX key permissions (`0600`).
- **Scrubbing Pipeline:** Legacy plaintext keys in `.env` or `settings.json` are automatically imported into the vault and wiped from disk.
- **Continuous Redaction:** Regex filters intercept all console output, agent logs, and error tracebacks to redact API keys (`AIza...`, `sk-ant...`, `sk-...`, `ghp_...`).

#### 3.2 Workspace Boundary Enforcement (`core/workspace.py`)
- All filesystem operations are forced through `WorkspaceGuard.canonicalize(path)`.
- Rejects any relative path resolving outside the designated active workspace directory.
- Detects directory junctions and symbolic links pointing outside the workspace boundary, throwing a `PermissionError`.
- Forbids absolute drive hops on Windows (e.g. attempting to read `C:\Windows\System32`).

#### 3.3 Risk-Classified Tool Gateway (`core/tool_gateway.py`)
- Centralized execution gate replacing arbitrary `shell=True` subprocesses.
- Command Risk Tiers:
  - `SAFE`: Read-only inspections (`git status`, `pytest`, `dir`, `ls`).
  - `MEDIUM`: Build and dependency installations (`pip install`, `npm install`).
  - `DANGEROUS`: Destructive deletions or system configurations (`rmdir /s /q`, `rm -rf`, `format`).
- Dangerous commands require explicit interactive user confirmation before execution.

#### 3.4 Multi-File Rollback Checkpoints (`workspace/checkpoints.py`)
- Before any autonomous agent edits a file, pre-edit hashes and file states are recorded.
- In the event of a test failure, error, or user cancellation, all touched files can be restored to their exact pre-task baseline.
