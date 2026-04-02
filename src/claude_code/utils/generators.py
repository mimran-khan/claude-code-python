"""
Async generator utilities.

Migrated from: utils/generators.ts
"""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncGenerator
from typing import Literal, TypeAlias, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class _NoValue:
    pass


_NO_VALUE = _NoValue()


async def last_x(gen: AsyncGenerator[T, None]) -> T:
    """Return the last value yielded by an async generator."""
    last_value: T | _NoValue = _NO_VALUE
    async for item in gen:
        last_value = item
    if last_value is _NO_VALUE:
        raise RuntimeError("No items in generator")
    return last_value  # type: ignore[return-value]


async def return_value(gen: AsyncGenerator[object, R]) -> R:
    """Consume an async generator until done and return its return value."""
    while True:
        try:
            await gen.__anext__()
        except StopAsyncIteration as e:
            return e.value  # type: ignore[no-any-return, misc]


async def all_generators(
    generators: list[AsyncGenerator[T, None]],
    concurrency_cap: float = float("inf"),
) -> AsyncGenerator[T, None]:
    """
    Run async generators concurrently up to concurrency_cap, yielding values as they complete.
    """
    cap = min(len(generators), int(concurrency_cap)) if concurrency_cap < float("inf") else len(generators)
    waiting: deque[AsyncGenerator[T, None]] = deque(generators)
    PullKind: TypeAlias = Literal["item", "done"]
    PullResult: TypeAlias = tuple[PullKind, AsyncGenerator[T, None], T | None]
    tasks: dict[asyncio.Task[PullResult], AsyncGenerator[T, None]] = {}

    async def _pull(g: AsyncGenerator[T, None]) -> PullResult:
        try:
            item = await g.__anext__()
            return ("item", g, item)
        except StopAsyncIteration:
            return ("done", g, None)

    def _start(g: AsyncGenerator[T, None]) -> None:
        t = asyncio.create_task(_pull(g))
        tasks[t] = g

    while len(tasks) < cap and waiting:
        _start(waiting.popleft())

    while tasks:
        done, _ = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
        for finished in done:
            tasks.pop(finished)
            kind, g, value = finished.result()
            if kind == "item":
                if value is not None:
                    yield value
                _start(g)
            elif waiting:
                _start(waiting.popleft())


async def to_array(gen: AsyncGenerator[T, None]) -> list[T]:
    """Collect all values from an async generator into a list."""
    out: list[T] = []
    async for item in gen:
        out.append(item)
    return out


async def from_array(values: list[T]) -> AsyncGenerator[T, None]:
    """Yield each value from a list (async generator wrapper)."""
    for v in values:
        yield v
