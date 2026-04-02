"""
Batch spawn / shutdown notifications for in-process teammate tasks.

Migrated from: hooks/notifs/useTeammateShutdownNotification.ts.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

_SPAWN_KEY = "teammate-spawn"
_SHUTDOWN_KEY = "teammate-shutdown"


def parse_notification_count(notif: Mapping[str, Any]) -> int:
    text = notif.get("text")
    if not isinstance(text, str):
        return 1
    match = re.match(r"^(\d+)", text)
    return int(match.group(1)) if match else 1


def make_spawn_notification(count: int = 1) -> dict[str, Any]:
    return {
        "key": _SPAWN_KEY,
        "text": "1 agent spawned" if count == 1 else f"{count} agents spawned",
        "priority": "low",
        "timeoutMs": 5000,
    }


def make_shutdown_notification(count: int = 1) -> dict[str, Any]:
    return {
        "key": _SHUTDOWN_KEY,
        "text": "1 agent shut down" if count == 1 else f"{count} agents shut down",
        "priority": "low",
        "timeoutMs": 5000,
    }


def is_in_process_teammate_task(task: Mapping[str, Any]) -> bool:
    """Matches tasks/InProcessTeammateTask/types.ts ``isInProcessTeammateTask``."""
    return task.get("type") == "in_process_teammate"


def diff_teammate_lifecycle_events(
    tasks: Mapping[str, Mapping[str, Any]],
    seen_running: set[str],
    seen_completed: set[str],
    add_notification: Callable[[dict[str, Any]], None],
) -> None:
    for tid, task in tasks.items():
        if not is_in_process_teammate_task(task):
            continue
        if task.get("status") == "running" and tid not in seen_running:
            seen_running.add(tid)
            add_notification(make_spawn_notification(1))
        if task.get("status") == "completed" and tid not in seen_completed:
            seen_completed.add(tid)
            add_notification(make_shutdown_notification(1))
