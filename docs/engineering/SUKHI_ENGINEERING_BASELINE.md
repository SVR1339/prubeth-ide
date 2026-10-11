# SUKHI IDE — Engineering Baseline & System Inventory
**Document ID:** `BASE-2026-10-10-V1`  
**Product:** SUKHI IDE — Horizon Edition v3.0.0  
**Workspace Root:** `c:\Users\asus\heretic-work`  
**Git Baseline Commit:** `9c008a6` (`feat(architecture): implement M00-M08 full-thrust architecture with 60/60 passing tests`)  
**Branch:** `master`  
**Execution Environment:** Windows 11, Python 3.12.2 (`.venv`), PyQt5 5.15.11, QScintilla 2.14.1  
**Author:** Senior Software Architect, Principal Python Engineer, DevSecOps & QA Lead  

---

## 1. Executive Baseline & Environment Overview

This document establishes the verified Phase Zero engineering baseline for SUKHI IDE — Horizon Edition v3.0.0. Every architectural claim, module boundary, call graph, and test execution status documented herein has been directly inspected from repository source code and verified with live test runs.

### 1.1 Technical Stack & Dependency Inventory
- **Application Entry Point:** `local_ai_studio_pro.py::main()` (invoked via `so-naive` CLI command or `python local_ai_studio_pro.py`).
- **GUI Framework:** PyQt5 (Qt 5.15), QScintilla (code editor with syntax lexing, line markers, visual diffs).
- **Python Runtime:** Python 3.12.2 x64 on Windows.
- **Dependency Manifests:**
  - `pyproject.toml`: specifies `setuptools>=61.0`, `PyQt5>=5.15.10`, `QScintilla>=2.14.1`, `requests>=2.31.0`. Dev extras: `pytest>=8.0.0`, `pyinstaller>=6.5.0`.
  - Virtual Environment: `.venv/` containing installed packages and pytest 9.1.1.
- **Packaging & Deployment:** `installer/` containing Windows installer generator, GGUF model verifiers, and PyInstaller spec files.

---

## 2. Baseline Architecture & Module Ownership

The repository is organized into distinct subpackages:

| Subsystem / Path | Module Ownership | Key Responsibilities | Current Verification Status |
| :--- | :--- | :--- | :--- |
| `local_ai_studio_pro.py` | GUI / Application Core | Main window (`Studio`), AI worker thread (`AIWorker`), model cascade router (`IntelligentModelRouter`), tool engine (`AgentToolEngine`). | **Active & Verified** (Primary runtime entry point). |
| `core/workspace.py` | Security / Filesystem | `WorkspaceGuard`: enforces workspace containment, canonicalizes paths, defends against directory traversal, provides safe atomic file reads, writes, and patches. | **Active & Verified** (Passing unit tests). |
| `core/credentials.py` | Security / Cryptography | `DPAPICredentialStore`, `SecretRedactor`: Windows DPAPI / Fernet encryption for secrets, regex-based redaction of tokens and keys in output streams. | **Active & Verified** (Passing unit tests). |
| `core/tool_gateway.py` | Security / Process Sandbox | `ToolGateway`: categorizes commands (`SAFE`, `READ_ONLY`, `MUTATING`, `HIGH_RISK`), enforces timeouts, redacts output secrets. | **Active / Unwired Hook** (Approval hook is `None` in `AgentToolEngine`, blocking high-risk commands). |
| `core/task_engine.py` | Orchestration / Tasks | `TaskEngine`: in-memory state machine for `Task` and `TaskStep` tracking. | **Dormant / In-Memory** (Instantiated in `AgentToolEngine` L1514 but unused; no database persistence). |
| `core/router.py` | AI Routing | `IntelligentRouter`, `AgentProfile` (`SMALL`, `MEDIUM`, `LARGE`): capability & cost-based model routing. | **Dormant / Disconnected** (Bypassed by GUI in favor of inline router). |
| `core/model_registry.py` | AI Models | `ModelRegistry`, `ModelMetadata`: catalog of known cloud and local model capabilities and fallbacks. | **Dormant / Disconnected** (Independent unit; GUI uses inline model list). |
| `core/plugin_engine.py` | Extensibility / MCP | `RealMCPStdioClient`, `PluginManifestValidator`: stdio-based MCP JSON-RPC 2.0 client and plugin schema validator. | **Active / Needs Header Framing** (Assumes newline JSON; breaks on `Content-Length:` headers). |
| `core/source_control.py` | Developer Tools / Git | `GitService`, `GitRepository`: local Git operations (status, diff, stage, commit, log). | **Active & Verified** (Powers `GitSidebarWidget`). |
| `ai/agents/planner.py` | Multi-Agent / DAG | `ExecutionPlan`, `TaskStep`: topological DAG planning, Kahn's algorithm cycle detection, step dispatching. | **Dormant / Disconnected** (Fully tested, but bypassed by GUI). |
| `ai/agents/critic.py` | Multi-Agent / Quality | `AgentCritic`: AST-based syntax analysis, security checks (`eval`, `exec` detection), secret scanning. | **Dormant / Disconnected** (Fully tested, but bypassed by GUI). |
| `ai/agents/orchestrator.py` | Multi-Agent Orchestration | `MultiAgentOrchestrator`: multi-role pipeline (Architect $\rightarrow$ Coder $\rightarrow$ Critic $\rightarrow$ Tester). | **Dormant / Disconnected** (Fully tested, but bypassed by GUI). |
| `workspace/checkpoints.py` | Reliability / Checkpoints | `CheckpointManager`: SHA-256 pre-edit file snapshotting and atomic transactional multi-file rollback. | **Active & Verified** (Used in file edits; exposed in `CheckpointsWidget`). |
| `ai/rag/code_indexer.py` | Semantic Search / RAG | `CodebaseIndexer`: AST-based Python chunking and symbol indexing. | **Active & Verified** (Tested in `test_rag.py`). |
| `plugins/` | Extensibility | `PluginManager`, `HookRegistry`, `PluginSandbox`: lifecycle, hooks, and AST sandbox. | **Partial** (Tested, but not wired into agent tool execution loop). |

