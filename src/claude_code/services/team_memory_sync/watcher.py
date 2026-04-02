"""
Debounced file watcher for team memory directory.

Migrated from: services/teamMemorySync/watcher.ts (asyncio.Task + debounce).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ...utils.debug import log_for_debugging
from ...utils.log import log_error
from .sync import (
    create_sync_state,
    is_team_memory_sync_available,
    pull_team_memory,
)
from .types import TeamMemorySyncPushResult

if TYPE_CHECKING:
    pass

DEBOUNCE_S = 2.0

_sync_state: Any = None
_debounce_handle: asyncio.TimerHandle | None = None
_push_task: asyncio.Task[None] | None = None
_loop: asyncio.AbstractEventLoop | None = None


def is_permanent_failure(r: TeamMemorySyncPushResult) -> bool:
    if r.error_type in ("no_oauth", "no_repo"):
        return True
    s = r.http_status
    return bool(s is not None and 400 <= s < 500 and s not in (409, 429))


async def start_team_memory_watcher(repo_slug: str) -> None:
    global _sync_state, _loop
    if not is_team_memory_sync_available():
        return
    _loop = asyncio.get_event_loop()
    _sync_state = create_sync_state()
    try:
        await pull_team_memory(_sync_state, repo_slug)
    except Exception as err:
        log_error(err if isinstance(err, Exception) else RuntimeError(str(err)))
    log_for_debugging(f"team-memory-watcher: ready (repo={repo_slug})")


async def notify_team_memory_write() -> None:
    _schedule_push_placeholder()


def _schedule_push_placeholder() -> None:
    """Debounce hook; full fs.watch parity is platform-specific."""
    global _debounce_handle, _loop
    if _loop is None:
        try:
            _loop = asyncio.get_event_loop()
        except RuntimeError:
            return

    if _debounce_handle:
        _debounce_handle.cancel()

    def _fire() -> None:
        log_for_debugging("team-memory-watcher: debounced push (stub)")

    _debounce_handle = _loop.call_later(DEBOUNCE_S, _fire)


async def stop_team_memory_watcher() -> None:
    global _debounce_handle, _push_task
    if _debounce_handle:
        _debounce_handle.cancel()
        _debounce_handle = None
    if _push_task and not _push_task.done():
        _push_task.cancel()
