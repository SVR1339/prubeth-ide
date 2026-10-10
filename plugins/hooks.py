"""
SUKHI IDE — Extensible Plugin Hook & Event Dispatch Subsystem
Provides lifecycle hook registration, priority execution ordering,
waterfall filtering, and fault-isolated event broadcasting.
"""
import logging
from enum import Enum
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger("SukhiIDE.Plugins.Hooks")


class HookEvent(str, Enum):
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"
    ON_FILE_OPEN = "on_file_open"
    ON_FILE_SAVE = "on_file_save"
    ON_PROMPT_PREPARE = "on_prompt_prepare"
    ON_TOOL_EXECUTE = "on_tool_execute"
    ON_TEST_COMPLETE = "on_test_complete"


@dataclass
class HookRegistration:
    handler_id: str
    event: HookEvent
    callback: Callable[..., Any]
    priority: int = 100  # Higher numbers execute earlier
    plugin_id: str = "core"


class HookRegistry:
    """Manages lifecycle hooks with priority execution and fault isolation."""

    def __init__(self):
        self._hooks: Dict[HookEvent, List[HookRegistration]] = {
            evt: [] for evt in HookEvent
        }
        self._next_id = 1

    def register(
        self,
        event: HookEvent,
        callback: Callable[..., Any],
        priority: int = 100,
        plugin_id: str = "core"
    ) -> str:
        handler_id = f"hook-{self._next_id}"
        self._next_id += 1

        reg = HookRegistration(
            handler_id=handler_id,
            event=event,
            callback=callback,
            priority=priority,
            plugin_id=plugin_id
        )

        bucket = self._hooks.setdefault(event, [])
        bucket.append(reg)
        bucket.sort(key=lambda r: r.priority, reverse=True)
        return handler_id

    def unregister(self, handler_id: str) -> bool:
        for bucket in self._hooks.values():
            for i, reg in enumerate(bucket):
                if reg.handler_id == handler_id:
                    bucket.pop(i)
                    return True
        return False

    def unregister_plugin(self, plugin_id: str) -> int:
        removed = 0
        for bucket in self._hooks.values():
            filtered = [r for r in bucket if r.plugin_id != plugin_id]
            removed += (len(bucket) - len(filtered))
            bucket[:] = filtered
        return removed

    def dispatch(self, event: HookEvent, **kwargs) -> List[Any]:
        """Broadcasts event to registered callbacks; errors are logged without halting dispatch."""
        results = []
        bucket = self._hooks.get(event, [])
        for reg in list(bucket):
            try:
                res = reg.callback(**kwargs)
                results.append(res)
            except Exception as ex:
                logger.error(
                    f"Hook handler '{reg.handler_id}' ({reg.plugin_id}) failed on event '{event.value}': {ex}",
                    exc_info=True
                )
        return results

    def dispatch_filter(self, event: HookEvent, value: Any, **kwargs) -> Any:
        """Pipes a value through handlers in waterfall sequence (e.g. prompt preprocessing)."""
        curr = value
        bucket = self._hooks.get(event, [])
        for reg in list(bucket):
            try:
                res = reg.callback(curr, **kwargs)
                if res is not None:
                    curr = res
            except Exception as ex:
                logger.error(
                    f"Filter hook handler '{reg.handler_id}' failed on '{event.value}': {ex}",
                    exc_info=True
                )
        return curr
