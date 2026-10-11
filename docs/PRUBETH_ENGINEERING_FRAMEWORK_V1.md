# PRUBETH Engineering Framework v1
### Operational Governance, Architectural Integrity, and Design System Foundations

---

## 1. The Core Golden Rule
> **"Finalize the architecture boundaries and the design-system foundations before building dozens of screens. Then develop one complete, representative workflow, validate it end-to-end, and extend the same architecture and visual language across the product."**

Building screens independently without unified foundations leads to fragmentation, drift, and massive rework. PRUBETH enforces a single source of truth for architectural boundaries and design tokens before extending capabilities.

---

## 2. The 7 Governance Pillars

### Pillar 1: Product and Requirements Governance
* **Scope Definition:** Every initiative starts with a bounded problem statement (e.g. SWE-bench style issue resolution, multi-file Composer editing).
* **User Stories & Personas:** Define who interacts with the system (e.g., *Systems Architect* in Mission Control vs. *Focused Coder* in Editor View).
* **Measurable Acceptance Criteria:** Every feature must define verifiable pass criteria (e.g., < 10ms typing latency, 100% test pass rate, 0 path traversal vulnerabilities).

### Pillar 2: Architecture Governance
* **C4 Architecture Model:**
  * *Context:* PRUBETH IDE interacting with developer, local CUDA Ollama, and cloud frontier models.
  * *Containers:* Electron Desktop Shell, Monaco / QScintilla Editor Canvas, Python `horizon_engine` runtime, PTY terminal.
  * *Components:* Mission Control DAG Scheduler, Artifact Engine, Worktree Sandbox Manager, Skills Progressive Disclosure Engine.
  * *Code:* Modular classes in `horizon_engine/` with explicit type annotations.
* **Module Contracts:** Strict dependency direction: UI widgets consume `horizon_engine` and `code_oss` APIs; engine modules never depend on UI presentation layers.
* **Architecture Decision Records (ADRs):** Lightweight records in `docs/adr/` documenting context, decision, consequences, and alternatives.

### Pillar 3: Experience Design Governance
* **Dual-Surface Information Architecture:**
  * *Synchronous Surface (Editor View):* Low-latency, distraction-free manual code editing, tab autocomplete, and diagnostics.
  * *Asynchronous Surface (Mission Control):* Macro dashboard for parallel 30-to-60 minute background objectives, stage-gate review, and mid-flight steering.
* **Interaction Standards:** Keyboard-first efficiency (`Ctrl+Shift+M`, `Ctrl+Shift+A`, `Ctrl+I`, `Ctrl+K`), non-blocking background task execution, and clear visual state feedback.
* **Usability Criteria:** Zero modal lockups; long-running tasks stream live ReAct traces without freezing the UI thread.

### Pillar 4: Design System Governance
* **Single Source of Truth:** Centralized design tokens codified in `ui/design_system.py`.
* **Color Palette (Obsidian Slate):**
  * `CANVAS_BG`: `#0B0D13` (deep obsidian)
  * `SURFACE_PANEL`: `#141824` / `#161722` (slate elevation)
  * `ACCENT_CYAN`: `#00F0FF` (horizon electric cyan)
  * `SUCCESS_GREEN`: `#00FF88` (verified evidence pass)
  * `WARNING_AMBER`: `#FFCC00` (stage-gate review required)
  * `DANGER_RED`: `#FF4466` (execution error / abort)
* **Visual Regression Standards:** Verifiable screenshot artifacts captured via headless verification before merging UI updates.

### Pillar 5: Incremental Delivery
* **Vertical Feature Slices:** Build thin, complete end-to-end slices (Plan ➔ UI ➔ Engine ➔ Tests) rather than wide, incomplete horizontal layers.
* **Agile Iteration:** Short cycles delivering verified working increments backed by automated test suites.

### Pillar 6: Quality and Security Engineering
* **Stage-Gate Process (PRINCE2):**
  $$\text{Plan (Initiation)} \longrightarrow \text{Review (Stage-Gate)} \longrightarrow \text{Execute (Sandbox)} \longrightarrow \text{Verify (Acceptance)}$$
* **Security Controls (`WorkspaceGuard`):** Path traversal blocking, canonical root enforcement, and hardware-encrypted credential vaults (Windows DPAPI / AES Fernet).
* **Performance Budgets:**
  * Typing Response: Sub-millisecond buffer latency via Piece Tables.
  * Memory Overhead: Skills progressive disclosure < 250 tokens in base prompt.
  * Test Suite Execution: Full test pass in < 15 seconds.

### Pillar 7: Release and Operations Governance
* **Packaging Standards:** Clean standalone executables and portable zips built via Inno Setup and PyInstaller.
* **Zero Telemetry:** Opt-out by default; zero background data harvesting.
* **Disaster Recovery:** Multi-file transactional checkpoints with atomic two-phase rollback.

---

## 3. Representative End-to-End Reference Workflow

The canonical workflow demonstrating all 7 pillars in action:

1. **Initiate Mission:** Developer spawns task in Mission Control (*Pillars 1 & 3*).
2. **Draft Plan:** Engine generates `implementation_plan.md` artifact (*Pillar 6 - PRINCE2*).
3. **Stage-Gate Review:** Developer inspects plan and leaves inline comment directives (*Pillars 2 & 3*).
4. **Isolated Execution:** Subagent executes modifications in shadow Git worktree (*Pillars 5 & 6*).
5. **Autonomous Verification:** Test suite & browser verifier execute evidence checks (*Pillars 4 & 6*).
6. **Merge & Complete:** Unified diff is reviewed and committed cleanly (*Pillar 7*).
