"""Task Create tool implementation."""

import uuid
from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext

TASK_CREATE_TOOL_NAME = "task_create"


@dataclass
class TaskCreateOutput:
    """Output from task create."""

    task_id: str
    status: str
    message: str


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            "description": "Description of the task to create",
        },
        "agent_type": {
            "type": "string",
            "description": "Type of agent to run the task",
        },
        "prompt": {
            "type": "string",
            "description": "Prompt for the agent",
        },
    },
    "required": ["description", "prompt"],
}


class TaskCreateTool(Tool):
    """Tool for creating background tasks."""

    name = TASK_CREATE_TOOL_NAME
    description = "Create a background task"
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[TaskCreateOutput]:
        """Create a task."""
        description = input_data.get("description", "")
        input_data.get("prompt", "")
        input_data.get("agent_type", "generalPurpose")

        task_id = f"task_{uuid.uuid4().hex[:8]}"

        return ToolResult(
            data=TaskCreateOutput(
                task_id=task_id,
                status="created",
                message=f"Task created: {description[:50]}",
            )
        )
