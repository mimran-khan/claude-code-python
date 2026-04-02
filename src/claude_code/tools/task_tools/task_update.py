"""Task Update tool implementation."""

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

TASK_UPDATE_TOOL_NAME = "task_update"


@dataclass
class TaskUpdateOutput:
    """Output from task update."""

    task_id: str
    success: bool
    message: str


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {
            "type": "string",
            "description": "ID of the task to update",
        },
        "status": {
            "type": "string",
            "description": "New status for the task",
        },
        "result": {
            "type": "string",
            "description": "Result data",
        },
    },
    "required": ["task_id"],
}


class TaskUpdateTool(Tool):
    """Tool for updating task status."""

    name = TASK_UPDATE_TOOL_NAME
    description = "Update a background task"
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[TaskUpdateOutput]:
        """Update task."""
        task_id = input_data.get("task_id", "")

        return ToolResult(
            data=TaskUpdateOutput(
                task_id=task_id,
                success=False,
                message="Task not found (stub)",
            )
        )
