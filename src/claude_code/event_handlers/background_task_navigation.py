"""
Shift+Up/Down teammate / background task navigation.

Migrated from: hooks/useBackgroundTaskNavigation.ts
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast


def _task_get(task: Any, key: str, default: Any = None) -> Any:
    if isinstance(task, Mapping):
        return task.get(key, default)
    return getattr(task, key, default)


def _task_id(task: Any) -> str | None:
    tid = _task_get(task, "id")
    return tid if isinstance(tid, str) else None


@dataclass(frozen=True)
class BackgroundNavKeyEvent:
    key: str
    shift: bool = False


@dataclass
class BackgroundNavOptions:
    """Optional callback when only non-teammate background tasks exist."""

    on_open_background_tasks: Callable[[], None] | None = None


def step_teammate_selection(
    delta: Literal[1, -1],
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
    *,
    running_teammate_count: int,
) -> None:
    if running_teammate_count == 0:
        return

    def go(prev: dict[str, Any]) -> dict[str, Any]:
        if prev.get("expanded_view") != "teammates":
            return {
                **prev,
                "expanded_view": "teammates",
                "view_selection_mode": "selecting-agent",
                "selected_ip_agent_index": -1,
            }
        max_idx = running_teammate_count
        cur = int(prev.get("selected_ip_agent_index", -1))
        nxt = (-1 if cur >= max_idx else cur + 1) if delta == 1 else max_idx if cur <= -1 else cur - 1
        return {
            **prev,
            "selected_ip_agent_index": nxt,
            "view_selection_mode": "selecting-agent",
        }

    set_app_state(go)


def clamp_teammate_selection_after_count_change(
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
    *,
    prev_count: int,
    current_count: int,
) -> None:
    def clamp(prev: dict[str, Any]) -> dict[str, Any]:
        sel_ip = int(prev.get("selected_ip_agent_index", -1))
        if current_count == 0 and prev_count > 0 and sel_ip != -1:
            if prev.get("view_selection_mode") == "viewing-agent":
                return {**prev, "selected_ip_agent_index": -1}
            return {**prev, "selected_ip_agent_index": -1, "view_selection_mode": "none"}
        exp = prev.get("expanded_view")
        max_index = current_count if exp == "teammates" else max(0, current_count - 1)
        sel = int(prev.get("selected_ip_agent_index", -1))
        if current_count > 0 and sel > max_index:
            return {**prev, "selected_ip_agent_index": max_index}
        return prev

    set_app_state(clamp)


def handle_background_task_keydown(
    event: BackgroundNavKeyEvent,
    *,
    tasks: Mapping[str, Any],
    view_selection_mode: str,
    viewing_agent_task_id: str | None,
    selected_ip_agent_index: int,
    teammate_tasks: list[Any],
    teammate_count: int,
    has_non_teammate_background_tasks: bool,
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
    options: BackgroundNavOptions | None = None,
    enter_teammate_view: Callable[[str, Callable[..., None]], None] | None = None,
    exit_teammate_view: Callable[[Callable[..., None]], None] | None = None,
    kill_teammate: Callable[[str, Callable[..., None]], Any] | None = None,
) -> bool:
    if event.key == "escape" and view_selection_mode == "viewing-agent":
        tid = viewing_agent_task_id
        if tid:
            task = tasks.get(tid)
            is_tm = task is not None and _task_get(task, "type") == "in_process_teammate"
            if is_tm and _task_get(task, "status") == "running":
                ac = _task_get(task, "current_work_abort_controller") or _task_get(
                    task,
                    "currentWorkAbortController",
                )
                if ac is not None and hasattr(ac, "abort"):
                    cast(Any, ac).abort()
                return True
        if exit_teammate_view is not None:
            exit_teammate_view(set_app_state)
        return True

    if event.key == "escape" and view_selection_mode == "selecting-agent":
        set_app_state(lambda p: {**p, "view_selection_mode": "none", "selected_ip_agent_index": -1})
        return True

    if event.shift and event.key in ("up", "down"):
        if teammate_count > 0:
            step_teammate_selection(
                1 if event.key == "down" else -1,
                set_app_state,
                running_teammate_count=teammate_count,
            )
        elif has_non_teammate_background_tasks and options is not None and options.on_open_background_tasks:
            options.on_open_background_tasks()
        return True

    if event.key == "f" and view_selection_mode == "selecting-agent" and teammate_count > 0:
        idx = selected_ip_agent_index
        if 0 <= idx < len(teammate_tasks) and enter_teammate_view is not None:
            tid = _task_id(teammate_tasks[idx])
            if tid:
                enter_teammate_view(tid, set_app_state)
        return True

    if event.key == "return" and view_selection_mode == "selecting-agent":
        idx = selected_ip_agent_index
        if idx == -1:
            if exit_teammate_view is not None:
                exit_teammate_view(set_app_state)
        elif idx >= teammate_count:
            set_app_state(
                lambda p: {
                    **p,
                    "expanded_view": "none",
                    "view_selection_mode": "none",
                    "selected_ip_agent_index": -1,
                }
            )
        elif 0 <= idx < len(teammate_tasks) and enter_teammate_view is not None:
            tid = _task_id(teammate_tasks[idx])
            if tid:
                enter_teammate_view(tid, set_app_state)
        return True

    is_k_kill = event.key == "k" and view_selection_mode == "selecting-agent" and selected_ip_agent_index >= 0
    if is_k_kill:
        idx = selected_ip_agent_index
        if 0 <= idx < len(teammate_tasks) and kill_teammate is not None:
            t = teammate_tasks[idx]
            if _task_get(t, "status") == "running":
                tid = _task_id(t)
                if tid:
                    kill_teammate(tid, set_app_state)
        return True

    return False
