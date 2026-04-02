"""
Queue for SDK system events (task notifications, etc.).

Migrated from: utils/sdkEventQueue.ts
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

_sdk_queue: list[dict[str, Any]] = []


def clear_sdk_event_queue_for_testing() -> None:
    """Reset the queue (tests only)."""
    _sdk_queue.clear()


def enqueue_sdk_event(event: dict[str, Any]) -> None:
    """Append a raw SDK event payload to the in-process queue."""
    _sdk_queue.append(event)


def drain_sdk_events() -> list[dict[str, Any]]:
    """Remove and return all queued events (adds uuid/session_id in TS; caller may enrich)."""
    drained = _sdk_queue[:]
    _sdk_queue.clear()
    for item in drained:
        item.setdefault("uuid", str(uuid.uuid4()))
    return drained


def emit_task_terminated_sdk(
    task_id: str,
    status: Literal["completed", "failed", "stopped"],
    opts: dict[str, Any] | None = None,
) -> None:
    """Emit ``system`` / ``task_notification`` when XML path is suppressed."""
    opts = opts or {}
    tool_use = opts.get("tool_use_id") or opts.get("toolUseId")
    enqueue_sdk_event(
        {
            "type": "system",
            "subtype": "task_notification",
            "task_id": task_id,
            "tool_use_id": tool_use,
            "status": status,
            "output_file": opts.get("output_file", ""),
            "summary": opts.get("summary", ""),
            "usage": opts.get("usage"),
        },
    )
