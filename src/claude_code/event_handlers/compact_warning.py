"""
Compact warning suppression visibility (ported from services/compact/compactWarningHook.ts).

React useSyncExternalStore is approximated with polling or explicit refresh calls.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from claude_code.services.compact.compact_warning_state import is_compact_warning_suppressed


@dataclass
class CompactWarningHandler:
    """Cached snapshot of suppression flag for integrations without a render loop."""

    suppressed: bool = field(init=False)

    def __post_init__(self) -> None:
        self.refresh()

    def refresh(self) -> bool:
        self.suppressed = is_compact_warning_suppressed()
        return self.suppressed


async def watch_compact_warning_suppression(
    on_change: Callable[[bool], None] | Callable[[bool], Awaitable[None]],
    *,
    poll_interval_s: float = 0.1,
    stop: asyncio.Event | None = None,
) -> None:
    """
    Async loop until ``stop`` is set; invokes on_change when suppression toggles.

    Python compact_warning_state has no native subscribers; polling keeps the
    handler self-contained without changing global state APIs.
    """
    stop_event = stop or asyncio.Event()
    last = is_compact_warning_suppressed()
    while not stop_event.is_set():
        cur = is_compact_warning_suppressed()
        if cur != last:
            last = cur
            maybe = on_change(cur)
            if asyncio.iscoroutine(maybe):
                await maybe
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=poll_interval_s)
        except TimeoutError:
            continue
