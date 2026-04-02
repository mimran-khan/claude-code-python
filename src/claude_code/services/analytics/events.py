"""
Analytics events module.

Core event logging functionality for analytics.

Migrated from: services/analytics/index.ts (174 lines)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Protocol

LogEventMetadata = dict[str, bool | int | float | str | None]

_ASYNC_BATCH_MAX = 48
_ASYNC_FLUSH_S = 0.25
_ASYNC_QUEUE_MAX = 10_000


@dataclass
class QueuedEvent:
    """A queued analytics event."""

    event_name: str
    metadata: LogEventMetadata
    is_async: bool = False


class AnalyticsSink(Protocol):
    """Protocol for analytics sink implementations."""

    def log_event(self, event_name: str, metadata: LogEventMetadata) -> None: ...
    async def log_event_async(self, event_name: str, metadata: LogEventMetadata) -> None: ...


_event_queue: list[QueuedEvent] = []
_sink: AnalyticsSink | None = None

_async_dispatch_queue: asyncio.Queue[tuple[str, LogEventMetadata]] | None = None
_async_worker: asyncio.Task[None] | None = None


def strip_proto_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Strip _PROTO_* keys from a payload destined for general-access storage.

    Returns the input unchanged when no _PROTO_ keys present.
    """
    result = None
    for key in tuple(metadata.keys()):
        if key.startswith("_PROTO_"):
            if result is None:
                result = dict(metadata)
            del result[key]

    return result if result is not None else metadata


def _ensure_async_worker_started() -> None:
    global _async_dispatch_queue, _async_worker
    if _sink is None:
        return
    if _async_worker is not None and not _async_worker.done():
        return
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return
    if _async_dispatch_queue is None:
        _async_dispatch_queue = asyncio.Queue(maxsize=_ASYNC_QUEUE_MAX)
    _async_worker = asyncio.create_task(_async_batch_worker())


async def _async_batch_worker() -> None:
    global _sink, _async_dispatch_queue
    if _async_dispatch_queue is None or _sink is None:
        return
    try:
        while True:
            name, meta = await _async_dispatch_queue.get()
            batch: list[tuple[str, LogEventMetadata]] = [(name, meta)]
            loop = asyncio.get_running_loop()
            deadline = loop.time() + _ASYNC_FLUSH_S
            while len(batch) < _ASYNC_BATCH_MAX:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    break
                try:
                    n2, m2 = await asyncio.wait_for(
                        _async_dispatch_queue.get(),
                        timeout=remaining,
                    )
                    batch.append((n2, m2))
                except TimeoutError:
                    break
            for n, m in batch:
                await _sink.log_event_async(n, m)
    except asyncio.CancelledError:
        raise


def attach_analytics_sink(new_sink: AnalyticsSink) -> None:
    """
    Attach the analytics sink that will receive all events.

    Idempotent: if a sink is already attached, this is a no-op.
    """
    global _sink, _event_queue

    if _sink is not None:
        return

    _sink = new_sink

    if not _event_queue:
        return

    queued_events = list(_event_queue)
    _event_queue.clear()

    import os

    if os.getenv("USER_TYPE") == "ant":
        _sink.log_event(
            "analytics_sink_attached",
            {"queued_event_count": len(queued_events)},
        )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        for event in queued_events:
            _sink.log_event(event.event_name, event.metadata)
        return

    _ensure_async_worker_started()
    if _async_dispatch_queue is None:
        for event in queued_events:
            _sink.log_event(event.event_name, event.metadata)
        return

    for event in queued_events:
        if event.is_async:
            _async_dispatch_queue.put_nowait((event.event_name, event.metadata))
        else:
            _sink.log_event(event.event_name, event.metadata)


def log_event(event_name: str, metadata: LogEventMetadata | None = None) -> None:
    """
    Log an event to analytics backends (synchronous).

    If no sink is attached, events are queued and drained when the sink attaches.
    """
    if metadata is None:
        metadata = {}

    if _sink is None:
        _event_queue.append(
            QueuedEvent(
                event_name=event_name,
                metadata=metadata,
                is_async=False,
            )
        )
        return

    _sink.log_event(event_name, metadata)


async def log_event_async(
    event_name: str,
    metadata: LogEventMetadata | None = None,
) -> None:
    """
    Log an event asynchronously.

    With an attached sink and running event loop, events are batched to
    ``sink.log_event_async``. Without a loop, falls back to ``log_event``.
    """
    if metadata is None:
        metadata = {}

    if _sink is None:
        _event_queue.append(
            QueuedEvent(
                event_name=event_name,
                metadata=metadata,
                is_async=True,
            )
        )
        return

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        _sink.log_event(event_name, metadata)
        return

    _ensure_async_worker_started()
    if _async_dispatch_queue is not None:
        await _async_dispatch_queue.put((event_name, metadata))
        return

    await _sink.log_event_async(event_name, metadata)


def reset_for_testing() -> None:
    """Reset analytics state for testing purposes only."""
    global _sink, _event_queue, _async_dispatch_queue, _async_worker
    if _async_worker is not None and not _async_worker.done():
        _async_worker.cancel()
    _async_worker = None
    _async_dispatch_queue = None
    _sink = None
    _event_queue.clear()
