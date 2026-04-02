"""
Task Types.

Type definitions for the task system.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    pass

# Task statuses
TaskStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "cancelled",
]

# Task types
TaskType = Literal[
    "shell",
    "agent",
    "workflow",
    "mcp",
    "remote",
]


@dataclass
class TaskConfig:
    """Configuration for a task."""

    type: TaskType = "shell"
    name: str = ""
    description: str = ""
    timeout_ms: int | None = None
    is_backgrounded: bool = False
    parent_task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of a task execution."""

    success: bool = True
    output: str = ""
    error: str | None = None
    exit_code: int | None = None
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskState:
    """State of a task."""

    task_id: str
    type: TaskType
    status: TaskStatus = "pending"
    name: str = ""
    description: str = ""

    # Timing
    created_at: float = 0.0
    started_at: float | None = None
    completed_at: float | None = None

    # Execution state (None = unspecified; False = foreground running per TS)
    is_backgrounded: bool | None = None
    parent_task_id: str | None = None
    child_task_ids: list[str] = field(default_factory=list)

    # Results
    result: TaskResult | None = None
    error: str | None = None

    # For agent tasks
    session_id: str | None = None
    agent_id: str | None = None
    model: str | None = None

    # Progress tracking
    progress: float = 0.0
    progress_message: str = ""

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_running(self) -> bool:
        """Check if task is currently running."""
        return self.status == "running"

    @property
    def is_completed(self) -> bool:
        """Check if task has completed (successfully or not)."""
        return self.status in ("completed", "failed", "cancelled")

    @property
    def is_successful(self) -> bool:
        """Check if task completed successfully."""
        return self.status == "completed"

    @property
    def duration_ms(self) -> int | None:
        """Get task duration in milliseconds."""
        if self.started_at is None:
            return None
        end_time = self.completed_at or time.time()
        return int((end_time - self.started_at) * 1000)


def is_background_task(task: TaskState | Mapping[str, Any]) -> bool:
    """Match ``tasks/types.ts`` ``isBackgroundTask`` (mapping or :class:`TaskState`)."""
    if isinstance(task, Mapping):
        status = task.get("status")
        if status not in ("running", "pending"):
            return False
        return not ("isBackgrounded" in task and task.get("isBackgrounded") is False)
    if task.status not in ("running", "pending"):
        return False
    return getattr(task, "is_backgrounded", None) is not False
