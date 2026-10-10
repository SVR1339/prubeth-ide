# SO NAIVE IDE — Release Readiness & Verification Gates
**Document ID:** DOC-ASSESS-004  
**Version:** 3.0.0-RC1  
**Date:** October 10, 2026  

---

## 1. Release Verification Gates

| Gate ID | Verification Gate | Target Requirement | Evaluation Method | Initial State | Target State |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GATE-01** | **Zero Plaintext Secrets** | Zero plaintext API keys in `settings.json`, `accounts.json`, logs, or dialogs. | Automated scanning & DPAPI verification tests. | ❌ Plaintext in settings.json | ✅ All secrets encrypted with DPAPI/AES |
| **GATE-02** | **Workspace Isolation** | Traversal attacks (`../../`) throw `PermissionError` and halt. | Adversarial path traversal unit tests. | ❌ Traversal unconstrained | ✅ Enforced via `core/workspace.py` |
| **GATE-03** | **Safe Command Gateway** | No agent command executed via unrestricted `shell=True`. | Code inspection & subprocess security tests. | ❌ Direct shell=True | ✅ Structured execution via `core/tool_gateway.py` |
| **GATE-04** | **Model & Task Routing** | Dynamic capability routing with Small, Medium, Large profiles. | Unit tests validating capability matching & policies. | ❌ Static hardcoded cascade | ✅ Policy engine in `core/router.py` |
| **GATE-05** | **Real MCP Transport** | Functional JSON-RPC tool invocation over stdio subprocess. | Integration test with live test MCP server. | ❌ Mock string return | ✅ Real JSON-RPC in `core/plugin_engine.py` |
| **GATE-06** | **Regression Integrity** | 100% of baseline tests passing + new security & engine tests. | `pytest tests/ -v` execution. | 27/27 Passing | 35+/35+ Passing (100%) |
| **GATE-07** | **Installer & Binary Build**| Setup executable unpacks real payload and launches successfully. | Extraction integrity test and binary compilation. | ✅ Verified (36.7 MB installer) | ✅ Verified with all modular core assets |

---

## 2. Release Recommendation Framework
- **GO:** All 7 gates verified passing with objective evidence.
- **CONDITIONAL GO:** Minor non-security edge case pending, with documented mitigation.
- **NO-GO:** Any security vulnerability (GATE-01, 02, 03) or regression in core editing workflow.
