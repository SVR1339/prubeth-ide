# SUKHI IDE — Horizon Edition
## CONTINUOUS TEST STRATEGY & VERIFICATION METHODOLOGY

**Test Specification:** ENG-TEST-001  
**Target Release:** Horizon Edition v3.0.0+  
**Status:** Approved Quality Standard  
**Effective Date:** October 10, 2026

---

### 1. Testing Philosophy & Quality Gate

No capability is marked complete without automated tests proving its operational correctness, exception handling, and security boundaries. "It compiles" or "the class exists" is rejected as evidence of completion.

Every milestone must maintain a **100% test pass rate** with zero regressions against the baseline.

---

### 2. Testing Pyramid & Test Levels

```
               /  E2E Packaging & Install Tests  \
              /-----------------------------------\
             /   Subsystem Integration Test Suites \
            /---------------------------------------\
           /    Unit Tests (Pure Logic, Models, AST) \
          /-------------------------------------------\
```

1. **Unit Tests (Fast, In-Memory):**
   - Pure algorithm verification: AST stack trace parsing, diff calculation, token counting, path canonicalization, credential encryption/decryption, JSON schema validation.
   - Execution target: < 5 seconds for full unit suite.

2. **Subsystem Integration Tests (Process & IO):**
   - Subprocess execution: `ToolGateway` sandboxed commands, `RealMCPStdioClient` JSON-RPC pipes, `LspClient` stdio transport, `GitService` command parsing.
   - Headless Qt fixtures: `QApplication` running in offscreen mode (`QT_QPA_PLATFORM=offscreen`).

3. **Packaging & Distribution Tests:**
   - Payload archive creation (`app_payload.zip`), setup wizard headless extraction, launcher script syntax verification.

---

### 3. Test Suites Inventory

| Test Module | Coverage Scope | Target Subsystems | Baseline Status |
| :--- | :--- | :--- | :---: |
| `tests/test_studio.py` | UI core, editor, diff, router, tools, credentials, workspace | `core/`, `ui/`, `installer/` | **33/33 Passed** |
| `tests/test_workspace.py` | Checkpoints, rollback, multi-file atomic transactions | `workspace/` | *Milestone M03* |
| `tests/test_source_control.py` | Git status, diff parsing, staging, commit composer | `source_control/` | *Milestone M04* |
| `tests/test_language_services.py` | LSP JSON-RPC client, diagnostics, definition | `language_services/` | *Milestone M05* |
| `tests/test_debugging.py` | DAP client, breakpoint management, launch configs | `debugging/` | *Milestone M06* |
| `tests/test_rag.py` | AST symbol extraction, local indexer, lexical search | `ai/rag/` | *Milestone M07* |

---

### 4. Continuous Test Execution Procedure

Tests must be executed using the standardized virtual environment runner:
```powershell
.\.venv\Scripts\pytest.exe tests/ -v
```
All pull requests, milestones, and release candidates must produce clean green output with zero unhandled exceptions.
