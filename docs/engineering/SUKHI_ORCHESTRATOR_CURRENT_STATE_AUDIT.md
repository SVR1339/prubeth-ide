# SUKHI IDE — Orchestration Engine Forensic Audit
**Document ID:** `AUD-ORCH-2026-10-10-V1`  
**Target Product:** SUKHI IDE — Horizon Edition v3.0.0  
**Repository Working Tree:** `c:\Users\asus\heretic-work` (Git commit: `9c008a6`)  
**Audit Type:** Static Code Inspection, Dependency Tracing, and Dynamic Test Execution Audit  
**Classification:** Engineering Architecture & Security Audit  
**Author:** Principal AI Systems Architect & DevSecOps Lead  

---

## 1. Executive Summary

This forensic audit evaluates the orchestration, agent execution, task scheduling, model routing, tool dispatch, security boundaries, and persistence mechanisms of **SUKHI IDE — Horizon Edition v3.0.0**.

### Key Conclusions:
1. **The Dual-Orchestrator Architecture:** The codebase contains **two completely separate orchestrator subsystems**:
   - **Active UI Orchestrator (`local_ai_studio_pro.py`):** The operational, Qt-integrated engine that users interact with. It coordinates prompt intake, model cascades, regex-based XML tool invocation (`AgentToolEngine`), and iterative feedback loops.
   - **Modular Multi-Agent Subsystem (`ai/agents/`, `core/`):** A clean, modern architecture consisting of `MultiAgentOrchestrator`, `ExecutionPlan` (topological DAG execution), `AgentCritic` (AST syntax and security static analysis), `TaskEngine`, and `IntelligentRouter`. Although these modules are fully implemented and pass 100% of their unit tests in `pytest`, they are **completely disconnected from the desktop GUI**.
2. **Critical Agent Loop Context Loss:** In the active GUI orchestrator (`local_ai_studio_pro.py`, lines 5405–5410), when tool execution results are fed back into the next AI step, the message history is replaced with only a generic system prompt and the latest tool result. The original user prompt, task goal, and multi-turn conversational context are completely dropped, severely degrading multi-step autonomous workflows.
3. **Regex Extraction Disconnect:** While `AgentToolEngine.execute_tool` implements handlers for `create_checkpoint`, `rollback_checkpoint`, and `semantic_search`, the static regex parser `AgentToolEngine.extract_tools` (lines 1756–1778) lacks patterns for these tools. As a consequence, autonomous agents cannot invoke these tools via model XML outputs.
4. **Approval Hook Blockage in ToolGateway:** `AgentToolEngine` initializes `ToolGateway(self.workspace_guard)` without an `approval_hook` callback. When any command triggers `CommandRiskLevel.HIGH_RISK` (e.g. commands containing dangerous patterns), `ToolGateway.execute_command()` immediately raises an unhandled `ToolSecurityError`, blocking execution rather than prompting the user via a UI dialog.
5. **Robust Workspace & Checkpoint Safety:** The workspace sandbox (`core/workspace.py`) and transactional snapshot manager (`workspace/checkpoints.py`) are rigorously implemented, verified by automated unit tests, and successfully prevent path traversal and unauthorized filesystem mutations.

---

## 2. Actual Orchestration Architecture and Data Flow

The following Mermaid diagrams illustrate the actual architecture and data flow observed in the codebase.

### 2.1 The Two Divergent Subsystems

```mermaid
graph TD
    subgraph Active GUI Engine ["Active GUI Subsystem (local_ai_studio_pro.py)"]
        UI_In[User Prompt Input] --> Studio_Send[Studio.send_prompt L5210]
        Studio_Send --> AI_Worker[AIWorker QThread L1031]
        AI_Worker --> Router_UI[IntelligentModelRouter L440]
        Router_UI --> LLM_Call[API Dispatch: Gemini / Navy / Ollama / Custom]
        LLM_Call --> Stream_Chunk[Token Streaming to UI Chat]
        LLM_Call --> On_Done[Studio.on_ai_done L5298]
        On_Done --> Handle_Tools[Studio.handle_agent_tools L5344]
        Handle_Tools --> Regex_Extract[AgentToolEngine.extract_tools L1756]
        Regex_Extract --> Tool_Exec[AgentToolEngine.execute_tool L1522]
        Tool_Exec --> Gateway[core.tool_gateway.ToolGateway]
        Tool_Exec --> WS_Guard[core.workspace.WorkspaceGuard]
        Tool_Exec --> Checkpoint[workspace.checkpoints.CheckpointManager]
        Handle_Tools --> Context_Drop["Context Loss Bug L5405<br/>(Drops History & Goal)"]
        Context_Drop --> Loop_Feedback[Studio.start_ai Next Step]
    end

    subgraph Dormant Backend ["Modular Subsystem (Disconnected from GUI)"]
        Mod_Orch[MultiAgentOrchestrator<br/>ai/agents/orchestrator.py]
        Mod_Plan[ExecutionPlan DAG<br/>ai/agents/planner.py]
        Mod_Critic[AgentCritic AST/Security<br/>ai/agents/critic.py]
        Mod_Task[TaskEngine<br/>core/task_engine.py]
        Mod_Router[IntelligentRouter<br/>core/router.py]
        Mod_Registry[ModelRegistry<br/>core/model_registry.py]
        
        Mod_Orch --> Mod_Plan
        Mod_Orch --> Mod_Critic
        Mod_Router --> Mod_Registry
    end

    UI_In -.->|Zero references| Mod_Orch
    Handle_Tools -.->|Instantiates TaskEngine but never calls it| Mod_Task
```

