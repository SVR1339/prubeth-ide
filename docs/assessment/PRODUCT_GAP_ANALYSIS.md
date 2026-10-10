# SO NAIVE IDE — Product Gap Analysis & Verification Audit
**Document ID:** DOC-ASSESS-001  
**Version:** 3.0.0-RC1  
**Date:** October 10, 2026  
**Auditor:** Principal AI Systems & Software Architect  

---

## 1. Executive Summary
This document establishes the verified baseline of **SO NAIVE IDE (Horizon Edition v3.0.0)** following rigorous static analysis, runtime verification, and test execution across the repository.

---

## 2. Feature Classification Matrix

| Feature Area | Sub-System | Baseline Status | Evidence & Defect Classification | User Impact | Severity | Proposed Repair |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Security** | Credential Storage | **Broken / Missing** | Secrets (`gemini_api_key`, `navy_api_key`, `openai_api_key`, `claude_api_key`, `github_token`) stored in plaintext JSON in `%USERPROFILE%\.local_ai_studio_pro\settings.json`. | Credential compromise by local scripts or malicious repository files. | **CRITICAL** | Implement `core/credentials.py` with Windows DPAPI (`crypt32.dll`) + AES-256-GCM fallback. Migrate and zero out plaintext. |
| **Security** | Secret Redaction | **Missing** | Tracebacks, exception messages, and dialog logs do not filter out Bearer tokens or API keys matching `sk-...`, `AQ...`. | Exposure of keys in error dialogs, logs, and screenshots. | **HIGH** | Implement centralized regex redactor in `core/credentials.py` wrapping logging and UI errors. |
| **Security** | Workspace Boundary | **Broken** | `AgentToolEngine` resolves relative paths via `(root / path).resolve()` without validating `Path.is_relative_to(root)`. | Path traversal attacks (`../../windows`) allowing unauthorized read/write. | **CRITICAL** | Implement `core/workspace.py` with canonical path resolution and strict boundary assertions. |
| **Security** | Command Execution | **Broken** | `AgentToolEngine.execute_tool('run_command')` uses `subprocess.run(cmd, shell=True)` with no allowlist or approval modal. | Arbitrary remote command execution via prompt injection. | **CRITICAL** | Implement `core/tool_gateway.py` with split argument parsing, timeout, output truncation, and approval gates. |
| **AI Routing** | Model Cascade | **Partial** | Hardcoded cascade in `IntelligentModelRouter` (`Gemini -> NavyAI -> Ollama -> OpenAI`). Lacks capability matching. | Suboptimal model selection, inability to configure per-task fallbacks. | **MEDIUM** | Implement `core/model_registry.py` with capability metadata (vision, tools, context) and `core/router.py`. |
| **Agent Autonomy**| Agent Profiles | **Missing** | No distinction between Small (read-only/fast), Medium (bounded multi-file), and Large (architecture/approval). | Over-privileged agents executing multi-step mutations without planning. | **HIGH** | Implement `core/router.py` with Small, Medium, Large workload profiles and deterministic policy constraints. |
| **Task Engine** | Task Lifecycle | **Partial** | Simple `task_id` in `AIWorker`; missing explicit persistent states (`QUEUED`, `WAITING_APPROVAL`, `CANCELLED`). | No recovery after crash, no task pause/resume, no cancellation verification. | **MEDIUM** | Implement `core/task_engine.py` with persistent task state machine, cancellation tokens, and checkpoints. |
| **Extensibility** | MCP Integration | **Mocked** | `AgentToolEngine.execute_tool('call_mcp')` returns formatted string literal without invoking JSON-RPC transport. | Inability to connect to real Model Context Protocol servers. | **HIGH** | Implement real JSON-RPC stdio client adapter in `core/plugin_engine.py`. |
| **Packaging** | Installer & Payload | **Verified** | `build_setup_exe.py` packages `app_payload.zip`, `setup_wizard.py` extracts and verifies `local_ai_studio_pro.py`. 27/27 tests pass. | Complete and reproducible installation. | **RESOLVED** | Maintain automated tests and verify packaging during release pipeline. |

---

## 3. Test Suite Baseline
- **Baseline Suite:** `tests/test_studio.py`
- **Total Tests:** 27
- **Passed:** 27 (100%)
- **Baseline Duration:** 10.36s
- **Target Post-Remediation:** 35+ tests passing across core security, workspace guard, and credential encryption.
