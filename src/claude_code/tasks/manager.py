"""
Task Manager.

Manages task lifecycle and execution.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .types import (
    TaskConfig,
    TaskResult,
    TaskState,
    TaskStatus,
    TaskType,
)

if TYPE_CHECKING:
    from collections.abc import Coroutine


@dataclass
class TaskManager:
    """Manager for task lifecycle and execution."""

    _tasks: dict[str, TaskState] = field(default_factory=dict)
    _running_tasks: dict[str, asyncio.Task[Any]] = field(default_factory=dict)

    def create(
        self,
        config: TaskConfig,
        *,
        task_id: str | None = None,
    ) -> TaskState:
        """Create a new task.

        Args:
            config: Task configuration
            task_id: Optional task ID (generated if not provided)

        Returns:
            The created task state
        """
        if task_id is None:
            task_id = str(uuid.uuid4())

        task = TaskState(
            task_id=task_id,
            type=config.type,
            status="pending",
            name=config.name,
            description=config.description,
            created_at=time.time(),
            is_backgrounded=config.is_backgrounded,
            parent_task_id=config.parent_task_id,
            metadata=config.metadata,
        )

        self._tasks[task_id] = task

        # Track child relationship
        if config.parent_task_id and config.parent_task_id in self._tasks:
            self._tasks[config.parent_task_id].child_task_ids.append(task_id)

        return task

    def get(self, task_id: str) -> TaskState | None:
        """Get a task by ID.

        Args:
            task_id: The task ID

        Returns:
            The task state, or None if not found
        """
        return self._tasks.get(task_id)

    def list(
        self,
        *,
        status: TaskStatus | None = None,
        task_type: TaskType | None = None,
        is_backgrounded: bool | None = None,
    ) -> list[TaskState]:
        """List tasks with optional filtering.

        Args:
            status: Filter by status
            task_type: Filter by type
            is_backgrounded: Filter by background status

        Returns:
            List of matching tasks
        """
        tasks = list(self._tasks.values())

        if status is not None:
            tasks = [t for t in tasks if t.status == status]

        if task_type is not None:
            tasks = [t for t in tasks if t.type == task_type]

        if is_backgrounded is not None:
            tasks = [t for t in tasks if t.is_backgrounded == is_backgrounded]

        return tasks

    async def run(
        self,
        task_id: str,
        coro: Coroutine[Any, Any, TaskResult],
    ) -> TaskResult:
        """Run a task asynchronously.

        Args:
            task_id: The task ID
            coro: The coroutine to run

        Returns:
            The task result
        """
        task = self.get(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        task.status = "running"
        task.started_at = time.time()

        try:
            # Wrap the coroutine in an asyncio task
            async_task = asyncio.create_task(coro)
            self._running_tasks[task_id] = async_task

            result = await async_task

            task.status = "completed"
            task.result = result

            return result

        except asyncio.CancelledError:
            task.status = "cancelled"
            task.error = "Task was cancelled"
            raise

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.result = TaskResult(
                success=False,
                error=str(e),
            )
            raise

        finally:
            task.completed_at = time.time()
            self._running_tasks.pop(task_id, None)

    async def cancel(self, task_id: str) -> bool:
        """Cancel a running task.

        Args:
            task_id: The task ID

        Returns:
            True if task was cancelled
        """
        task = self.get(task_id)
        if task is None:
            return False

        if task.status != "running":
            return False

        async_task = self._running_tasks.get(task_id)
        if async_task:
            async_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await async_task

        task.status = "cancelled"
        task.completed_at = time.time()

        return True

    def update_progress(
        self,
        task_id: str,
        progress: float,
        message: str = "",
    ) -> None:
        """Update task progress.

        Args:
            task_id: The task ID
            progress: Progress value (0.0 to 1.0)
            message: Optional progress message
        """
        task = self.get(task_id)
        if task is None:
            return

        task.progress = min(1.0, max(0.0, progress))
        task.progress_message = message

    def background(self, task_id: str) -> bool:
        """Move a task to background.

        Args:
            task_id: The task ID

        Returns:
            True if task was backgrounded
        """
        task = self.get(task_id)
        if task is None:
            return False

        task.is_backgrounded = True
        return True

    def foreground(self, task_id: str) -> bool:
        """Move a task to foreground.

        Args:
            task_id: The task ID

        Returns:
            True if task was foregrounded
        """
        task = self.get(task_id)
        if task is None:
            return False

        task.is_backgrounded = False
        return True

    def remove(self, task_id: str) -> bool:
        """Remove a completed task.

        Args:
            task_id: The task ID

        Returns:
            True if task was removed
        """
        task = self.get(task_id)
        if task is None:
            return False

        if task.status == "running":
            return False

        del self._tasks[task_id]
        return True

    def clear_completed(self) -> int:
        """Remove all completed tasks.

        Returns:
            Number of tasks removed
        """
        completed = [t.task_id for t in self._tasks.values() if t.status in ("completed", "failed", "cancelled")]

        for task_id in completed:
            del self._tasks[task_id]

        return len(completed)


# Global task manager
_default_manager: TaskManager | None = None


def get_default_manager() -> TaskManager:
    """Get the default task manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = TaskManager()
    return _default_manager


def create_task(
    config: TaskConfig,
    *,
    task_id: str | None = None,
    manager: TaskManager | None = None,
) -> TaskState:
    """Create a new task."""
    if manager is None:
        manager = get_default_manager()
    return manager.create(config, task_id=task_id)


def get_task(
    task_id: str,
    *,
    manager: TaskManager | None = None,
) -> TaskState | None:
    """Get a task by ID."""
    if manager is None:
        manager = get_default_manager()
    return manager.get(task_id)


async def cancel_task(
    task_id: str,
    *,
    manager: TaskManager | None = None,
) -> bool:
    """Cancel a running task."""
    if manager is None:
        manager = get_default_manager()
    return await manager.cancel(task_id)


def list_tasks(
    *,
    status: TaskStatus | None = None,
    task_type: TaskType | None = None,
    manager: TaskManager | None = None,
) -> list[TaskState]:
    """List tasks with optional filtering."""
    if manager is None:
        manager = get_default_manager()
    return manager.list(status=status, task_type=task_type)