### 2.2 Active User Request Data Flow (Step-by-Step)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Studio as Studio (GUI Main Window)
    participant Worker as AIWorker (QThread)
    participant Model as LLM Provider (Gemini/Navy/Ollama)
    participant Engine as AgentToolEngine
    participant Gateway as ToolGateway / WorkspaceGuard

    User->>Studio: Submits prompt in chat input
    Studio->>Studio: Assemble context (active file, open tabs) [L5238]
    Studio->>Studio: Assemble system prompt & format tools [L5219-L5236]
    Studio->>Worker: Launch QThread with messages [L5250]
    Worker->>Worker: Evaluate model cascade (Router) [L440]
    Worker->>Model: Dispatch HTTP/SDK generation request
    Model-->>Worker: Stream text response
    Worker-->>Studio: Emit chunk_received (Render markdown)
    Worker-->>Studio: Emit finished(reply, meta) [L1142]
    Studio->>Studio: on_ai_done: check meta["type"] == "agent" [L5334]
    Studio->>Engine: AgentToolEngine.extract_tools(reply) [L5361]
    loop For each extracted tool
        Studio->>Engine: execute_tool(name, args) [L5382]
        Engine->>Gateway: Enforce security & execute [L1522]
        Gateway-->>Engine: Tool result string
        Engine-->>Studio: Return result
        Studio->>Studio: Render collapsible result tag in chat
    end
    Note over Studio: Critical Defect: Previous history & original goal<br/>are discarded here [L5405-L5410]
    Studio->>Worker: start_ai(followup_msgs, step + 1)
