"""
Sleep Utilities.

Async sleep functions with abort support.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TypeVar

T = TypeVar("T")


class AbortError(Exception):
    """Error raised when an operation is aborted."""

    pass


async def sleep(
    seconds: float,
    *,
    abort_event: asyncio.Event | None = None,
    throw_on_abort: bool = False,
) -> None:
    """Abort-responsive sleep.

    Resolves after `seconds`, or immediately when `abort_event` is set.

    Args:
        seconds: Seconds to sleep
        abort_event: Optional event that triggers early wake
        throw_on_abort: If True, raise AbortError on abort

    Raises:
        AbortError: If throw_on_abort is True and abort_event is set
    """
    if abort_event and abort_event.is_set():
        if throw_on_abort:
            raise AbortError("aborted")
        return

    if abort_event is None:
        await asyncio.sleep(seconds)
        return

    done = asyncio.Event()

    async def wait_for_abort() -> None:
        await abort_event.wait()
        done.set()

    async def wait_for_timeout() -> None:
        await asyncio.sleep(seconds)
        done.set()

    abort_task = asyncio.create_task(wait_for_abort())
    timeout_task = asyncio.create_task(wait_for_timeout())

    try:
        await done.wait()
    finally:
        abort_task.cancel()
        timeout_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await abort_task
        with contextlib.suppress(asyncio.CancelledError):
            await timeout_task

    if abort_event.is_set() and throw_on_abort:
        raise AbortError("aborted")


async def with_timeout(
    coro: asyncio.coroutine,
    seconds: float,
    message: str = "Operation timed out",
) -> T:
    """Race a coroutine against a timeout.

    Args:
        coro: The coroutine to run
        seconds: Timeout in seconds
        message: Error message if timeout

    Returns:
        The coroutine result

    Raises:
        TimeoutError: If the coroutine doesn't complete in time
    """
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except TimeoutError:
        raise TimeoutError(message)


def sleep_sync(seconds: float) -> None:
    """Synchronous sleep.

    Args:
        seconds: Seconds to sleep
    """
    import time

    time.sleep(seconds)
