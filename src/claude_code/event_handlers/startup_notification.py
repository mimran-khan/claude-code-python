"""
One-shot startup notification(s) gated on non-remote mode.

Migrated from: hooks/notifs/useStartupNotification.ts
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

log = logging.getLogger(__name__)

Notification = dict[str, Any]
Result = Notification | Sequence[Notification] | None


async def run_startup_notification_once(
    compute: Callable[[], Result | Awaitable[Result]],
    add_notification: Callable[[Notification], None],
    *,
    is_remote_mode: bool,
) -> None:
    if is_remote_mode:
        return
    try:
        raw = compute()
        if asyncio.iscoroutine(raw):
            result = await raw
        else:
            result = raw
        if not result:
            return
        if isinstance(result, dict):
            items: list[Notification] = [result]
        else:
            items = list(result)
        for n in items:
            add_notification(n)
    except Exception:  # noqa: BLE001
        log.exception("startup notification compute failed")
