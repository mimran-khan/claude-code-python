"""
Task Update Tool.

Update task status.

Migrated from: tools/TaskUpdateTool/TaskUpdateTool.ts
"""

from __future__ import annotations

from typing import Any

from ..base import Tool, ToolResult, ToolUseContext

TASK_UPDATE_TOOL_NAME = "TaskUpdate"


class TaskUpdateTool(Tool[dict[str, Any], dict[str, Any]]):
    """Update task status."""

    @property
    def name(self) -> str:
        return TASK_UPDATE_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "update task, task status"

    async def description(self) -> str:
        return "Update the status of a task."

    async def prompt(self) -> str:
        return "Update a task."

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "status": {"type": "string"},
            },
            "required": ["task_id", "status"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "status": {"type": "string"},
            },
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        """Update task."""
        task_id = input.get("task_id", "")
        status = input.get("status", "")

        return ToolResult(
            success=True,
            output={"task_id": task_id, "status": status},
        )
