"""Task Stop tool implementation."""

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

TASK_STOP_TOOL_NAME = "task_stop"


@dataclass
class TaskStopOutput:
    """Output from task stop."""

    task_id: str
    stopped: bool
    message: str


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {
            "type": "string",
            "description": "ID of the task to stop",
        },
        "reason": {
            "type": "string",
            "description": "Reason for stopping the task",
        },
    },
    "required": ["task_id"],
}


class TaskStopTool(Tool):
    """Tool for stopping tasks."""

    name = TASK_STOP_TOOL_NAME
    description = "Stop a running background task"
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[TaskStopOutput]:
        """Stop task."""
        task_id = input_data.get("task_id", "")
        input_data.get("reason", "")

        return ToolResult(
            data=TaskStopOutput(
                task_id=task_id,
                stopped=False,
                message="Task not found (stub)",
            )
        )
