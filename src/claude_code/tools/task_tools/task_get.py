"""Task Get tool implementation."""

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

TASK_GET_TOOL_NAME = "task_get"


@dataclass
class TaskGetOutput:
    """Output from task get."""

    task_id: str
    status: str
    description: str | None = None
    result: str | None = None
    error: str | None = None


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {
            "type": "string",
            "description": "ID of the task to get",
        },
    },
    "required": ["task_id"],
}


class TaskGetTool(Tool):
    """Tool for getting task status."""

    name = TASK_GET_TOOL_NAME
    description = "Get status of a background task"
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[TaskGetOutput]:
        """Get task status."""
        task_id = input_data.get("task_id", "")

        return ToolResult(
            data=TaskGetOutput(
                task_id=task_id,
                status="unknown",
                error="Task not found (stub)",
            )
        )
