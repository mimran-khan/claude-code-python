"""
Task Update Tool Implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import DESCRIPTION, TASK_UPDATE_TOOL_NAME


class TaskUpdateInput(BaseModel):
    """Input parameters for task update tool."""

    task_id: str = Field(
        ...,
        alias="taskId",
        description="The task ID to update.",
    )
    status: Literal["pending", "in_progress", "completed", "deleted"] | None = Field(
        default=None,
        description="The new status.",
    )
    subject: str | None = Field(
        default=None,
        description="New task title.",
    )
    description: str | None = Field(
        default=None,
        description="New task description.",
    )
    active_form: str | None = Field(
        default=None,
        alias="activeForm",
        description="Present continuous form for spinner.",
    )
    owner: str | None = Field(
        default=None,
        description="Task owner (agent name).",
    )
    add_blocks: list[str] | None = Field(
        default=None,
        alias="addBlocks",
        description="Task IDs that cannot start until this one completes.",
    )
    add_blocked_by: list[str] | None = Field(
        default=None,
        alias="addBlockedBy",
        description="Task IDs that must complete before this one can start.",
    )


@dataclass
class TaskUpdateSuccess:
    """Successful task update result."""

    type: Literal["success"] = "success"
    task_id: str = ""
    message: str = ""


@dataclass
class TaskUpdateError:
    """Failed task update result."""

    type: Literal["error"] = "error"
    task_id: str = ""
    error: str = ""


TaskUpdateOutput = TaskUpdateSuccess | TaskUpdateError


class TaskUpdateTool(Tool[TaskUpdateInput, TaskUpdateOutput]):
    """
    Tool for updating tasks.
    """

    # Reference to shared task storage
    _tasks: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return TASK_UPDATE_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "taskId": {
                    "type": "string",
                    "description": "The task ID to update.",
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "deleted"],
                    "description": "The new status.",
                },
                "subject": {
                    "type": "string",
                    "description": "New task title.",
                },
                "description": {
                    "type": "string",
                    "description": "New task description.",
                },
                "activeForm": {
                    "type": "string",
                    "description": "Present continuous form for spinner.",
                },
                "owner": {
                    "type": "string",
                    "description": "Task owner.",
                },
                "addBlocks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Task IDs blocked by this task.",
                },
                "addBlockedBy": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Task IDs that block this task.",
                },
            },
            "required": ["taskId"],
        }

    def is_read_only(self, input_data: TaskUpdateInput) -> bool:
        return True

    async def call(
        self,
        input_data: TaskUpdateInput,
        context: Any,
    ) -> ToolResult[TaskUpdateOutput]:
        """Execute the task update operation."""
        task_id = input_data.task_id

        if task_id not in self._tasks:
            return ToolResult(
                success=False,
                output=TaskUpdateError(
                    task_id=task_id,
                    error=f"Task not found: {task_id}",
                ),
            )

        task = self._tasks[task_id]

        # Handle deletion
        if input_data.status == "deleted":
            del self._tasks[task_id]
            return ToolResult(
                success=True,
                output=TaskUpdateSuccess(
                    task_id=task_id,
                    message=f"Deleted task {task_id}",
                ),
            )

        # Update fields
        if input_data.status is not None:
            task["status"] = input_data.status
        if input_data.subject is not None:
            task["subject"] = input_data.subject
        if input_data.description is not None:
            task["description"] = input_data.description
        if input_data.active_form is not None:
            task["active_form"] = input_data.active_form
        if input_data.owner is not None:
            task["owner"] = input_data.owner
        if input_data.add_blocks:
            task.setdefault("blocks", []).extend(input_data.add_blocks)
        if input_data.add_blocked_by:
            task.setdefault("blocked_by", []).extend(input_data.add_blocked_by)

        return ToolResult(
            success=True,
            output=TaskUpdateSuccess(
                task_id=task_id,
                message=f"Updated task {task_id}",
            ),
        )

    def user_facing_name(self, input_data: TaskUpdateInput | None = None) -> str:
        return "Task"
