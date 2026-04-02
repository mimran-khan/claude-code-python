"""
Minimum on-screen time for rapidly changing status text.

Migrated from: hooks/useMinDisplayTime.ts
"""

from __future__ import annotations

import asyncio
import time
from typing import Generic, TypeVar

T = TypeVar("T")


class MinDisplayTimeController(Generic[T]):
    """Hold displayed value; call :meth:`on_source_change` when input changes."""

    def __init__(self, min_ms: int) -> None:
        self.min_ms = min_ms
        self.displayed: T | None = None
        self._last_shown_at = 0.0
        self._pending: asyncio.Task[None] | None = None

    def snapshot(self) -> T | None:
        return self.displayed

    async def on_source_change(self, value: T) -> None:
        now = time.monotonic() * 1000
        elapsed = now - self._last_shown_at
        if self._pending is not None:
            self._pending.cancel()
            self._pending = None
        if elapsed >= self.min_ms:
            self._last_shown_at = now
            self.displayed = value
            return
        wait_ms = self.min_ms - elapsed

        async def _apply() -> None:
            nonlocal self
            await asyncio.sleep(wait_ms / 1000)
            self._last_shown_at = time.monotonic() * 1000
            self.displayed = value
            self._pending = None

        self._pending = asyncio.create_task(_apply())

    def cancel(self) -> None:
        if self._pending is not None:
            self._pending.cancel()
            self._pending = None