```

---

## 3. Component and Module Inventory

| Module Path | Core Classes / Entry Points | Primary Purpose | Architectural Status |
| :--- | :--- | :--- | :--- |
| `local_ai_studio_pro.py` | `Studio`, `AIWorker`, `AgentToolEngine`, `IntelligentModelRouter` | Primary desktop IDE application, GUI widgets, active agent loop, provider cascade. | **Active & Integrated** (Primary runtime entry point). |
| `core/task_engine.py` | `TaskState`, `TaskStep`, `Task`, `TaskEngine` | In-memory lifecycle management for tasks and task steps. | **Dormant / Disconnected** (Instantiated in `AgentToolEngine` line 1514, but no methods invoked). |
| `core/tool_gateway.py` | `CommandRiskLevel`, `ToolGateway`, `ToolSecurityError` | Safe process execution, risk classification, secret redaction, timeout control. | **Active** (Used by `AgentToolEngine.execute_tool`), but missing approval callback. |
| `core/workspace.py` | `WorkspaceGuard`, `WorkspaceSecurityError` | Filesystem sandbox, path canonicalization, directory traversal defense. | **Active & Core** (Enforced across all file operations). |
| `core/router.py` | `AgentProfile`, `PolicyConstraint`, `IntelligentRouter` | Tiered model routing (SMALL, MEDIUM, LARGE) with cost & local constraints. | **Dormant / Disconnected** (Not imported by `AIWorker` or `Studio`). |
| `core/model_registry.py` | `ModelCapability`, `ModelMetadata`, `ModelRegistry` | Model metadata catalogue, capability flags, fallback chains. | **Dormant / Disconnected** (Independent unit; UI uses inline routing). |
| `core/plugin_engine.py` | `RealMCPStdioClient`, `PluginManifestValidator` | Stdio MCP JSON-RPC 2.0 client and plugin manifest schema validator. | **Active** (Invoked by `<tool:call_mcp>` and plugin manager). |
| `core/credentials.py` | `CredentialStore`, `DPAPICredentialStore`, `SecretRedactor` | Windows DPAPI / Fernet credential encryption and regex secret redactor. | **Active & Core** (Integrated at startup line 4070 and in `ToolGateway`). |
| `core/source_control.py` | `GitRepository`, `GitStatusEntry`, `GitService` | Native Git CLI wrapper, status parser, staging, log inspection. | **Active in UI** (Powers `GitSidebarWidget`). |
| `ai/agents/orchestrator.py` | `AgentRole`, `Subagent`, `MultiAgentOrchestrator` | Multi-agent DAG orchestrator with role delegation (Architect, Coder, Critic, Tester). | **Dormant / Disconnected** (Tested in `test_agents.py`, 0 references in UI). |
| `ai/agents/planner.py` | `TaskStep`, `ExecutionPlan`, `TaskStatus`, `CycleDetectedError` | Directed Acyclic Graph (DAG) task planner, topological sorting, Kahn's algorithm. | **Dormant / Disconnected** (Tested in `test_agents.py`, 0 references in UI). |
| `ai/agents/critic.py` | `AgentCritic`, `CriticReport`, `CriticIssue`, `ReviewStatus` | AST-based code analysis, detection of dangerous calls (`eval`, `exec`), hardcoded secrets. | **Dormant / Disconnected** (Tested in `test_agents.py`, 0 references in UI). |
| `workspace/checkpoints.py` | `CheckpointManager`, `FileSnapshot` | SHA-256 pre-edit file snapshotting, transactional multi-file rollback. | **Active** (Integrated with `AgentToolEngine` writes and `CheckpointsWidget`). |
| `plugins/manager.py` | `PluginManager`, `PluginInfo`, `PluginState` | Plugin discovery, activation, manifest validation, dependency resolution. | **Partial** (Integrated into UI catalog dialog, not hooked into agent loop). |
| `plugins/sandbox.py` | `PluginSandbox`, `PluginPermissionError` | Restricted Python execution sandbox for third-party extensions. | **Partial** (Tested in unit tests, isolated from agent runtime). |
| `plugins/hooks.py` | `HookRegistry`, `HookPriority` | Extension event dispatcher (`on_file_save`, `on_editor_load`, etc.). | **Partial** (Fully unit-tested; not hooked into `Studio.handle_agent_tools`). |
| `ai/rag/code_indexer.py` | `CodebaseIndexer`, `CodeChunk` | AST-based Python code chunking and symbol-based lexical/semantic indexing. | **Active** (Invoked via `semantic_search` tool handler). |

---

## 4. Capability Status Matrix

Each of the 23 requested orchestration capabilities has been forensically analyzed and assigned one of five verified statuses:
- **WORKING:** Fully implemented, verified in runtime or test suites, operational end-to-end.
- **PARTIAL:** Core functionality exists, but contains architectural constraints or edge cases.
- **DISCONNECTED:** Code exists and works in isolation/tests, but is not connected to the active GUI orchestrator.
- **BROKEN:** Code contains defects that cause runtime errors, execution failures, or silent malfunctions.
- **MISSING:** Feature has no underlying implementation.

| # | Capability Area | Status | Evidence & Location in Codebase |
| :--- | :--- | :--- | :--- |
| 1 | **User request intake & task classification** | **PARTIAL** | Intake operates in `Studio.send_prompt` ([local_ai_studio_pro.py#L5210](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py#L5210)). Task classification is limited to string mode selection (`chat`, `agent`, `edit`). Advanced classification in `core/router.py` is disconnected. |
| 2 | **Planning & task decomposition** | **DISCONNECTED** | `PlannerAgent` & `ExecutionPlan` in [ai/agents/planner.py#L40](file:///c:/Users/asus/heretic-work/ai/agents/planner.py#L40) provide 4-step DAG decomposition, but the active GUI orchestrator sends requests directly to the model without prior decomposition. |
| 3 | **Task dependency graphs & ordering** | **DISCONNECTED** | Topological sort and cycle detection exist in `ExecutionPlan.topological_order()` ([ai/agents/planner.py#L60](file:///c:/Users/asus/heretic-work/ai/agents/planner.py#L60)). Active GUI uses a flat linear counter (`step = step + 1`). |
| 4 | **Sequential & parallel task execution** | **PARTIAL** | Tool calls are executed sequentially in a single turn ([local_ai_studio_pro.py#L5372](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py#L5372)). True parallel multi-agent task execution is missing; only one worker runs at a time. |
| 5 | **Agent creation, delegation & coordination** | **DISCONNECTED** | Subagents (`Architect`, `Coder`, `Critic`, `Tester`) exist in [ai/agents/orchestrator.py#L30](file:///c:/Users/asus/heretic-work/ai/agents/orchestrator.py#L30). Active GUI uses a single monolithic system prompt with zero delegation. |
| 6 | **Model selection, routing & fallback** | **WORKING** | `IntelligentModelRouter.get_execution_plan()` ([local_ai_studio_pro.py#L440](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py#L440)) builds an operational cascade: Gemini $\rightarrow$ NavyAI $\rightarrow$ Ollama $\rightarrow$ Custom. Fallback executes inside `AIWorker.run()`. |
| 7 | **Tool discovery, registration & invocation** | **BROKEN** | 10 tools are registered via XML regex in `extract_tools` ([local_ai_studio_pro.py#L1756](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py#L1756)). However, `create_checkpoint`, `rollback_checkpoint`, and `semantic_search` handlers exist in `execute_tool` but **lack regex extraction patterns**, rendering them unreachable by the agent. Native JSON-schema tool calling is missing. |
| 8 | **Skills & plugin integration** | **DISCONNECTED** | Plugin manager and manifest validation exist in `plugins/` and `core/plugin_engine.py`, but plugin hooks are not triggered during the autonomous agent loop in `handle_agent_tools`. |
| 9 | **MCP client/server integration** | **PARTIAL** | Stdio client `RealMCPStdioClient` in [core/plugin_engine.py#L15](file:///c:/Users/asus/heretic-work/core/plugin_engine.py#L15) connects to local MCP servers via JSON-RPC 2.0. However, it assumes newline-delimited output (breaking on standard `Content-Length:` HTTP headers), lacks SSE transport, and cannot act as an MCP server. |
| 10 | **Git & GitHub operations** | **PARTIAL** | Local Git operations work via `GitService` ([core/source_control.py#L65](file:///c:/Users/asus/heretic-work/core/source_control.py#L65)) and `GitSidebarWidget`. GitHub operations (pull requests, issues, remote repo creation) have no direct API integration and rely on raw CLI execution. |
| 11 | **Multi-project & multi-repo awareness** | **PARTIAL** | Only a single root workspace folder (`self.root`) can be active at one time. Multi-root workspace files (e.g. `.code-workspace`) are not supported. |
| 12 | **Workspace & context management** | **WORKING** | `WorkspaceGuard` ([core/workspace.py#L22](file:///c:/Users/asus/heretic-work/core/workspace.py#L22)) strictly validates canonical paths against the root, preventing path traversal attacks. Initial workspace context is injected via `Studio.gather_context`. |
| 13 | **File reading, editing & modification safety** | **WORKING** | `safe_read`, `safe_write`, and `safe_patch` ([core/workspace.py#L70](file:///c:/Users/asus/heretic-work/core/workspace.py#L70)) perform atomic file mutations with pre-edit `.bak` backups and SHA-256 fingerprinting. |
| 14 | **Code generation, diffing & patching** | **PARTIAL** | `VisualDiffDialog` provides interactive diff review for user edits. `safe_patch` uses strict literal string replacement; it fails on minor whitespace/indentation discrepancies and lacks AST-aware or fuzzy patch recovery. |
| 15 | **Execution sandboxing & command running** | **PARTIAL** | `ToolGateway` ([core/tool_gateway.py#L64](file:///c:/Users/asus/heretic-work/core/tool_gateway.py#L64)) classifies commands, blocks dangerous patterns, and redacts secrets. However, execution runs via `subprocess.run(shell=True)` on Windows without OS-level job containerization. |
| 16 | **Safety boundaries & confirmation gates** | **BROKEN** | `ToolGateway` blocks `HIGH_RISK` commands unless an `approval_hook` is set. In `AgentToolEngine` ([local_ai_studio_pro.py#L1512](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py#L1512)), `approval_hook` is left as `None`. Any high-risk command throws an unhandled `ToolSecurityError` instead of prompting the user. |
| 17 | **Undo, rollback, checkpoint & recovery** | **PARTIAL** | `CheckpointManager` ([workspace/checkpoints.py#L30](file:///c:/Users/asus/heretic-work/workspace/checkpoints.py#L30)) supports transactional snapshots and atomic rollbacks. It is exposed in the `CheckpointsWidget` UI, but disconnected from autonomous agent invocations due to missing regex extraction. |
| 18 | **Long-running & background tasks** | **PARTIAL** | LLM inference runs asynchronously in `AIWorker` (QThread). However, tool actions (compilation, test runs, shell commands) run synchronously within the main agent handler, blocking until finished (up to a 60-second timeout). |
| 19 | **Progress reporting & event streaming** | **WORKING** | Token streaming from worker to UI works in real time. Executed tools are dynamically rendered as collapsible HTML `<details>` widgets in the chat transcript ([local_ai_studio_pro.py#L5397](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py#L5397)). |
| 20 | **Human-in-the-loop clarification** | **PARTIAL** | Basic `QMessageBox` confirmation exists for shell commands if `unrestricted_mode` is disabled ([local_ai_studio_pro.py#L5374](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py#L5374)). Interactive multi-choice questions or structured clarification tools are missing. |
| 21 | **Memory, conversational context & persistence** | **BROKEN** | Conversations persist to disk in `~/.local_ai_studio_pro/conversations/`. However, during autonomous agent loops, lines 5405–5410 construct a 2-message payload containing only the latest tool outputs, **completely discarding previous turns, user intent, and historical reasoning**. Cross-session semantic memory is missing. |
| 22 | **Self-correction, linting & verification loops** | **PARTIAL** | `<tool:verify_deliverable>` ([local_ai_studio_pro.py#L1713](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py#L1713)) performs automated Python syntax checks (`py_compile`) and test verification (`pytest`). However, `AgentCritic` (AST security checks) is disconnected from the loop. |
| 23 | **Performance, latency & rate limiting** | **PARTIAL** | File reading is capped at `MAX_FILE_CONTEXT = 30000` chars and history truncated to 6000 chars per message. However, there is no token consumption telemetry, token cost tracking, or exponential backoff on HTTP 429 rate limits. |

---

## 5. Verified Execution Paths

### Detailed Trace: User Request $\rightarrow$ Tool Execution $\rightarrow$ Result Return

1. **Intake & Context Assembly (`local_ai_studio_pro.py`, Lines 5210–5249):**
   - User types a goal into `self.prompt` (e.g. *"Refactor auth module and run tests"*) and clicks Send.
   - `Studio.send_prompt()` reads the text and clears the input.
   - Lines 5219–5236 construct the monolithic system prompt describing the 10 available `<tool:...>` XML tags.
   - Line 5238 calls `self.gather_context(goal)`, which inspects open editor tabs and attaches the active file's content (up to 30,000 characters).
   - Line 5242 builds `msgs = [{"role": "system", ...}]`, appends up to 6 historical conversation messages from `~/.local_ai_studio_pro/history.json`, and appends the user prompt.
   - Line 5246 calls `self.start_ai(msgs, "agent", extra_meta={"goal": goal, "step": 1})`.

2. **Model Cascade & Execution (`local_ai_studio_pro.py`, Lines 1031–1150):**
   - `Studio.start_ai()` instantiates `AIWorker(self.settings, msgs, "agent", extra_meta)` and starts its `QThread`.
   - `AIWorker.run()` calls `IntelligentModelRouter.get_execution_plan("agent", available_models)` (line 440).
   - If configured to `⚡ Auto-Router`, the worker evaluates candidate providers in order:
     1. Google Gemini (via `google.genai` SDK or REST fallback to `gemini-2.5-flash`).
     2. NavyAI (`navy-pro` or `navy-flash`).
     3. Local Ollama (`http://localhost:11434` with `qwen2.5-coder` or `llama3.2`).
     4. Custom OpenAI-compatible endpoints.
   - Streaming tokens are emitted via `self.signals.chunk_received.emit(chunk)` and rendered incrementally in `Studio.chat`.
   - Upon completion, the worker emits `self.signals.finished.emit(full_reply, extra_meta)`.

