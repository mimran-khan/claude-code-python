"""
Task List Tool Implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel

from ..base import Tool, ToolResult
from .prompt import DESCRIPTION, TASK_LIST_TOOL_NAME


class TaskListInput(BaseModel):
    """Input parameters for task list tool."""

    pass  # No required inputs


@dataclass
class TaskSummary:
    """Summary of a task."""

    id: str = ""
    subject: str = ""
    status: str = "pending"
    owner: str | None = None
    blocked_by: list[str] = field(default_factory=list)


@dataclass
class TaskListSuccess:
    """Successful task list result."""

    type: Literal["success"] = "success"
    tasks: list[TaskSummary] = field(default_factory=list)
    total: int = 0


TaskListOutput = TaskListSuccess


class TaskListTool(Tool[TaskListInput, TaskListOutput]):
    """
    Tool for listing tasks.
    """

    # Reference to shared task storage (would be injected in real impl)
    _tasks: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return TASK_LIST_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    def is_read_only(self, input_data: TaskListInput) -> bool:
        return True

    async def call(
        self,
        input_data: TaskListInput,
        context: Any,
    ) -> ToolResult[TaskListOutput]:
        """Execute the task list operation."""
        tasks = [
            TaskSummary(
                id=task["id"],
                subject=task["subject"],
                status=task["status"],
                owner=task.get("owner"),
                blocked_by=task.get("blocked_by", []),
            )
            for task in self._tasks.values()
        ]

        return ToolResult(
            success=True,
            output=TaskListSuccess(
                tasks=tasks,
                total=len(tasks),
            ),
        )

    def user_facing_name(self, input_data: TaskListInput | None = None) -> str:
        return "Tasks"
