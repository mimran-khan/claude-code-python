"""TaskGet tool definition. Migrated from tools/TaskGetTool/TaskGetTool.ts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import TASK_GET_TOOL_NAME
from .prompt import DESCRIPTION, PROMPT


@dataclass
class TaskRecord:
    """A single task record returned by TaskGet."""

    id: str
    subject: str
    description: str
    status: str
    blocks: list[str]
    blocked_by: list[str]


class TaskGetToolDef(Tool[dict[str, Any], dict[str, Any]]):
    """Retrieve a task by ID from the task list (v2 / todo list integration)."""

    @property
    def name(self) -> str:
        return TASK_GET_TOOL_NAME

    @property
    def search_hint(self) -> str | None:
        return "retrieve a task by ID"

    @property
    def max_result_size_chars(self) -> int:
        return 100_000

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The ID of the task to retrieve",
                },
            },
            "required": ["task_id"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": ["object", "null"],
                    "properties": {
                        "id": {"type": "string"},
                        "subject": {"type": "string"},
                        "description": {"type": "string"},
                        "status": {"type": "string"},
                        "blocks": {"type": "array", "items": {"type": "string"}},
                        "blocked_by": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "required": ["task"],
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = str(input.get("task_id", ""))
        return ToolResult(success=True, output={"task": None})
