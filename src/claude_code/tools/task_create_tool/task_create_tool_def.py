"""Task create tool. Migrated from tools/TaskCreateTool/TaskCreateTool.ts (surface)."""

from __future__ import annotations

import uuid
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import TASK_CREATE_TOOL_NAME
from .task_create_prompt import DESCRIPTION, get_task_create_prompt


class TaskCreateToolDef(Tool[dict[str, Any], dict[str, Any]]):
    """Create a new task in the task list."""

    @property
    def name(self) -> str:
        return TASK_CREATE_TOOL_NAME

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return get_task_create_prompt()

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "description": {"type": "string"},
                "active_form": {"type": "string"},
            },
            "required": ["subject", "description"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": True}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = context
        subject = str(input.get("subject", "")).strip()
        description = str(input.get("description", "")).strip()
        if not subject or not description:
            return ToolResult(success=False, error="subject and description are required")
        task_id = str(uuid.uuid4())
        return ToolResult(
            success=True,
            output={
                "taskId": task_id,
                "subject": subject,
                "description": description,
                "activeForm": input.get("active_form"),
                "status": "pending",
            },
        )