---

## 3. Verified Call Graphs & Execution Paths

### 3.1 Active GUI Execution Path (Current State)
1. **Intake:** User submits prompt in `Studio.prompt` $\rightarrow$ `Studio.send_prompt()` (line 5210).
2. **Context Injection:** `Studio.gather_context()` collects active editor buffer and open tabs (line 5238).
3. **Worker Thread Launch:** `Studio.start_ai()` spawns `AIWorker` in a separate `QThread` (line 5250).
4. **Model Cascade:** `AIWorker.run()` invokes `IntelligentModelRouter.get_execution_plan()` (line 440) cascading:
   `Google Gemini` $\rightarrow$ `NavyAI` $\rightarrow$ `Local Ollama` $\rightarrow$ `Custom OpenAI Endpoint`.
5. **Streaming Tokens:** Worker emits `chunk_received` signals to `Studio.chat`.
6. **Completion & Tool Extraction:** `AIWorker` emits `finished` $\rightarrow$ `Studio.on_ai_done()` $\rightarrow$ `Studio.handle_agent_tools()` (line 5344).
7. **Tool Extraction:** `AgentToolEngine.extract_tools()` parses XML tags via regex (line 1756).
8. **Tool Execution:** `AgentToolEngine.execute_tool()` dispatches to `WorkspaceGuard`, `ToolGateway`, `CheckpointManager` (line 1522).
9. **Next Step Iteration:** `Studio.handle_agent_tools()` builds feedback and calls `Studio.start_ai(followup_msgs, step + 1)`.

### 3.2 Key Divergences and Architectural Flaws
- **Defect 1 (P0 Context Loss):** At lines 5405–5410 of `local_ai_studio_pro.py`, `followup_msgs` contains only the system prompt and the latest tool output string. The original task objective, user prompt, and multi-step conversation turns are permanently discarded.
- **Defect 2 (P0 Approval Hook Blockage):** In `AgentToolEngine.__init__` (line 1512), `ToolGateway` is instantiated without an `approval_hook`. Any command classified as `HIGH_RISK` by `ToolGateway` (lines 88–97) immediately throws `ToolSecurityError`, causing tool execution failure with no mechanism for user approval.
- **Defect 3 (P1 Regex Tool Reachability):** Handlers for `create_checkpoint`, `rollback_checkpoint`, and `semantic_search` exist in `execute_tool` (lines 1533, 1538, 1588) but are absent from `extract_tools` (lines 1756–1778), rendering them completely unreachable by models.
- **Defect 4 (P1 Disconnected Multi-Agent Core):** `MultiAgentOrchestrator`, `ExecutionPlan`, and `AgentCritic` are operational in `ai/agents/` but never imported or invoked by `local_ai_studio_pro.py`.

