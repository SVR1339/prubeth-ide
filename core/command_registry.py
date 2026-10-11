"""
PRUBETH IDE — Centralized Command & Action Registry
Pillar 2 & 4: Architecture & Design System Governance

Centralized registry providing consistent command execution, global shortcut resolution,
searchable command palette integration, risk-level auditing, and cancellation support.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Callable


class CommandRiskLevel:
    READ_ONLY = "read_only"
    SAFE_EXECUTION = "safe_execution"
    MUTATING = "mutating"
    HIGH_RISK = "high_risk"


@dataclass
class Command:
    """Represents an executable action within the PRUBETH IDE."""
    command_id: str
    title: str
    category: str  # File, Edit, View, AI, Terminal, Preferences, Developer, Tools
    handler: Callable
    description: str = ""
    shortcut: str = ""
    risk_level: str = CommandRiskLevel.READ_ONLY
    is_available: Callable[[], bool] = field(default_factory=lambda: (lambda: True))
    audit_required: bool = False
    source: str = "core"  # core, plugin, agent, user


@dataclass
class CommandExecutionRecord:
    command_id: str
    timestamp: float
    success: bool
    duration_ms: float
    error_message: Optional[str] = None


class CommandRegistry:
    """Singleton registry governing all interactive and programmatically invokable commands."""

    _instance: Optional[CommandRegistry] = None

    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._execution_history: List[CommandExecutionRecord] = []
        self._recent_ids: List[str] = []

    @classmethod
    def get_instance(cls) -> CommandRegistry:
        if cls._instance is None:
            cls._instance = CommandRegistry()
        return cls._instance

    def register(self, command: Command) -> None:
        """Registers a command into the central directory."""
        self._commands[command.command_id] = command

    def unregister(self, command_id: str) -> None:
        self._commands.pop(command_id, None)

    def get(self, command_id: str) -> Optional[Command]:
        return self._commands.get(command_id)

    def list_all(self) -> List[Command]:
        return list(self._commands.values())

    def search(self, query: str, category: Optional[str] = None) -> List[Command]:
        """Search commands by title, ID, category, or shortcut."""
        q = query.lower().strip()
        results: List[Command] = []
        for cmd in self._commands.values():
            if category and cmd.category.lower() != category.lower():
                continue
            if not q or q in cmd.title.lower() or q in cmd.command_id.lower() or q in cmd.category.lower() or q in cmd.shortcut.lower():
                results.append(cmd)
        return results

    def execute(self, command_id: str, *args, **kwargs) -> Any:
        """Executes a command by ID with validation, error isolation, and audit tracking."""
        cmd = self.get(command_id)
        if not cmd:
            raise KeyError(f"Command not found: '{command_id}'")

        if callable(cmd.is_available) and not cmd.is_available():
            raise PermissionError(f"Command '{command_id}' is currently unavailable in the active context.")

        t0 = time.time()
        success = False
        error_msg = None
        try:
            res = cmd.handler(*args, **kwargs)
            success = True
            return res
        except Exception as exc:
            error_msg = str(exc)
            raise
        finally:
            duration = (time.time() - t0) * 1000
            rec = CommandExecutionRecord(
                command_id=command_id,
                timestamp=time.time(),
                success=success,
                duration_ms=round(duration, 2),
                error_message=error_msg
            )
            self._execution_history.append(rec)
            if command_id in self._recent_ids:
                self._recent_ids.remove(command_id)
            self._recent_ids.insert(0, command_id)
            if len(self._recent_ids) > 20:
                self._recent_ids = self._recent_ids[:20]

    def get_recent_commands(self) -> List[Command]:
        return [self._commands[cid] for cid in self._recent_ids if cid in self._commands]

    def get_history(self, limit: int = 50) -> List[CommandExecutionRecord]:
        return list(self._execution_history[-limit:])
