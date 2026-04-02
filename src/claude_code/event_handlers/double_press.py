"""
Time-window double-press detector (first press arms, second within window fires).

Migrated from: hooks/useDoublePress.ts
"""

from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

DOUBLE_PRESS_TIMEOUT_MS = 800
DOUBLE_PRESS_TIMEOUT_S = DOUBLE_PRESS_TIMEOUT_MS / 1000.0


@dataclass
class DoublePressController:
    """Asyncio equivalent of useDoublePress (no React setState)."""

    on_double_press: Callable[[], None] | Callable[[], Awaitable[None]]
    set_pending: Callable[[bool], None] | None = None
    on_first_press: Callable[[], None] | Callable[[], Awaitable[None]] | None = None
    _last_press_ms: float = 0.0
    _timeout_task: asyncio.Task[None] | None = field(default=None, repr=False)

    def _clear_timeout(self) -> None:
        if self._timeout_task is not None:
            self._timeout_task.cancel()
            self._timeout_task = None

    def reset(self) -> None:
        self._clear_timeout()
        self._last_press_ms = 0.0

    async def press(self) -> None:
        now = time.monotonic() * 1000.0
        time_since = now - self._last_press_ms
        pending = self._timeout_task is not None and not self._timeout_task.done()
        is_double = time_since <= DOUBLE_PRESS_TIMEOUT_MS and pending

        if is_double:
            self._clear_timeout()
            if self.set_pending:
                self.set_pending(False)
            res = self.on_double_press()
            if inspect.isawaitable(res):
                await res
        else:
            if self.on_first_press:
                fp = self.on_first_press()
                if inspect.isawaitable(fp):
                    await fp
            if self.set_pending:
                self.set_pending(True)
            self._clear_timeout()

            async def _expire() -> None:
                try:
                    await asyncio.sleep(DOUBLE_PRESS_TIMEOUT_S)
                except asyncio.CancelledError:
                    return
                if self.set_pending:
                    self.set_pending(False)

            self._timeout_task = asyncio.create_task(_expire())

        self._last_press_ms = now
