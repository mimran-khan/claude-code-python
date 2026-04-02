"""
Analytics Events.

Event logging for analytics and telemetry.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol


class AnalyticsSink(Protocol):
    """Protocol for analytics sinks."""

    def log_event(self, event_name: str, metadata: dict[str, Any]) -> None:
        """Log an event synchronously."""
        ...

    async def log_event_async(
        self,
        event_name: str,
        metadata: dict[str, Any],
    ) -> None:
        """Log an event asynchronously."""
        ...


@dataclass
class QueuedEvent:
    """Event queued for later delivery."""

    event_name: str
    metadata: dict[str, Any]
    is_async: bool = False


@dataclass
class EventQueue:
    """Queue for events logged before sink is attached."""

    events: list[QueuedEvent] = field(default_factory=list)
    sink: AnalyticsSink | None = None
    max_queue_size: int = 1000

    def add(self, event: QueuedEvent) -> None:
        """Add an event to the queue."""
        if len(self.events) < self.max_queue_size:
            self.events.append(event)

    def drain(self) -> list[QueuedEvent]:
        """Remove and return all events from the queue."""
        events = self.events
        self.events = []
        return events


# Global event queue
_event_queue = EventQueue()


def attach_analytics_sink(sink: AnalyticsSink) -> None:
    """Attach an analytics sink to receive events.

    Queued events are drained asynchronously.
    Idempotent: if a sink is already attached, this is a no-op.
    """
    global _event_queue

    if _event_queue.sink is not None:
        return

    _event_queue.sink = sink

    # Drain queued events
    events = _event_queue.drain()
    for event in events:
        if event.is_async:
            asyncio.create_task(sink.log_event_async(event.event_name, event.metadata))
        else:
            sink.log_event(event.event_name, event.metadata)


def detach_analytics_sink() -> None:
    """Detach the analytics sink."""
    global _event_queue
    _event_queue.sink = None


def log_event(event_name: str, metadata: dict[str, Any] | None = None) -> None:
    """Log an analytics event.

    If no sink is attached, the event is queued for later delivery.

    Args:
        event_name: Name of the event
        metadata: Optional metadata to attach to the event
    """
    metadata = metadata or {}

    if _event_queue.sink is not None:
        _event_queue.sink.log_event(event_name, metadata)
    else:
        _event_queue.add(
            QueuedEvent(
                event_name=event_name,
                metadata=metadata,
                is_async=False,
            )
        )


async def log_event_async(
    event_name: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Log an analytics event asynchronously.

    If no sink is attached, the event is queued for later delivery.

    Args:
        event_name: Name of the event
        metadata: Optional metadata to attach to the event
    """
    metadata = metadata or {}

    if _event_queue.sink is not None:
        await _event_queue.sink.log_event_async(event_name, metadata)
    else:
        _event_queue.add(
            QueuedEvent(
                event_name=event_name,
                metadata=metadata,
                is_async=True,
            )
        )


# Common event names
EVENT_SESSION_START = "session_start"
EVENT_SESSION_END = "session_end"
EVENT_QUERY_START = "query_start"
EVENT_QUERY_END = "query_end"
EVENT_TOOL_USE = "tool_use"
EVENT_TOOL_RESULT = "tool_result"
EVENT_ERROR = "error"
EVENT_PERMISSION_REQUEST = "permission_request"
EVENT_PERMISSION_GRANTED = "permission_granted"
EVENT_PERMISSION_DENIED = "permission_denied"
EVENT_MCP_CONNECT = "mcp_connect"
EVENT_MCP_DISCONNECT = "mcp_disconnect"
EVENT_COMPACT_CONVERSATION = "compact_conversation"
