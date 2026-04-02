"""
Task List Tool.

List tasks.

Migrated from: tools/TaskListTool/TaskListTool.ts
"""

from __future__ import annotations

from typing import Any

from ..base import Tool, ToolResult, ToolUseContext

TASK_LIST_TOOL_NAME = "TaskList"


class TaskListTool(Tool[dict[str, Any], dict[str, Any]]):
    """List all tasks."""

    @property
    def name(self) -> str:
        return TASK_LIST_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "list tasks, show tasks"

    async def description(self) -> str:
        return "List all active tasks."

    async def prompt(self) -> str:
        return "List tasks."

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tasks": {"type": "array"},
            },
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        """List tasks."""
        return ToolResult(
            success=True,
            output={"tasks": []},
        )