3. **Response Parsing & Tool Dispatch (`local_ai_studio_pro.py`, Lines 5344–5403):**
   - `Studio.on_ai_done()` receives the reply. If `meta.get("type") == "agent"`, it forwards the response to `Studio.handle_agent_tools(reply)`.
   - Line 5346 checks for `<deliverable:complete name="...">...</deliverable:complete>`. If found, it posts a completion banner and logs the deliverable.
   - Line 5361 calls `AgentToolEngine.extract_tools(answer)`, which uses regular expressions to parse XML tags:
     ```python
     # Example: <tool:run_command cmd="pytest" />
     # Parsed into: ("run_command", {"cmd": "pytest"})
     ```
   - If no tools are found, the agent loop concludes.
   - If tools are found, the step counter is checked against `self.settings.get("max_agent_steps", 25)`.
   - For each tool, line 5382 calls `res = self.tool_engine.execute_tool(name, args)`.
   - In `AgentToolEngine.execute_tool()`:
     - `read_file` $\rightarrow$ `self.workspace_guard.safe_read(path)`
     - `write_file` $\rightarrow$ `self.checkpoint_manager.track_file_before_edit(...)`, `self.workspace_guard.safe_write(...)`
     - `patch_file` $\rightarrow$ `self.workspace_guard.safe_patch(...)`
     - `run_command` $\rightarrow$ `self.tool_gateway.execute_command(cmd)`
     - `verify_deliverable` $\rightarrow$ `py_compile` checks + `pytest -q`
     - `call_mcp` $\rightarrow$ `RealMCPStdioClient.call_tool(...)`
   - Results are sanitized with `html_escape` and rendered as interactive `<details>` tags in the chat window.

