"""
Task definitions and management.

This module defines the Task type and related utilities for background
task execution (shell commands, agents, workflows, etc.).

Migrated from: Task.ts (125 lines) + tasks.ts (39 lines)
"""

from __future__ import annotations

import os
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol

if TYPE_CHECKING:
    pass


# Task types
TaskType = Literal[
    "local_bash",
    "local_agent",
    "remote_agent",
    "in_process_teammate",
    "local_workflow",
    "monitor_mcp",
    "dream",
]

# Task status
TaskStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "killed",
]


def is_terminal_task_status(status: TaskStatus) -> bool:
    """
    Check if a task is in a terminal state and will not transition further.

    Used to guard against injecting messages into dead teammates, evicting
    finished tasks from AppState, and orphan-cleanup paths.
    """
    return status in ("completed", "failed", "killed")


@dataclass
class TaskHandle:
    """Handle to a running task."""

    task_id: str
    cleanup: Callable[[], None] | None = None


SetAppState = Callable[[Callable[[Any], Any]], None]


@dataclass
class TaskContext:
    """Context for task execution."""

    abort_controller: Any  # AbortController equivalent
    get_app_state: Callable[[], Any]  # AppState
    set_app_state: SetAppState


@dataclass
class TaskStateBase:
    """Base fields shared by all task states."""

    id: str
    type: TaskType
    status: TaskStatus
    description: str
    start_time: float  # milliseconds since epoch
    output_file: str
    output_offset: int = 0
    notified: bool = False
    tool_use_id: str | None = None
    end_time: float | None = None
    total_paused_ms: float | None = None


@dataclass
class LocalShellSpawnInput:
    """Input for spawning a local shell task."""

    command: str
    description: str
    timeout: int | None = None
    tool_use_id: str | None = None
    agent_id: str | None = None
    kind: Literal["bash", "monitor"] | None = None


class Task(Protocol):
    """
    Protocol for task implementations.

    Each task type must implement this protocol.
    """

    name: str
    type: TaskType

    async def kill(self, task_id: str, set_app_state: SetAppState) -> None:
        """Kill a running task."""
        ...


# Task ID prefixes
_TASK_ID_PREFIXES: dict[str, str] = {
    "local_bash": "b",
    "local_agent": "a",
    "remote_agent": "r",
    "in_process_teammate": "t",
    "local_workflow": "w",
    "monitor_mcp": "m",
    "dream": "d",
}


def _get_task_id_prefix(task_type: TaskType) -> str:
    """Get the ID prefix for a task type."""
    return _TASK_ID_PREFIXES.get(task_type, "x")


# Case-insensitive-safe alphabet (digits + lowercase) for task IDs.
# 36^8 ≈ 2.8 trillion combinations, sufficient to resist brute-force symlink attacks.
_TASK_ID_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def generate_task_id(task_type: TaskType) -> str:
    """Generate a unique task ID for the given type."""
    prefix = _get_task_id_prefix(task_type)
    random_bytes = secrets.token_bytes(8)
    suffix = "".join(_TASK_ID_ALPHABET[b % len(_TASK_ID_ALPHABET)] for b in random_bytes)
    return prefix + suffix


def get_task_output_path(task_id: str) -> str:
    """Get the output file path for a task."""
    # Use a temp directory for task output
    from ..utils.path import get_temp_dir

    temp_dir = get_temp_dir()
    return os.path.join(temp_dir, "tasks", f"{task_id}.output")


def create_task_state_base(
    task_id: str,
    task_type: TaskType,
    description: str,
    tool_use_id: str | None = None,
) -> TaskStateBase:
    """Create a base task state with default values."""
    return TaskStateBase(
        id=task_id,
        type=task_type,
        status="pending",
        description=description,
        tool_use_id=tool_use_id,
        start_time=time.time() * 1000,  # Convert to milliseconds
        output_file=get_task_output_path(task_id),
    )


# Task registry
_registered_tasks: list[Task] = []


def register_task(task: Task) -> None:
    """Register a task implementation."""
    _registered_tasks.append(task)


def get_all_tasks() -> list[Task]:
    """Get all registered tasks."""
    return _registered_tasks.copy()


def get_task_by_type(task_type: TaskType) -> Task | None:
    """Get a task implementation by its type."""
    for task in _registered_tasks:
        if task.type == task_type:
            return task
    return None
