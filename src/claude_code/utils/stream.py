"""
Async single-consumer queue stream (async iterator).

Migrated from: utils/stream.ts
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Generic, TypeVar

T = TypeVar("T")

_DONE = object()


class Stream(Generic[T], AsyncIterator[T]):
    """Async iterator with ``enqueue``, ``done``, and ``error`` from a producer."""

    def __init__(self, returned: Callable[[], None] | None = None) -> None:
        self._queue: asyncio.Queue[object] = asyncio.Queue()
        self._started = False
        self._returned = returned
        self._finished = False

    def __aiter__(self) -> Stream[T]:
        if self._started:
            msg = "Stream can only be iterated once"
            raise RuntimeError(msg)
        self._started = True
        return self

    async def __anext__(self) -> T:
        item = await self._queue.get()
        if item is _DONE:
            self._finished = True
            raise StopAsyncIteration
        if isinstance(item, BaseException):
            raise item
        return item  # type: ignore[return-value]

    def enqueue(self, value: T) -> None:
        self._queue.put_nowait(value)

    def done(self) -> None:
        self._queue.put_nowait(_DONE)

    def error(self, err: BaseException) -> None:
        self._queue.put_nowait(err)

    async def aclose(self) -> None:
        """Producer finished early (TS ``return`` on iterator)."""
        if not self._finished:
            self._queue.put_nowait(_DONE)
        if self._returned is not None:
            self._returned()