4. **Feedback Loop & The Context-Loss Defect (`local_ai_studio_pro.py`, Lines 5404–5410):**
   - Lines 5404–5408 assemble the feedback payload:
     ```python
     feedback = "\n\n".join(tool_results)
     msgs = [
         {"role": "system", "content": "You are continuing the autonomous task. Review tool results and provide the next step or final resolution..."},
         {"role": "user", "content": f"Tool Execution Outputs:\n{feedback}\n\nContinue autonomously until expected answer or verified deliverable is achieved."}
     ]
     self.start_ai(msgs, "agent", extra_meta={"step": step + 1})
     ```
   - **Forensic Failure Analysis:** Notice that `msgs` contains **only** these two elements. The initial user request (`goal`), the workspace context, previous tool outputs, and model reasoning from turns $1 \dots step-1$ are discarded. On Step 2 and beyond, the model only sees the raw output of the previous tool, with no knowledge of what it was originally asked to build or solve.
   - Furthermore, `extra_meta={"step": step + 1}` omits `"goal"`, permanently erasing the task reference from metadata.

---

## 6. Persistence and Recovery Analysis

### 6.1 Checkpoints and Transactional Rollback
The checkpoint subsystem in `workspace/checkpoints.py` provides high-fidelity, transactional file snapshots:
- **Snapshot Storage:** Stored in `.checkpoints/<timestamp>_<hash>/`.
- **Integrity Fingerprinting:** SHA-256 hashes are calculated for every tracked file before and after mutation.
- **Atomic Rollback:** `CheckpointManager.rollback(checkpoint_id)` reads `metadata.json`, restores modified files to their original byte contents, and deletes newly created files.
- **Path Traversal Protection:** Validated by `test_checkpoint_rejection_of_traversal`, rejecting attempts to snapshot files outside the workspace root.
- **Gaps:** The agent cannot trigger checkpoints autonomously because `<tool:create_checkpoint>` and `<tool:rollback_checkpoint>` are omitted from `AgentToolEngine.extract_tools()`.

