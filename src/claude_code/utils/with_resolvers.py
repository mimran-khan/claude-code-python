"""
Deferred future with explicit resolve/reject callbacks.

Migrated from: utils/withResolvers.ts (Promise.withResolvers polyfill).

Uses :class:`concurrent.futures.Future` so this works from threads without a
running asyncio loop. For asyncio, prefer ``loop.create_future()`` directly.
"""

from __future__ import annotations

from concurrent.futures import Future
from typing import TypeVar

T = TypeVar("T")


def with_resolvers() -> tuple[Future[T], object, object]:
    """Return ``(future, resolve, reject)`` matching the TS ``PromiseWithResolvers`` shape."""

    fut: Future[T] = Future()

    def resolve(value: T | None = None) -> None:
        if not fut.done():
            fut.set_result(value)  # type: ignore[arg-type]

    def reject(reason: BaseException | None = None) -> None:
        if not fut.done():
            fut.set_exception(reason if reason is not None else RuntimeError("Rejected"))

    return fut, resolve, reject
