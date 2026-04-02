"""Task List tool implementation."""

from dataclasses import dataclass, field
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

TASK_LIST_TOOL_NAME = "task_list"


@dataclass
class TaskInfo:
    """Task information."""

    task_id: str
    status: str
    description: str


@dataclass
class TaskListOutput:
    """Output from task list."""

    tasks: list[TaskInfo] = field(default_factory=list)
    total: int = 0


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status_filter": {
            "type": "string",
            "enum": ["all", "running", "completed", "failed"],
            "description": "Filter tasks by status",
        },
    },
}


class TaskListTool(Tool):
    """Tool for listing tasks."""

    name = TASK_LIST_TOOL_NAME
    description = "List background tasks"
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[TaskListOutput]:
        """List tasks."""
        return ToolResult(
            data=TaskListOutput(
                tasks=[],
                total=0,
            )
        )
