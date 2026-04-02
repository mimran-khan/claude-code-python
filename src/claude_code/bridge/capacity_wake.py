"""Capacity wake for bridge poll loops (ported from bridge/capacityWake.ts)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class CapacitySignal:
    """Merged abort for outer loop + capacity wake."""

    event: asyncio.Event
    cleanup: Callable[[], None]


class CapacityWake:
    def __init__(self, outer_event: asyncio.Event) -> None:
        self._outer = outer_event
        self._wake = asyncio.Event()

    def wake(self) -> None:
        self._wake.set()
        self._wake = asyncio.Event()

    def signal(self) -> CapacitySignal:
        merged = asyncio.Event()

        def abort() -> None:
            merged.set()

        if self._outer.is_set() or self._wake.is_set():
            merged.set()
            return CapacitySignal(merged, lambda: None)

        outer_wait = asyncio.create_task(self._outer.wait())
        wake_wait = asyncio.create_task(self._wake.wait())

        def cleanup() -> None:
            outer_wait.cancel()
            wake_wait.cancel()

        async def _waiter() -> None:
            done, pending = await asyncio.wait({outer_wait, wake_wait}, return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
            abort()

        task = asyncio.create_task(_waiter())

        def cleanup2() -> None:
            task.cancel()
            cleanup()

        return CapacitySignal(merged, cleanup2)


def create_capacity_wake(outer_signal: asyncio.Event) -> CapacityWake:
    """Create from an asyncio.Event standing in for AbortSignal."""
    return CapacityWake(outer_signal)
