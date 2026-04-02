"""
Desktop notification when user has been idle past interaction threshold.

Migrated from: hooks/useNotifyAfterTimeout.ts
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable

DEFAULT_INTERACTION_THRESHOLD_S = 6.0


def time_since_last_interaction(get_last_interaction_time: Callable[[], float]) -> float:
    return time.time() * 1000 - get_last_interaction_time()


def has_recent_interaction(
    get_last_interaction_time: Callable[[], float],
    threshold_ms: float = DEFAULT_INTERACTION_THRESHOLD_S * 1000,
) -> bool:
    return (time.time() * 1000 - get_last_interaction_time()) < threshold_ms


async def run_notify_after_idle_poll(
    *,
    message: str,
    notification_type: str,
    send_notification: Callable[[str, str], Awaitable[None]],
    get_last_interaction_time: Callable[[], float],
    stop_event: asyncio.Event,
    interval_s: float = DEFAULT_INTERACTION_THRESHOLD_S,
    is_test_env: bool = False,
) -> None:
    """Poll until idle + notify once; mirrors setInterval body from TS hook."""
    has_notified = False
    while not stop_event.is_set():
        idle = not has_recent_interaction(get_last_interaction_time)
        if not is_test_env and idle and not has_notified:
            has_notified = True
            await send_notification(message, notification_type)
            return
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_s)
            return
        except TimeoutError:
            continue
