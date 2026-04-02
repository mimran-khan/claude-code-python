"""
Task Create Tool.

Create new tasks.

Migrated from: tools/TaskCreateTool/TaskCreateTool.ts
"""

from __future__ import annotations

import uuid
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext

TASK_CREATE_TOOL_NAME = "TaskCreate"


class TaskCreateTool(Tool[dict[str, Any], dict[str, Any]]):
    """Create a new task."""

    @property
    def name(self) -> str:
        return TASK_CREATE_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "create new task, spawn task"

    async def description(self) -> str:
        return "Create a new task to be executed."

    async def prompt(self) -> str:
        return "Create a new task."

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "prompt": {"type": "string"},
            },
            "required": ["description", "prompt"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
            },
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        """Create a task."""
        task_id = str(uuid.uuid4())

        return ToolResult(
            success=True,
            output={"task_id": task_id},
        )
