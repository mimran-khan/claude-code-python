"""
Skill / command directory change debouncing (chokidar → async debounce).

Migrated from: utils/skills/skillChangeDetector.ts
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from ..signal import VoidSignal

_skills_changed = VoidSignal()
_reload_task: asyncio.Task[None] | None = None
_pending: set[str] = set()
_lock = asyncio.Lock()
_initialized = False
_DEBOUNCE_MS = 0.3


async def initialize() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True


async def dispose() -> None:
    global _initialized, _reload_task
    _initialized = False
    if _reload_task and not _reload_task.done():
        _reload_task.cancel()
    _reload_task = None
    _pending.clear()
    _skills_changed.clear()


def subscribe(listener: Callable[[], None]) -> Callable[[], None]:
    return _skills_changed.subscribe(listener)


async def _debounced_emit() -> None:
    await asyncio.sleep(_DEBOUNCE_MS)
    async with _lock:
        _pending.clear()
    _skills_changed.emit()


def notify_skill_paths_changed(paths: list[str]) -> None:
    """Schedule a debounced ``skills_changed`` emit (tests / manual integration)."""
    global _reload_task
    _pending.update(paths)
    if _reload_task is None or _reload_task.done():
        _reload_task = asyncio.create_task(_debounced_emit())


async def reset_for_testing() -> None:
    await dispose()
    global _initialized
    _initialized = False


skill_change_detector = {
    "initialize": initialize,
    "dispose": dispose,
    "subscribe": subscribe,
    "resetForTesting": reset_for_testing,
}
