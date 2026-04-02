"""
Watch tasks directory and claim the next available task.

Migrated from: hooks/useTaskListWatcher.ts
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


class TaskListTask(Protocol):
    id: str
    status: str
    owner: str | None
    blocked_by: list[str]
    subject: str
    description: str | None


class TaskListPort(Protocol):
    async def ensure_tasks_dir(self, task_list_id: str | None) -> None: ...

    def get_tasks_dir(self, task_list_id: str | None) -> str: ...

    async def list_tasks(self, task_list_id: str | None) -> list[TaskListTask]: ...

    async def claim_task(self, task_list_id: str | None, task_id: str, agent_id: str) -> Any: ...

    async def update_task(self, task_list_id: str | None, task_id: str, **kwargs: Any) -> None: ...


DEBOUNCE_S = 1.0
DEFAULT_TASK_LIST_ID = "default"


@dataclass
class TaskListWatcherState:
    current_task_id: str | None = None
    debounce_handle: asyncio.TimerHandle | None = None


def find_available_task(tasks: list[TaskListTask]) -> TaskListTask | None:
    unresolved = {t.id for t in tasks if t.status != "completed"}
    for task in tasks:
        if task.status != "pending" or task.owner:
            continue
        if all(b not in unresolved for b in task.blocked_by):
            return task
    return None


def format_task_as_prompt(task: TaskListTask) -> str:
    prompt = f"Complete all open tasks. Start with task #{task.id}: \n\n {task.subject}"
    if task.description:
        prompt += f"\n\n{task.description}"
    return prompt


async def check_for_tasks(
    port: TaskListPort,
    state: TaskListWatcherState,
    *,
    task_list_id: str | None,
    agent_id: str,
    is_loading: bool,
    on_submit_task: Callable[[str], bool],
) -> None:
    if task_list_id is None or is_loading:
        return
    tasks = await port.list_tasks(task_list_id)
    if state.current_task_id is not None:
        cur = next((t for t in tasks if t.id == state.current_task_id), None)
        if cur is None or cur.status == "completed":
            state.current_task_id = None
        else:
            return
    avail = find_available_task(tasks)
    if avail is None:
        return
    result = await port.claim_task(task_list_id, avail.id, agent_id)
    success = getattr(result, "success", True)
    if isinstance(result, dict):
        success = bool(result.get("success", True))
    if not success:
        return
    state.current_task_id = avail.id
    prompt = format_task_as_prompt(avail)
    if not on_submit_task(prompt):
        await port.update_task(task_list_id, avail.id, owner=None)
        state.current_task_id = None
