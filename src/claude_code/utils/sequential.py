"""
Sequential async wrapper — one in-flight call at a time (FIFO).

Migrated from: utils/sequential.ts
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def sequential(
    fn: Callable[P, Awaitable[R]],
) -> Callable[P, Coroutine[Any, Any, R]]:
    """
    Wrap ``fn`` so concurrent invocations run strictly one-after-another.
    Preserves per-call return values via futures.
    """
    queue: list[tuple[tuple[Any, ...], dict[str, Any], asyncio.Future[R]]] = []
    mutex = asyncio.Lock()
    active: asyncio.Task[None] | None = None

    async def worker_loop() -> None:
        while True:
            async with mutex:
                if not queue:
                    return
                args, kwargs, fut = queue.pop(0)
            try:
                result = await fn(*args, **kwargs)
                fut.set_result(result)
            except Exception as e:
                fut.set_exception(e)

    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        nonlocal active
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[R] = loop.create_future()
        async with mutex:
            queue.append((args, kwargs, fut))
            if active is None or active.done():
                active = asyncio.create_task(worker_loop())
        return await fut

    return wrapped
