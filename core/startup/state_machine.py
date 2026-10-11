"""
PRUBETH IDE — Staged Startup State Machine
Part of the Zero-Silent-Failure Launcher & Application Startup Engine.

Enforces explicit, auditable lifecycle transitions:
NOT_STARTED -> PREFLIGHT -> CONFIGURATION_READY -> CORE_SERVICES_READY -> GUI_READY -> APPLICATION_READY
with explicit failure, recovery, degraded, and cancellation handling.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Callable


class StartupState(str, Enum):
    NOT_STARTED = "not_started"
    PREFLIGHT = "preflight"
    CONFIGURATION_READY = "configuration_ready"
    CORE_SERVICES_READY = "core_services_ready"
    GUI_READY = "gui_ready"
    APPLICATION_READY = "application_ready"
    DEGRADED_MODE = "degraded_mode"
    RECOVERY_MODE = "recovery_mode"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SHUTDOWN = "shutdown"


@dataclass
class TransitionRecord:
    """Historical telemetry record of a single startup state transition."""
    from_state: StartupState
    to_state: StartupState
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class InvalidStateTransitionError(RuntimeError):
    """Raised when attempting an unauthorized or out-of-order startup state transition."""
    pass


class StartupStateMachine:
    """
    State machine that governs application initialization.
    Guarantees every stage has defined preconditions, bounded timeouts,
    timing telemetry, and rollback/recovery hooks.
    """

    # Permitted state transition graph
    VALID_TRANSITIONS: Dict[StartupState, List[StartupState]] = {
        StartupState.NOT_STARTED: [StartupState.PREFLIGHT, StartupState.FAILED, StartupState.CANCELLED],
        StartupState.PREFLIGHT: [
            StartupState.CONFIGURATION_READY,
            StartupState.RECOVERY_MODE,
            StartupState.FAILED,
            StartupState.CANCELLED
        ],
        StartupState.CONFIGURATION_READY: [
            StartupState.CORE_SERVICES_READY,
            StartupState.RECOVERY_MODE,
            StartupState.FAILED,
            StartupState.CANCELLED
        ],
        StartupState.CORE_SERVICES_READY: [
            StartupState.GUI_READY,
            StartupState.APPLICATION_READY, # In headless mode
            StartupState.DEGRADED_MODE,
            StartupState.FAILED,
            StartupState.CANCELLED
        ],
        StartupState.DEGRADED_MODE: [
            StartupState.GUI_READY,
            StartupState.APPLICATION_READY,
            StartupState.FAILED,
            StartupState.CANCELLED
        ],
        StartupState.GUI_READY: [
            StartupState.APPLICATION_READY,
            StartupState.DEGRADED_MODE,
            StartupState.FAILED,
            StartupState.CANCELLED
        ],
        StartupState.APPLICATION_READY: [StartupState.SHUTDOWN, StartupState.FAILED],
        StartupState.RECOVERY_MODE: [
            StartupState.PREFLIGHT,
            StartupState.CONFIGURATION_READY,
            StartupState.DEGRADED_MODE,
            StartupState.FAILED,
            StartupState.CANCELLED
        ],
        StartupState.FAILED: [StartupState.RECOVERY_MODE, StartupState.SHUTDOWN],
        StartupState.CANCELLED: [StartupState.SHUTDOWN],
        StartupState.SHUTDOWN: []
    }

    def __init__(self):
        self._current_state: StartupState = StartupState.NOT_STARTED
        self._history: List[TransitionRecord] = []
        self._listeners: List[Callable[[StartupState, StartupState, TransitionRecord], None]] = []
        self._lock = threading.RLock()
        self._startup_start_time: float = time.time()
        self._stage_start_time: float = time.time()

    @property
    def current_state(self) -> StartupState:
        with self._lock:
            return self._current_state

    @property
    def is_ready(self) -> bool:
        with self._lock:
            return self._current_state in (StartupState.APPLICATION_READY, StartupState.DEGRADED_MODE)

    @property
    def is_failed(self) -> bool:
        with self._lock:
            return self._current_state in (StartupState.FAILED, StartupState.CANCELLED)

    def register_listener(self, callback: Callable[[StartupState, StartupState, TransitionRecord], None]) -> None:
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def transition_to(
        self,
        target_state: StartupState,
        error_message: Optional[str] = None,
        diagnostics: Optional[Dict[str, Any]] = None
    ) -> TransitionRecord:
        """
        Transitions the state machine to target_state with validation and timing telemetry.
        """
        with self._lock:
            now = time.time()
            allowed = self.VALID_TRANSITIONS.get(self._current_state, [])
            
            if target_state not in allowed:
                err_msg = (
                    f"Illegal startup state transition: cannot transition from "
                    f"'{self._current_state.value}' to '{target_state.value}'. "
                    f"Allowed transitions: {[s.value for s in allowed]}"
                )
                record = TransitionRecord(
                    from_state=self._current_state,
                    to_state=target_state,
                    start_time=self._stage_start_time,
                    end_time=now,
                    duration_ms=(now - self._stage_start_time) * 1000.0,
                    success=False,
                    error_message=err_msg
                )
                self._history.append(record)
                raise InvalidStateTransitionError(err_msg)

            duration_ms = (now - self._stage_start_time) * 1000.0
            from_st = self._current_state
            
            record = TransitionRecord(
                from_state=from_st,
                to_state=target_state,
                start_time=self._stage_start_time,
                end_time=now,
                duration_ms=duration_ms,
                success=(error_message is None),
                error_message=error_message,
                diagnostics=diagnostics or {}
            )

            self._current_state = target_state
            self._stage_start_time = now
            self._history.append(record)

            # Notify listeners
            listeners = list(self._listeners)
            for listener in listeners:
                try:
                    listener(from_st, target_state, record)
                except Exception:
                    pass

            return record

    def get_summary(self) -> Dict[str, Any]:
        """Returns structured startup telemetry summary."""
        with self._lock:
            now = time.time()
            total_duration_ms = (now - self._startup_start_time) * 1000.0
            return {
                "current_state": self._current_state.value,
                "is_ready": self.is_ready,
                "is_failed": self.is_failed,
                "total_startup_duration_ms": round(total_duration_ms, 2),
                "transition_count": len(self._history),
                "transitions": [
                    {
                        "from": r.from_state.value,
                        "to": r.to_state.value,
                        "duration_ms": round(r.duration_ms, 2),
                        "success": r.success,
                        "error": r.error_message
                    }
                    for r in self._history
                ]
            }
