"""
Process-exit cleanup hooks (mirrors utils/cleanupRegistry.ts).

Registers callables to run at interpreter exit. Async work is run via
``asyncio.run`` in a fresh policy context when possible.
"""

from __future__ import annotations

import asyncio
import atexit
import logging
from collections.abc import Awaitable, Callable

_logger = logging.getLogger(__name__)

_sync_hooks: list[Callable[[], None]] = []
_async_hooks: list[Callable[[], Awaitable[None]]] = []


def register_cleanup(
    fn: Callable[[], None] | Callable[[], Awaitable[None]],
) -> None:
    """Register a sync or async cleanup to run at process exit."""
    if asyncio.iscoroutinefunction(fn):
        _async_hooks.append(fn)  # type: ignore[arg-type]
    else:
        _sync_hooks.append(fn)  # type: ignore[arg-type]


def _run_async_cleanups() -> None:
    if not _async_hooks:
        return

    async def _run_all() -> None:
        for hook in _async_hooks:
            try:
                await hook()  # type: ignore[misc]
            except Exception:
                _logger.exception("Async cleanup hook failed")

    try:
        asyncio.run(_run_all())
    except RuntimeError:
        # Event loop may already be running or closed; best-effort.
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_run_all())
            loop.close()
        except Exception:
            _logger.exception("Could not run async cleanup hooks")


def _run_exit_cleanups() -> None:
    for hook in _sync_hooks:
        try:
            hook()
        except Exception:
            _logger.exception("Sync cleanup hook failed")
    _run_async_cleanups()


atexit.register(_run_exit_cleanups)

__all__ = ["register_cleanup"]