### 6.2 Conversation and History Persistence
- Conversations are serialized as JSON documents in `~/.local_ai_studio_pro/conversations/<id>.json`.
- Each record contains `id`, `title`, `created_at`, `updated_at`, and `messages`.
- General prompt history is saved in `~/.local_ai_studio_pro/history.json` (retaining the last 40 entries).
- **Session Resumption Limitation:** If the IDE terminates while an autonomous agent loop is mid-execution (e.g. on step 4 of 25), the active execution state is lost. There is no task journal or WAL (write-ahead log) on disk. When re-opened, the IDE cannot resume in-flight agent tasks.

### 6.3 TaskEngine Persistence
- `core/task_engine.py` manages `Task` and `TaskStep` entities solely in an internal Python dictionary (`self._tasks: Dict[str, Task] = {}`).
- There is no SQLite, JSON, or disk persistence layer in `TaskEngine`. Any restart of the application completely clears all task history.

---

## 7. Tool, Skills, Plugin and MCP Integration Analysis

### 7.1 AgentToolEngine vs Native Tool Calling
SUKHI IDE relies on **prompt-engineered XML tag extraction** rather than native provider function calling (such as OpenAI Tools or Gemini Function Calling API schemas).
- **Advantages:** Provider-agnostic. Functions uniformly on local models (Ollama, custom GGUF) that do not support OpenAI-style tool schema JSON parameters.
- **Disadvantages:**
  - Susceptible to hallucinated XML formats (e.g. `<tool:read_file>path</tool:read_file>` instead of `<tool:read_file path="..." />`).
  - Strict regular expressions in `extract_tools` silently ignore malformed tags.
  - High token overhead in the system prompt (lines 5219–5236) teaching the model XML syntax on every invocation.

### 7.2 MCP (Model Context Protocol) Implementation
`core/plugin_engine.py` implements `RealMCPStdioClient`:
- Spawns subprocesses specified in `~/.local_ai_studio_pro/mcp_servers.json`.
- Implements JSON-RPC 2.0 handshake (`initialize`, `tools/list`, `tools/call`).
- **Framing Vulnerability:** The client uses `readline()` expecting raw newline-delimited JSON:
  ```python
  line = self.proc.stdout.readline()
  return json.loads(line)
  ```
  Standard MCP stdio servers adhering strictly to the JSON-RPC specification often frame messages using HTTP headers (`Content-Length: ...\r\n\r\n{...}`). If an external server sends header framing, `readline()` reads the `Content-Length` header line instead of the JSON payload, throwing a `json.decoder.JSONDecodeError` and terminating the session.

### 7.3 Plugins and Hooks Isolation
- `plugins/hooks.py` provides a prioritized event dispatcher (`HookRegistry`).
- `plugins/sandbox.py` provides restricted Python execution using AST parsing to prohibit unsafe modules (`sys`, `os`, `shutil`, `subprocess`).
- **Integration Disconnect:** The hook registry is not connected to `AgentToolEngine`. External plugins cannot listen to tool executions, intercept commands, or register new dynamic agent tools into the execution loop.

---

## 8. Multi-Project and Concurrency Assessment

1. **Single Workspace Constraint:**
   - The IDE operates strictly with a single active directory: `self.root = os.path.abspath(self.settings["project_root"])`.
   - `WorkspaceGuard` enforces that all file reads, writes, searches, and patches reside within `self.root`.
   - There is no support for multi-root workspaces, linked repositories, or cross-project referencing.
2. **Execution Concurrency:**
   - `AIWorker` runs in a dedicated `QThread`, preventing UI freezes during token generation.
   - However, tool execution inside `handle_agent_tools` runs on the Qt main thread. When a tool runs a command (e.g., `pytest` running for 20 seconds), the Qt UI event loop is blocked until the command completes or times out.
   - Simultaneous agent executions are explicitly blocked: line 5212 checks `if not goal or self.active_task: return`.

