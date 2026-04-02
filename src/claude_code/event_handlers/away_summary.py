"""
\"While you were away\" summary after terminal blur + idle delay.

Migrated from: hooks/useAwaySummary.ts
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

BLUR_DELAY_MS = 5 * 60_000
BLUR_DELAY_S = BLUR_DELAY_MS / 1000.0


def has_summary_since_last_user_turn(messages: Sequence[Mapping[str, Any]]) -> bool:
    """Walk backward from transcript tail; stop at real user turn."""
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if m.get("type") == "user" and not m.get("isMeta") and not m.get("isCompactSummary"):
            return False
        if m.get("type") == "system" and m.get("subtype") == "away_summary":
            return True
    return False


@dataclass
class AwaySummaryTimerState:
    """
    Terminal-blur driven timer. Call ``schedule_blur_fire`` when focus is lost,
    ``cancel_on_focus`` when focus returns.
    """

    pending_after_load: bool = False
    _blur_task: asyncio.Task[None] | None = field(default=None, repr=False)

    def cancel_blur_task(self) -> None:
        if self._blur_task is not None:
            self._blur_task.cancel()
            self._blur_task = None

    async def on_focus(self) -> None:
        self.cancel_blur_task()
        self.pending_after_load = False

    def schedule_blur_fire(self, on_fire: Callable[[], Any]) -> None:
        self.cancel_blur_task()

        async def _delayed() -> None:
            try:
                await asyncio.sleep(BLUR_DELAY_S)
            except asyncio.CancelledError:
                return
            res = on_fire()
            if asyncio.iscoroutine(res):
                await res

        self._blur_task = asyncio.create_task(_delayed())