---

## 4. Baseline Automated Test Suite Results

On 2026-10-10, the test suite was executed against the project virtual environment (`.venv`):
- **Command:** `.venv\Scripts\python.exe -m pytest -v`
- **Result:** **60 passed in 41.78 seconds (100% pass rate, 0 failures, 0 errors)**.

### Detailed Test Distribution:
- `tests/test_agents.py`: 4 tests (Topological sort, DAG cycle detection, AST security critic, multi-agent pipeline).
- `tests/test_debugging.py`: 3 tests (DAP framing, breakpoint registration, stack trace/variables parsing).
- `tests/test_language_services.py`: 4 tests (LSP URI roundtrip, framing, diagnostics dispatch, definition parsing).
- `tests/test_plugins.py`: 3 tests (Hook registry priority, sandbox permissions, plugin manager lifecycle).
- `tests/test_rag.py`: 2 tests (AST Python chunking, codebase indexer search).
- `tests/test_source_control.py`: 4 tests (Git repo detection, status untracked/staging, commit/log, sidebar widget).
- `tests/test_studio.py`: 23 tests (Lexers, diff dialog, intelligent router, branding, DPAPI redaction, tool gateway, task engine, plugin validator, installer worker).
- `tests/test_ui_widgets.py`: 3 tests (Checkpoints widget lifecycle, diagnostics filtering, debug panel state).
- `tests/test_workspace.py`: 4 tests (Checkpoint creation, single file rollback, atomic multi-file rollback, traversal rejection).

---

## 5. Verified Capabilities vs Gaps Summary

| Area | Verified Working | Gaps / Limitations |
| :--- | :--- | :--- |
| **Model Routing** | 4-tier model cascade with live streaming and fallback. | Disconnected from `core/router.py` profiles (SMALL/MEDIUM/LARGE). |
| **Filesystem Safety** | Path canonicalization, traversal defense, pre-edit `.bak` backups. | Patching requires exact literal string matches (no fuzzy whitespace tolerance). |
| **Checkpoints** | SHA-256 pre-edit snapshots, multi-file atomic rollback. | Missing regex extractor patterns for autonomous agent invocation. |
| **Security & Secrets** | Windows DPAPI storage, stdout/stderr secret redaction, blacklist regex. | High-risk commands blocked due to missing approval hook in `ToolGateway`. |
| **Multi-Agent DAG** | DAG scheduler, Kahn's cycle detection, AST critic code review. | Completely disconnected from desktop GUI. |
| **Persistence** | Conversation history saved as JSON files in user profile. | In-flight agent task state is in-memory only; wiped on app restart. |
| **MCP Integration** | JSON-RPC 2.0 stdio client functional. | Missing HTTP header (`Content-Length:`) framing support; client-only. |

---

## 6. Action Plan for Phase One (Gate 2)

With the Phase Zero baseline established and verified against real files and test runs, engineering proceeds immediately to **Gate 2: Repair the Active Agent Execution Loop**:
1. **P0 Fix 1:** Preserve conversation history, original user goal, and multi-turn tool interaction history in `Studio.handle_agent_tools` (`local_ai_studio_pro.py`).
2. **P0 Fix 2:** Connect `ToolGateway` approval hook to Qt user confirmation dialog in `AgentToolEngine` (`local_ai_studio_pro.py`).
3. **P1 Fix 3:** Add regex extraction patterns for `create_checkpoint`, `rollback_checkpoint`, and `semantic_search` in `AgentToolEngine.extract_tools`.
4. **Regression Tests:** Write comprehensive unit and integration tests verifying context survival across multi-turn loops, approval handling, and regex tool reachability.