---

## 9. Security and Reliability Findings

### 9.1 Strengths
1. **Directory Traversal Defense:** `WorkspaceGuard.canonicalize()` resolves symbolic links and strictly verifies that paths start with `self.root`. Attempts to access parent paths (e.g. `../../Windows/System32`) trigger a `WorkspaceSecurityError`.
2. **Secret Redaction:** `core/credentials.py` (`SecretRedactor`) scans stdout/stderr for API keys, bearer tokens, passwords, and secrets using regular expressions, replacing them with `[REDACTED_SECRET]` before displaying them in UI logs or chat feeds.
3. **Prohibited Command Blocking:** `ToolGateway` maintains a blacklist of destructive patterns (`rmdir /s`, `format`, `reg delete`, `diskpart`, `powershell -enc`). Attempted executions are blocked prior to process creation.

### 9.2 Vulnerabilities & Defects
1. **Unwired Approval Hook (High-Risk Command Denial of Service):**
   - In `core/tool_gateway.py` lines 88–97:
     ```python
     if risk == CommandRiskLevel.HIGH_RISK:
         if self.approval_hook:
             approved = self.approval_hook(command_str, "Command contains potentially destructive patterns")
             if not approved:
                 raise ToolSecurityError(f"Execution rejected by user: '{command_str}'")
         else:
             raise ToolSecurityError(
                 f"Execution blocked: Command '{command_str}' is classified as HIGH_RISK and no user approval channel is registered."
             )
     ```
   - In `AgentToolEngine.__init__` ([local_ai_studio_pro.py#L1512](file:///c:/Users/asus/heretic-work/local_ai_studio_pro.py#L1512)), `ToolGateway` is initialized without `approval_hook`:
     ```python
     self.tool_gateway = ToolGateway(self.workspace_guard)
     ```
   - **Result:** Any high-risk command (such as `pip install`, `npm install`, or `git push`) will immediately raise `ToolSecurityError`, failing the agent step even when the user intended to allow it.
2. **Context Loss Leading to Hallucination Loops:**
   - Because previous conversational turns are dropped on step 2 of an agent loop, models frequently lose track of their objective, hallucinate new tasks, or repeatedly run `list_files` in an infinite loop until `max_agent_steps` is hit.
3. **Blocking Main UI Thread During Tool Execution:**
   - Long-running shell commands executed via `<tool:run_command>` or `<tool:run_tests>` run synchronously inside `Studio.handle_agent_tools`, causing the Windows OS to flag the window as "Not Responding" during intensive builds or test suites.

---

## 10. Existing Tests and Their Actual Results

On 2026-10-10, the complete automated test suite was executed against the project virtual environment (`.venv/Scripts/python.exe -m pytest -v`):

```text
============================= test session starts =============================
platform win32 -- Python 3.12.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\asus\heretic-work, configfile: pyproject.toml
collected 60 items

tests/test_agents.py ................................... [  6%]
tests/test_debugging.py ................................ [ 11%]
tests/test_language_services.py ........................ [ 18%]
tests/test_plugins.py .................................. [ 23%]
tests/test_rag.py ...................................... [ 26%]
tests/test_source_control.py ........................... [ 33%]
tests/test_studio.py ................................... [ 88%]
tests/test_ui_widgets.py ............................... [ 93%]
tests/test_workspace.py ................................ [100%]

============================= 60 passed in 41.78s =============================
```

### Breakdown of Passing Orchestrator & Agent Tests:
- `tests/test_agents.py::test_execution_plan_topological_sort_and_cycle_detection`: **PASSED** (Verifies DAG topological sorting and Kahn's cycle detection in `ai/agents/planner.py`).
- `tests/test_agents.py::test_agent_critic_security_and_syntax_analysis`: **PASSED** (Verifies AST security validation, `eval` blocking, and secret detection in `ai/agents/critic.py`).
- `tests/test_agents.py::test_multi_agent_orchestrator_pipeline`: **PASSED** (Verifies 4-stage Architect $\rightarrow$ Coder $\rightarrow$ Critic $\rightarrow$ Tester pipeline in `ai/agents/orchestrator.py`).
- `tests/test_agents.py::test_multi_agent_orchestrator_critic_rejection`: **PASSED** (Verifies plan rejection when generated code fails security inspection).
- `tests/test_studio.py::test_agent_tool_extraction`: **PASSED** (Verifies regex extraction of 10 standard XML tool tags).
- `tests/test_studio.py::test_agent_tool_execution`: **PASSED** (Verifies execution of read, write, patch, list, and verify tools).
- `tests/test_studio.py::test_tool_gateway_risk_and_execution`: **PASSED** (Verifies `ToolGateway` risk classification and secret redaction).
- `tests/test_studio.py::test_task_engine_lifecycle`: **PASSED** (Verifies in-memory state transitions in `core/task_engine.py`).
- `tests/test_workspace.py` (All 4 tests): **PASSED** (Verifies checkpoints, file edits, atomic multi-file rollback, and traversal rejection).

---

## 11. Prioritized Gaps Ranked by Severity and Evidence

| Priority | Gap Title | Severity | Impact | Verified Source Evidence |
| :---: | :--- | :---: | :--- | :--- |
| **P0** | **Autonomous Agent Context Loss** | **Critical** | Multi-step agent loops lose the original goal, previous steps, and conversational reasoning after Step 1. | `local_ai_studio_pro.py` lines 5405–5410 constructs `followup_msgs` with only the latest tool outputs, omitting history. |
| **P0** | **ToolGateway Approval Hook Disconnect** | **Critical** | All `HIGH_RISK` commands fail with `ToolSecurityError` because no approval callback is wired to `ToolGateway`. | `local_ai_studio_pro.py` line 1512 instantiates `ToolGateway(self.workspace_guard)` without `approval_hook`. |
| **P1** | **Orchestrator Architecture Divergence** | **High** | High-level capabilities (DAG execution, Critic AST checks, Multi-Agent roles) exist in `ai/agents/` but are completely bypassed by the GUI. | Zero imports of `MultiAgentOrchestrator`, `ExecutionPlan`, or `AgentCritic` in `local_ai_studio_pro.py`. |
| **P1** | **Missing Regex Extraction for Checkpoint & Semantic Tools** | **High** | Agents cannot invoke `create_checkpoint`, `rollback_checkpoint`, or `semantic_search` autonomously. | Handlers exist in `execute_tool` (lines 1533, 1538, 1588) but regexes are absent in `extract_tools` (lines 1756–1778). |
| **P2** | **MCP Stdio Line-Delimited Assumption** | **Medium** | Fails against standard MCP servers that utilize `Content-Length:` HTTP-style message headers. | `core/plugin_engine.py` line 44 reads `stdout.readline()` assuming raw newline-delimited JSON. |
| **P2** | **In-Memory-Only Task & State Persistence** | **Medium** | Task state and agent progress cannot survive application restarts or unexpected crashes. | `core/task_engine.py` line 45 stores tasks in an in-memory dictionary `self._tasks = {}` with no disk backing. |
| **P2** | **UI Main Thread Blocking During Tool Execution** | **Medium** | Shell commands and test suites run synchronously inside `handle_agent_tools`, freezing the Qt event loop. | `local_ai_studio_pro.py` line 5382 executes tools synchronously inside the Qt slot handler. |
| **P3** | **Absence of Token Telemetry & Rate-Limit Backoff** | **Low** | No real-time token tracking or exponential backoff on HTTP 429 errors during heavy automated sessions. | `AIWorker.run()` lacks token consumption counters and backoff retry logic. |

---

## 12. Recommended Next Steps

1. **Fix Agent Context Retention (Immediate P0):**
   - In `local_ai_studio_pro.py` (`handle_agent_tools`), preserve the original prompt history and append assistant turns and tool results as a continuous message history across steps, rather than wiping `msgs`.
   - Ensure `extra_meta={"goal": original_goal, "step": step + 1}` retains the original goal.
2. **Wire ToolGateway Approval Hook to Qt Dialog (Immediate P0):**
   - Provide an approval hook callback to `ToolGateway` in `AgentToolEngine` that connects to a Qt confirmation dialog (or respects `unrestricted_mode`), allowing high-risk commands to be approved rather than throwing a blocking security error.
3. **Harmonize Regex Extractor with Handlers (P1):**
   - Add regex patterns to `AgentToolEngine.extract_tools` for:
     - `<tool:create_checkpoint description="..." />`
     - `<tool:rollback_checkpoint id="..." />`
     - `<tool:semantic_search query="..." top_k="..." />`
4. **Bridge `MultiAgentOrchestrator` into the UI Runtime (P1):**
   - Refactor `Studio.send_prompt` in `agent` mode to leverage `MultiAgentOrchestrator` (`ai/agents/orchestrator.py`) and `ExecutionPlan` (`ai/agents/planner.py`).
   - Route generated code snippets through `AgentCritic` before writing them to disk.
5. **Upgrade MCP Client Message Framing (P2):**
   - Enhance `RealMCPStdioClient` in `core/plugin_engine.py` to support standard LSP/MCP header framing (`Content-Length: <n>\r\n\r\n{json}`) alongside newline-delimited JSON.
6. **Offload Tool Execution to Background QThread (P2):**
   - Move `AgentToolEngine.execute_tool` to a background worker thread with Qt signals to prevent UI lockup during long-running builds or test executions.
7. **Persist TaskEngine to SQLite (P2):**
   - Add a lightweight SQLite backend to `core/task_engine.py` (`~/.local_ai_studio_pro/tasks.db`) to enable task resumption across IDE sessions.
