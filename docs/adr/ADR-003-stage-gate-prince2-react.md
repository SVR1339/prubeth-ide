# ADR-003: PRINCE2 Stage-Gate Lifecycle and ReAct Autonomous Engine

## Status
Accepted

## Date
2026-10-11

## Context
Unconstrained AI agents can loop infinitely, perform uncontrolled destructive actions, or drift from product requirements. A rigorous governance model is required to enforce stage boundaries, validation checkpoints, and verifiable decision logs without sacrificing speed.

## Decision
We implemented the **PRINCE2 Stage-Gate Lifecycle & ReAct Engine** (`horizon_engine/stage_gate.py`):
1. **Explicit Lifecycle Stages**:
   - `INITIATION`: Requirements gathering, scope validation, and task objective setup.
   - `STAGE_GATE_REVIEW`: Verifiable artifact plan review (`implementation_plan.md`, `task_checklist.json`) with human approval gates.
   - `EXECUTION`: Autonomous execution of actions within isolated sandbox worktrees (`worktree_sandbox.py`).
   - `ACCEPTANCE`: Automated verification including browser headless tests (`browser_verifier.py`) and pytest suites.
   - `COMPLETED`: Merging shadow worktrees, updating memory stores, and finalizing release logs.
2. **ReAct Trace Logging**:
   - Every agent step explicitly emits structured entries: `Thought` (internal reasoning), `Action` (tool/command invocation), and `Observation` (environment response).
3. **Mid-Flight Feedback Injection**:
   - Developers can inject steer comments or modify checklist items mid-flight, immediately interrupting and re-orienting the agent DAG without restarting the task.

## Consequences
- **Positive**: Complete auditability, predictable delivery, zero runaway loops, and high human trust.
- **Negative**: Adds a stage transition overhead and requires artifact generation before code execution.
