"""
Task Create Tool Implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import DESCRIPTION, TASK_CREATE_TOOL_NAME


class TaskCreateInput(BaseModel):
    """Input parameters for task create tool."""

    subject: str = Field(
        ...,
        description="A brief, actionable title in imperative form.",
    )
    description: str = Field(
        default="",
        description="What needs to be done.",
    )
    active_form: str | None = Field(
        default=None,
        alias="activeForm",
        description="Present continuous form for spinner display.",
    )


@dataclass
class TaskCreateSuccess:
    """Successful task creation result."""

    type: Literal["success"] = "success"
    task_id: str = ""
    subject: str = ""
    message: str = ""


@dataclass
class TaskCreateError:
    """Failed task creation result."""

    type: Literal["error"] = "error"
    error: str = ""


TaskCreateOutput = TaskCreateSuccess | TaskCreateError


class TaskCreateTool(Tool[TaskCreateInput, TaskCreateOutput]):
    """
    Tool for creating tasks.
    """

    _task_counter: int = 0
    _tasks: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return TASK_CREATE_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "A brief, actionable title.",
                },
                "description": {
                    "type": "string",
                    "description": "What needs to be done.",
                },
                "activeForm": {
                    "type": "string",
                    "description": "Present continuous form for spinner.",
                },
            },
            "required": ["subject"],
        }

    def is_read_only(self, input_data: TaskCreateInput) -> bool:
        return True

    async def call(
        self,
        input_data: TaskCreateInput,
        context: Any,
    ) -> ToolResult[TaskCreateOutput]:
        """Execute the task create operation."""
        self._task_counter += 1
        task_id = str(self._task_counter)

        task = {
            "id": task_id,
            "subject": input_data.subject,
            "description": input_data.description,
            "active_form": input_data.active_form,
            "status": "pending",
            "owner": None,
            "blocked_by": [],
            "blocks": [],
        }

        self._tasks[task_id] = task

        return ToolResult(
            success=True,
            output=TaskCreateSuccess(
                task_id=task_id,
                subject=input_data.subject,
                message=f"Created task {task_id}: {input_data.subject}",
            ),
        )

    def user_facing_name(self, input_data: TaskCreateInput | None = None) -> str:
        return "Task"
