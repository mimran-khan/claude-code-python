"""
TodoV2 task list refresh and hide-after-complete behavior.

Migrated from: hooks/useTasksV2.ts (core logic only; wire I/O via ports).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol


class TaskLike(Protocol):
    id: str
    status: str
    metadata: dict[str, Any] | None


class TasksV2Port(Protocol):
    def get_task_list_id(self) -> str: ...

    async def list_tasks(self, task_list_id: str) -> list[TaskLike]: ...

    async def reset_task_list(self, task_list_id: str) -> None: ...


HIDE_DELAY_S = 5.0
FALLBACK_POLL_S = 5.0


def _task_row_meta(task: TaskLike | Mapping[str, Any]) -> dict[str, Any] | None:
    if isinstance(task, Mapping):
        m = task.get("metadata")
        return m if isinstance(m, dict) else None
    meta = getattr(task, "metadata", None)
    return meta if isinstance(meta, dict) else None


def _task_row_status(task: TaskLike | Mapping[str, Any]) -> str:
    if isinstance(task, Mapping):
        s = task.get("status")
        return s if isinstance(s, str) else ""
    s = getattr(task, "status", None)
    return s if isinstance(s, str) else ""


@dataclass
class TasksV2Store:
    """
    In-memory snapshot + hide flag. Drive with :meth:`refresh` from a background task.

    File watching should call ``request_refresh`` (debounced by caller).
    """

    port: TasksV2Port
    _tasks: list[TaskLike] | None = None
    hidden: bool = False
    _hide_scheduled_monotonic: float | None = None
    _hide_task_list_id: str | None = None
    _listeners: list[Callable[[], None]] = field(default_factory=list)

    def get_snapshot(self) -> list[TaskLike] | None:
        return None if self.hidden else self._tasks

    def subscribe(self, fn: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(fn)

        def unsub() -> None:
            if fn in self._listeners:
                self._listeners.remove(fn)

        return unsub

    def _notify(self) -> None:
        for fn in self._listeners[:]:
            fn()

    async def refresh(self) -> None:
        """Fetch tasks, update hide timer, optional fallback poll loop step."""
        task_list_id = self.port.get_task_list_id()
        raw = await self.port.list_tasks(task_list_id)
        current = [t for t in raw if not (_task_row_meta(t) or {}).get("_internal")]
        self._tasks = current

        has_incomplete = any(_task_row_status(t) != "completed" for t in current)

        if has_incomplete or len(current) == 0:
            self.hidden = len(current) == 0
            self._hide_scheduled_monotonic = None
            self._hide_task_list_id = None
        elif not self.hidden:
            self._hide_scheduled_monotonic = time.monotonic()
            self._hide_task_list_id = task_list_id

        self._notify()

    async def tick_hide_timer(self) -> None:
        """Call periodically (e.g. once per second) to apply 5s hide + reset."""
        if self._hide_scheduled_monotonic is None or self._hide_task_list_id is None:
            return
        if time.monotonic() - self._hide_scheduled_monotonic < HIDE_DELAY_S:
            return
        scheduled_id = self._hide_task_list_id
        self._hide_scheduled_monotonic = None
        self._hide_task_list_id = None
        if self.port.get_task_list_id() != scheduled_id:
            return
        tasks = await self.port.list_tasks(scheduled_id)
        if len(tasks) > 0 and all(_task_row_status(t) == "completed" for t in tasks):
            await self.port.reset_task_list(scheduled_id)
            self._tasks = []
            self.hidden = True
            self._notify()


async def run_tasks_v2_refresh_loop(
    store: TasksV2Store,
    *,
    stop_event: asyncio.Event,
    poll_interval_s: float = FALLBACK_POLL_S,
) -> None:
    """Poll until stopped; skips sleep when tasks are all completed."""
    while not stop_event.is_set():
        await store.refresh()
        await store.tick_hide_timer()
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=poll_interval_s)
            break
        except TimeoutError:
            snap = store.get_snapshot()
            if snap is None:
                continue
            if all(_task_row_status(t) == "completed" for t in snap):
                await asyncio.wait_for(stop_event.wait(), timeout=poll_interval_s)
            continue


def collapse_expanded_tasks_when_hidden(
    *,
    tasks_snapshot: list[TaskLike] | None,
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
) -> None:
    if tasks_snapshot is not None:
        return

    def collapse(prev: dict[str, Any]) -> dict[str, Any]:
        if prev.get("expanded_view") != "tasks":
            return prev
        return {**prev, "expanded_view": "none"}

    set_app_state(collapse)
