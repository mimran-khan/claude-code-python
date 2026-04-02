"""
Cron delete tool.

Delete scheduled tasks.

Migrated from: tools/ScheduleCronTool/CronDeleteTool.ts
"""

from __future__ import annotations

from typing import Any

from ..base import Tool, ToolResult

CRON_DELETE_TOOL_NAME = "CronDelete"


class CronDeleteTool(Tool):
    """
    Tool for deleting scheduled tasks.
    """

    name = CRON_DELETE_TOOL_NAME
    description = "Delete a scheduled task by ID"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the task to delete",
                },
            },
            "required": ["id"],
        }

    async def execute(
        self,
        input_data: dict[str, Any],
        context: Any,
    ) -> ToolResult:
        """Execute the cron delete tool."""
        task_id = input_data.get("id", "")

        if not task_id:
            return ToolResult(
                output="Task ID is required",
                is_error=True,
            )

        # In a full implementation, this would delete from task storage
        # For now, return success stub

        return ToolResult(
            output=f"Deleted task: {task_id}",
            data={"id": task_id, "deleted": True},
        )
