"""
Task type registry.

Migrated from: tasks.ts
"""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from typing import Any, Literal, Protocol

TaskType = Literal[
    "local_bash",
    "local_agent",
    "remote_agent",
    "in_process_teammate",
    "local_workflow",
    "monitor_mcp",
    "dream",
]

TaskStatus = Literal["pending", "running", "completed", "failed", "killed"]

_TASK_ID_PREFIXES: dict[str, str] = {
    "local_bash": "b",
    "local_agent": "a",
    "remote_agent": "r",
    "in_process_teammate": "t",
    "local_workflow": "w",
    "monitor_mcp": "m",
    "dream": "d",
}

_ALPHABET = string.digits + string.ascii_lowercase


def is_terminal_task_status(status: TaskStatus) -> bool:
    return status in ("completed", "failed", "killed")


@dataclass
class TaskHandle:
    task_id: str


class Task(Protocol):
    name: str
    type: TaskType

    async def kill(self, task_id: str, set_app_state: Any) -> None: ...


def generate_task_id(kind: TaskType) -> str:
    prefix = _TASK_ID_PREFIXES.get(kind, "x")
    tail = "".join(secrets.choice(_ALPHABET) for _ in range(8))
    return prefix + tail


def get_all_tasks() -> list[Task]:
    """Return registered task modules (wire LocalShellTask et al. when ported)."""
    return []


def get_task_by_type(task_type: TaskType) -> Task | None:
    for t in get_all_tasks():
        if t.type == task_type:
            return t
    return None
