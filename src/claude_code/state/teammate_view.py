"""
Teammate transcript view transitions.

Migrated from: state/teammateViewHelpers.ts
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Any

from ..tasks.task import is_terminal_task_status
from .app_state import AppState

PANEL_GRACE_MS = 30_000

SetAppState = Callable[[Callable[[AppState], AppState]], None]


def _is_local_agent(task: Any) -> bool:
    return isinstance(task, Mapping) and task.get("type") == "local_agent"


def _release_local_agent_task(task: Mapping[str, Any]) -> dict[str, Any]:
    status = task.get("status")
    terminal = is_terminal_task_status(status) if isinstance(status, str) else False  # type: ignore[arg-type]
    evict_after = (time.time() * 1000 + PANEL_GRACE_MS) if terminal else None
    return {
        **dict(task),
        "retain": False,
        "messages": None,
        "diskLoaded": False,
        "evictAfter": evict_after,
    }


def enter_teammate_view(task_id: str, set_app_state: SetAppState) -> None:
    """Focus transcript for ``task_id``; release previously retained local agent."""

    def updater(prev: AppState) -> AppState:
        tasks = dict(prev.tasks or {})
        task = tasks.get(task_id)
        prev_id = prev.viewing_agent_task_id
        prev_task = tasks.get(prev_id) if prev_id else None
        switching = (
            prev_id is not None
            and prev_id != task_id
            and _is_local_agent(prev_task)
            and bool((prev_task or {}).get("retain"))
        )
        needs_retain = _is_local_agent(task) and (
            not (task or {}).get("retain") or (task or {}).get("evictAfter") is not None
        )
        needs_view = prev.viewing_agent_task_id != task_id or prev.view_selection_mode != "viewing-agent"
        if not needs_retain and not needs_view and not switching:
            return prev
        new_tasks = tasks
        if switching or needs_retain:
            new_tasks = dict(tasks)
            if switching and prev_id and prev_task:
                new_tasks[prev_id] = _release_local_agent_task(prev_task)
            if needs_retain and task:
                new_tasks[task_id] = {**dict(task), "retain": True, "evictAfter": None}
        return replace(
            prev,
            viewing_agent_task_id=task_id,
            view_selection_mode="viewing-agent",
            tasks=new_tasks,
        )

    set_app_state(updater)


def exit_teammate_view(set_app_state: SetAppState) -> None:
    """Return to leader transcript; drop retain on viewed local agent."""

    def updater(prev: AppState) -> AppState:
        task_id = prev.viewing_agent_task_id
        cleared = replace(
            prev,
            viewing_agent_task_id=None,
            view_selection_mode="none",
        )
        if task_id is None:
            return prev if prev.view_selection_mode == "none" else cleared
        task = (prev.tasks or {}).get(task_id)
        if not _is_local_agent(task) or not (task or {}).get("retain"):
            return cleared
        new_tasks = dict(prev.tasks or {})
        new_tasks[task_id] = _release_local_agent_task(task)
        return replace(cleared, tasks=new_tasks)

    set_app_state(updater)


def stop_or_dismiss_agent(task_id: str, set_app_state: SetAppState) -> None:
    """Running → abort; terminal → dismiss (evict) and maybe exit view."""

    def updater(prev: AppState) -> AppState:
        tasks = dict(prev.tasks or {})
        task = tasks.get(task_id)
        if not _is_local_agent(task):
            return prev
        if task.get("status") == "running":
            ac = task.get("abortController")
            if ac is not None and hasattr(ac, "abort"):
                ac.abort()
            return prev
        if task.get("evictAfter") == 0:
            return prev
        viewing = prev.viewing_agent_task_id == task_id
        new_task = {**_release_local_agent_task(task), "evictAfter": 0}
        tasks[task_id] = new_task
        if viewing:
            return replace(
                prev,
                tasks=tasks,
                viewing_agent_task_id=None,
                view_selection_mode="none",
            )
        return replace(prev, tasks=tasks)

    set_app_state(updater)
