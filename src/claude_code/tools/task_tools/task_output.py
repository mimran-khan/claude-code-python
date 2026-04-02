"""Task Output tool implementation."""

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

TASK_OUTPUT_TOOL_NAME = "task_output"


@dataclass
class TaskOutputOutput:
    """Output from task output."""

    content: str
    format: str = "text"


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "The output content",
        },
        "format": {
            "type": "string",
            "enum": ["text", "json", "markdown"],
            "description": "Format of the output",
        },
    },
    "required": ["content"],
}


class TaskOutputTool(Tool):
    """Tool for outputting task results."""

    name = TASK_OUTPUT_TOOL_NAME
    description = "Output content from a task"
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[TaskOutputOutput]:
        """Output task result."""
        content = input_data.get("content", "")
        fmt = input_data.get("format", "text")

        return ToolResult(
            data=TaskOutputOutput(
                content=content,
                format=fmt,
            )
        )
