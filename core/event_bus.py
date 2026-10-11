"""
PRUBETH IDE — Central Application Event Bus & Audit Stream
Pillar 6 & 7: Quality Engineering & Operations Governance

Structured event bus supporting typed channels, asynchronous/synchronous subscriber dispatch,
automatic secret redaction on event payloads, and bounded audit retention.
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Callable


class EventChannel:
    APPLICATION = "application"
    WORKSPACE = "workspace"
    EDITOR = "editor"
    MODEL = "model"
    AGENT = "agent"
    CONFIG = "config"
    SECURITY = "security"
    HEALTH = "health"


class EventSeverity:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SECURITY = "security"


@dataclass
class Event:
    """Represents a structured lifecycle, audit, or telemetry event within the IDE."""
    channel: str
    source: str
    payload: Dict[str, Any]
    severity: str = EventSeverity.INFO
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """Central event broker for internal operations, monitoring, and state inspection."""

    _instance: Optional[EventBus] = None

    SECRET_PATTERNS = [
        re.compile(r"(api[_-]?key|token|secret|password|bearer)\s*[:=]\s*([^\s,;\"']+)", re.IGNORECASE),
        re.compile(r"(AIza[0-9A-Za-z-_]{35})"),
        re.compile(r"(sk-[a-zA-Z0-9]{32,})"),
    ]

    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._history: List[Event] = []

    @classmethod
    def get_instance(cls) -> EventBus:
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance

    def subscribe(self, channel: str, callback: Callable[[Event], None]) -> None:
        """Subscribes a listener to a specific event channel, or '*' for all channels."""
        self._subscribers.setdefault(channel, []).append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[Event], None]) -> None:
        if channel in self._subscribers and callback in self._subscribers[channel]:
            self._subscribers[channel].remove(callback)

    def publish(self, channel: str, source: str, payload: Dict[str, Any], severity: str = EventSeverity.INFO) -> Event:
        """Sanitizes payload, records in bounded history, and broadcasts to listeners."""
        sanitized_payload = self._sanitize_dict(payload)
        ev = Event(
            channel=channel,
            source=source,
            payload=sanitized_payload,
            severity=severity
        )
        self._history.append(ev)
        if len(self._history) > self.max_history:
            self._history.pop(0)

        # Dispatch to channel listeners and wildcard listeners
        listeners = list(self._subscribers.get(channel, [])) + list(self._subscribers.get("*", []))
        for cb in listeners:
            try:
                cb(ev)
            except Exception:
                pass  # Listener failures must never crash the event emitter
        return ev

    def get_history(self, channel: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Returns bounded event history, optionally filtered by channel."""
        if channel:
            filtered = [e for e in self._history if e.channel == channel]
            return filtered[-limit:]
        return self._history[-limit:]

    def clear_history(self) -> None:
        self._history.clear()

    @classmethod
    def _sanitize_string(cls, val: str) -> str:
        res = val
        for pat in cls.SECRET_PATTERNS:
            res = pat.sub(r"[REDACTED_SECRET]", res)
        return res

    @classmethod
    def _sanitize_dict(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}
        for k, v in d.items():
            k_lower = k.lower()
            if any(s in k_lower for s in ("key", "secret", "token", "password", "auth")):
                cleaned[k] = "[REDACTED_SECRET]"
            elif isinstance(v, str):
                cleaned[k] = cls._sanitize_string(v)
            elif isinstance(v, dict):
                cleaned[k] = cls._sanitize_dict(v)
            elif isinstance(v, list):
                cleaned[k] = [cls._sanitize_dict(x) if isinstance(x, dict) else cls._sanitize_string(x) if isinstance(x, str) else x for x in v]
            else:
                cleaned[k] = v
        return cleaned
