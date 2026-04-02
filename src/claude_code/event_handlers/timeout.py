"""
Elapsed flag after delay (optionally reset by trigger).

Migrated from: hooks/useTimeout.ts
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass
class TimeoutController:
    delay_s: float
    is_elapsed: bool = False
    _task: asyncio.Task[None] | None = field(default=None, repr=False)

    async def arm(self, *, reset_trigger: int | None = None) -> None:
        _ = reset_trigger
        self.cancel()
        self.is_elapsed = False

        async def _fire() -> None:
            await asyncio.sleep(self.delay_s)
            self.is_elapsed = True

        self._task = asyncio.create_task(_fire())

    def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
