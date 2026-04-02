"""
Ctrl+B session backgrounding / foreground sync.

Migrated from: hooks/useSessionBackgrounding.ts
"""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class SessionBackgroundingDeps(Protocol):
    """Narrow protocol for state updates (implement with your AppState)."""

    def set_messages(self, fn: Callable[[list[Any]], list[Any]]) -> None: ...

    def set_is_loading(self, loading: bool) -> None: ...

    def reset_loading_state(self) -> None: ...

    def set_abort_controller(self, controller: Any | None) -> None: ...

    def on_background_query(self) -> None: ...


@dataclass
class LocalAgentTaskView:
    """Minimal fields read from a foregrounded local_agent task."""

    status: str
    messages: list[Any] | None = None
    abort_controller: Any | None = None


def handle_background_session_key(
    *,
    foregrounded_task_id: str | None,
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
    deps: SessionBackgroundingDeps,
) -> None:
    """User pressed background hotkey: re-background task or spawn background query."""
    if foregrounded_task_id:

        def re_bg(prev: dict[str, Any]) -> dict[str, Any]:
            tid = prev.get("foregrounded_task_id")
            if not tid:
                return prev
            tasks: MutableMapping[str, Any] = prev.get("tasks") or {}
            task = tasks.get(tid)
            if not task:
                return {**prev, "foregrounded_task_id": None}
            return {
                **prev,
                "foregrounded_task_id": None,
                "tasks": {**dict(tasks), tid: {**task, "is_backgrounded": True}},
            }

        set_app_state(re_bg)
        deps.set_messages(lambda _: [])
        deps.reset_loading_state()
        deps.set_abort_controller(None)
        return

    deps.on_background_query()


def sync_foregrounded_local_agent_task(
    *,
    foregrounded_task_id: str | None,
    foregrounded_task: LocalAgentTaskView | None,
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
    deps: SessionBackgroundingDeps,
    last_synced_len: list[int],
) -> None:
    """
    Mirror useEffect: sync messages + loading from foregrounded local_agent task.

    ``last_synced_len`` is a one-element box for message length watermark.
    """
    if not foregrounded_task_id:
        last_synced_len[0] = 0
        return

    if foregrounded_task is None:
        set_app_state(lambda prev: {**prev, "foregrounded_task_id": None})
        deps.reset_loading_state()
        last_synced_len[0] = 0
        return

    task_messages = foregrounded_task.messages or []
    if len(task_messages) != last_synced_len[0]:
        last_synced_len[0] = len(task_messages)
        deps.set_messages(lambda _: list(task_messages))

    if foregrounded_task.status == "running":
        ac = foregrounded_task.abort_controller
        signal = getattr(ac, "signal", None) if ac is not None else None
        aborted = getattr(signal, "aborted", False) if signal is not None else False
        if aborted:

            def clear_fg(prev: dict[str, Any]) -> dict[str, Any]:
                tid = prev.get("foregrounded_task_id")
                if not tid:
                    return prev
                tasks = dict(prev.get("tasks") or {})
                t = tasks.get(tid)
                if not t:
                    return {**prev, "foregrounded_task_id": None}
                return {
                    **prev,
                    "foregrounded_task_id": None,
                    "tasks": {**tasks, tid: {**t, "is_backgrounded": True}},
                }

            set_app_state(clear_fg)
            deps.reset_loading_state()
            deps.set_abort_controller(None)
            last_synced_len[0] = 0
            return

        deps.set_is_loading(True)
        if ac is not None:
            deps.set_abort_controller(ac)
        return

    def complete_fg(prev: dict[str, Any]) -> dict[str, Any]:
        tid = prev.get("foregrounded_task_id")
        if not tid:
            return prev
        tasks = dict(prev.get("tasks") or {})
        t = tasks.get(tid)
        if not t:
            return {**prev, "foregrounded_task_id": None}
        return {
            **prev,
            "foregrounded_task_id": None,
            "tasks": {**tasks, tid: {**t, "is_backgrounded": True}},
        }

    set_app_state(complete_fg)
    deps.reset_loading_state()
    deps.set_abort_controller(None)
    last_synced_len[0] = 0
