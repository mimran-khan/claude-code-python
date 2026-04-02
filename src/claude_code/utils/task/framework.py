"""
Task framework utilities.

Migrated from: utils/task/framework.ts
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

# Standard polling interval for all tasks
POLL_INTERVAL_MS = 1000

# Duration to display killed tasks before eviction
STOPPED_DISPLAY_MS = 3_000

# Grace period for terminal local_agent tasks in the coordinator panel
PANEL_GRACE_MS = 30_000


@dataclass
class TaskAttachment:
    """Attachment type for task status updates."""

    type: Literal["task_status"] = "task_status"
    task_id: str = ""
    tool_use_id: str | None = None
    task_type: str = ""  # TaskType
    status: str = ""  # TaskStatus
    description: str = ""
    delta_summary: str | None = None  # New output since last attachment


T = TypeVar("T")
SetAppState = Callable[[Callable[[Any], Any]], None]


def update_task_state(
    task_id: str,
    set_app_state: SetAppState,
    updater: Callable[[T], T],
) -> None:
    """Update a task's state in AppState.

    Helper function for task implementations.
    Generic to allow type-safe updates for specific task types.
    """

    def state_updater(prev: Any) -> Any:
        tasks = prev.get("tasks", {}) if isinstance(prev, dict) else getattr(prev, "tasks", {})
        task = tasks.get(task_id)
        if task is None:
            return prev

        updated = updater(task)
        if updated is task:
            # Updater returned the same reference - skip update
            return prev

        new_tasks = {**tasks, task_id: updated}

        if isinstance(prev, dict):
            return {**prev, "tasks": new_tasks}
        else:
            # Assume dataclass-like
            import copy

            new_prev = copy.copy(prev)
            new_prev.tasks = new_tasks
            return new_prev

    set_app_state(state_updater)


def register_task(task: Any, set_app_state: SetAppState) -> None:
    """Register a new task in AppState."""

    def state_updater(prev: Any) -> Any:
        tasks = prev.get("tasks", {}) if isinstance(prev, dict) else getattr(prev, "tasks", {})
        task_id = task.get("id") if isinstance(task, dict) else getattr(task, "id", None)

        existing = tasks.get(task_id)

        # Carry forward UI-held state on re-register
        if existing and hasattr(existing, "retain"):
            merged = (
                {
                    **task,
                    "retain": existing.retain,
                    "start_time": existing.start_time,
                    "messages": existing.messages,
                    "disk_loaded": existing.disk_loaded,
                    "pending_messages": existing.pending_messages,
                }
                if isinstance(task, dict)
                else task
            )
        else:
            merged = task

        new_tasks = {**tasks, task_id: merged}

        if isinstance(prev, dict):
            return {**prev, "tasks": new_tasks}
        else:
            import copy

            new_prev = copy.copy(prev)
            new_prev.tasks = new_tasks
            return new_prev

    set_app_state(state_updater)


def remove_task(task_id: str, set_app_state: SetAppState) -> None:
    """Remove a task from AppState."""

    def state_updater(prev: Any) -> Any:
        tasks = prev.get("tasks", {}) if isinstance(prev, dict) else getattr(prev, "tasks", {})

        if task_id not in tasks:
            return prev

        new_tasks = {k: v for k, v in tasks.items() if k != task_id}

        if isinstance(prev, dict):
            return {**prev, "tasks": new_tasks}
        else:
            import copy

            new_prev = copy.copy(prev)
            new_prev.tasks = new_tasks
            return new_prev

    set_app_state(state_updater)
