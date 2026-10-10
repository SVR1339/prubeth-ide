# SUKHI IDE — Horizon Edition
## SUB-SYSTEM IMPLEMENTATION ROADMAP & EXECUTION PLAN

**Roadmap Document:** ENG-ROADMAP-001  
**Target Architecture:** Modular Horizon Edition v3.0.0+  
**Status:** Active Sprint Execution  
**Effective Date:** October 10, 2026

---

### 1. Phased Execution Overview

The roadmap delivers all identified missing capabilities through vertical, test-driven slices while preserving 100% backward compatibility and desktop stability.

```
M00 (Baseline) ──► M01 (Governance) ──► M02 (Core Wire-up) ──► M03 (Checkpoints)
                                                                     │
M07 (RAG Search) ◄── M06 (DAP Debug) ◄── M05 (LSP Intel) ◄── M04 (Git Sidebar)
       │
       ▼
M08 (Integration Verification & Release Gate)
```

---

### 2. Detailed Milestone Specifications

#### Milestone M02: Core Decoupling Wire-Up
- **Objective:** Bind existing tested modules (`core/model_registry.py`, `core/router.py`, `core/task_engine.py`) into [`local_ai_studio_pro.py`](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py).
- **Deliverables:**
  - Replace hardcoded model dictionaries in UI with `ModelRegistry` dynamic lookup.
  - Route user chat and agent dispatches through `AgentRouter` profiles (`speed`, `complex_code`, `agent`).
  - Bind agent execution steps to `TaskEngine` state machine transitions (`PLANNING` -> `RUNNING` -> `COMPLETED`).
- **Exit Criteria:** UI model comboboxes populate from registry; tasks persist to disk; existing 33 tests pass.

#### Milestone M03: Multi-File Transactional Checkpoints & Rollback
- **Objective:** Implement session-level atomic snapshots and rollback for autonomous agent file modifications.
- **Deliverables:**
  - Create `workspace/checkpoints.py` with `CheckpointManager`.
  - Capture pre-edit file hashes, original content, created files, and modified files before agent execution.
  - Add one-click "Rollback Agent Task" capability restoring all affected files atomically.
  - Automated tests validating multi-file rollback, hash verification, and directory traversal rejection.
- **Exit Criteria:** Modifying 5 files and executing rollback restores original contents identically.

#### Milestone M04: Visual Source Control (Git Integration)
- **Objective:** Implement a dedicated Git engine and visual sidebar for source control.
- **Deliverables:**
  - Create `source_control/git_service.py` wrapping Git CLI commands without unsafe shell interpolation.
  - Implement branch detection, changed file discovery (staged, unstaged, untracked), diff generation, staging/unstaging, and commit creation.
  - Implement `ui/git_sidebar.py` presenting changed file lists with one-click staging and commit message composer.
  - Automated tests in `tests/test_source_control.py` verifying status parsing, diff generation, and commit creation.
- **Exit Criteria:** Live git status rendered in sidebar; files staged and committed cleanly.

#### Milestone M05: Language Server Protocol (LSP) Engine
- **Objective:** Build a real JSON-RPC 2.0 stdio LSP client for language intelligence.
- **Deliverables:**
  - Create `language_services/lsp_client.py` establishing bidirectional stdio pipes with language servers (e.g. `pylsp` / `pyright`).
  - Implement initialize handshake, document open/change synchronization, and `textDocument/definition` request.
  - Implement diagnostic notification parser capturing linting errors and warnings.
  - Unit tests verifying JSON-RPC framing, document sync, and definition parsing.
- **Exit Criteria:** LSP client connects, synchronizes document buffers, and parses diagnostics.

#### Milestone M06: Debug Adapter Protocol (DAP) Engine
- **Objective:** Build a Python debug adapter client foundation for interactive debugging.
- **Deliverables:**
  - Create `debugging/dap_client.py` communicating with `debugpy` over DAP protocol.
  - Implement breakpoint management (add, remove, list breakpoints).
  - Implement launch configuration generator for active Python scripts.
  - Automated tests verifying DAP message framing and breakpoint state tracking.
- **Exit Criteria:** Breakpoint registration and debug launch payload validated.

#### Milestone M07: Semantic Codebase Indexing & Local Search (RAG)
- **Objective:** Implement a local retrieval pipeline with AST symbol extraction for large codebases.
- **Deliverables:**
  - Create `ai/rag/code_indexer.py` scanning workspace source files.
  - Implement AST chunking extracting class names, function definitions, docstrings, and line ranges.
  - Implement lexical BM25/keyword ranker and optional local embedding hook.
  - Unit tests verifying symbol chunking, line range accuracy, and search ranking.
- **Exit Criteria:** Natural language query retrieves relevant code chunks with exact file/line citations.

#### Milestone M08: Verification & Release Packaging Gate
- **Objective:** Execute full test suite, measure net line count additions, and update ledger.
- **Deliverables:**
  - Execute combined Pytest test suite across all subsystems.
  - Run `scripts/count_lines.py --json` and record metrics in `LINE_COUNT_LEDGER.md`.
  - Compile final standalone Windows installer and verify distribution packages.
- **Exit Criteria:** 100% test pass rate with zero regressions.
