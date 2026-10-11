# ADR-002: Dual-Surface Interaction Architecture (Synchronous vs. Asynchronous)

## Status
Accepted

## Date
2026-10-11

## Context
Traditional AI code assistants force human developers into modal popups, chat sidebars, or modal blocking states while an AI model generates multi-file diffs or runs terminal commands. This friction degrades developer productivity and creates attention bottlenecks.

## Decision
We separated PRUBETH IDE into a **Dual-Surface Workflow**:
1. **Synchronous Surface ("Editor View")**:
   - The primary focus space for the human engineer.
   - Houses code tabs, the Monaco editor, file trees, terminal docks, and interactive inline diffs.
   - Allows uninterrupted manual coding, syntax inspection, and local debugging.
2. **Asynchronous Surface ("Mission Control / Agent Manager")**:
   - Dedicated space (`ui/mission_control_widget.py`, toggleable via `Ctrl+Shift+M`) for autonomous subagents executing background tasks.
   - Shows live task DAGs, ReAct execution traces (`Thought`, `Action`, `Observation`), and GPU offload telemetry.
   - Provides mid-flight steering: human developers can pause, inject guidance, or cancel tasks without interrupting their active editor session.

## Consequences
- **Positive**: Zero developer blocking during lengthy multi-step agent actions; total transparency into background agent planning and memory; frictionless switching with global keyboard shortcuts (`Ctrl+Shift+M`, `Ctrl+Shift+E`).
- **Negative**: Requires event-driven cross-surface state synchronisation via signals/slots to ensure changes made in Mission Control update editor buffers reliably.
