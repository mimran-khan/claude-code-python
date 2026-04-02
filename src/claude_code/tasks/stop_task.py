"""
Stop a running background task (tool + SDK control path).

Migrated from: tasks/stopTask.ts
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import is_dataclass, replace
from typing import Any, Literal

from ..state.app_state import AppState
from ..utils.sdk_event_queue import emit_task_terminated_sdk
from .task import SetAppState, get_task_by_type


class StopTaskError(Exception):
    """Task could not be stopped."""

    def __init__(
        self,
        message: str,
        code: Literal["not_found", "not_running", "unsupported_type"],
    ) -> None:
        super().__init__(message)
        self.code = code


def is_local_shell_task(task: Mapping[str, Any] | Any) -> bool:
    """True if ``task`` is a local bash/shell task."""
    if isinstance(task, Mapping):
        return task.get("type") == "local_bash"
    return getattr(task, "type", None) == "local_bash"


def _merge_task_notified(task: Any) -> tuple[Any, bool]:
    """Return (new_task, changed) with notified=True if applicable."""
    if isinstance(task, dict):
        if task.get("notified"):
            return task, False
        return {**task, "notified": True}, True
    if is_dataclass(task) and not getattr(task, "notified", False):
        return replace(task, notified=True), True  # type: ignore[type-var]
    return task, False


async def stop_task(
    task_id: str,
    *,
    get_app_state: Callable[[], Any],
    set_app_state: SetAppState,
) -> dict[str, Any]:
    """
    Look up ``task_id``, ensure running, invoke task implementation ``kill``.

    Returns ``{task_id, task_type, command}``. Raises :class:`StopTaskError`.
    """
    app_state = get_app_state()
    tasks_map = getattr(app_state, "tasks", None) or {}
    raw_task = tasks_map.get(task_id)
    if raw_task is None:
        raise StopTaskError(f"No task found with ID: {task_id}", "not_found")

    task_view: Mapping[str, Any] = raw_task if isinstance(raw_task, Mapping) else vars(raw_task)

    status = task_view.get("status")
    if status != "running":
        raise StopTaskError(
            f"Task {task_id} is not running (status: {status})",
            "not_running",
        )

    task_type = task_view.get("type")
    impl = get_task_by_type(task_type) if task_type is not None else None
    if impl is None:
        raise StopTaskError(f"Unsupported task type: {task_type}", "unsupported_type")

    await impl.kill(task_id, set_app_state)

    if is_local_shell_task(task_view):
        suppressed = False

        def shell_notified_updater(prev: AppState) -> AppState:
            nonlocal suppressed
            tasks = dict(prev.tasks or {})
            existing = tasks.get(task_id)
            if existing is None:
                return prev
            new_task, changed = _merge_task_notified(existing)
            if not changed:
                return prev
            suppressed = True
            tasks[task_id] = new_task
            return replace(prev, tasks=tasks)

        set_app_state(shell_notified_updater)

        if suppressed:
            tool_use = task_view.get("toolUseId") or task_view.get("tool_use_id")
            emit_task_terminated_sdk(
                task_id,
                "stopped",
                {"tool_use_id": tool_use, "summary": task_view.get("description", "")},
            )

    command = task_view.get("command") if is_local_shell_task(task_view) else task_view.get("description")
    return {"task_id": task_id, "task_type": str(task_type), "command": command}
