"""Task update tool. Migrated from tools/TaskUpdateTool/TaskUpdateTool.ts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import TASK_UPDATE_TOOL_NAME
from .prompt import DESCRIPTION, PROMPT


@dataclass
class TaskUpdateInput:
    """Tool input (camelCase keys match TypeScript schema)."""

    taskId: str
    subject: str | None = None
    description: str | None = None
    activeForm: str | None = None
    status: str | None = None
    addBlocks: list[str] | None = None
    addBlockedBy: list[str] | None = None
    owner: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class TaskUpdateOutput:
    """Tool output (camelCase keys match TypeScript schema)."""

    success: bool
    taskId: str
    updatedFields: list[str]
    error: str | None = None


class TaskUpdateToolDef(Tool[dict[str, Any], dict[str, Any]]):
    """Update tasks in the structured task list."""

    @property
    def name(self) -> str:
        return TASK_UPDATE_TOOL_NAME

    @property
    def search_hint(self) -> str | None:
        return "update a task"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "taskId": {"type": "string", "description": "The ID of the task to update"},
                "subject": {"type": "string"},
                "description": {"type": "string"},
                "activeForm": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "deleted"],
                },
                "addBlocks": {"type": "array", "items": {"type": "string"}},
                "addBlockedBy": {"type": "array", "items": {"type": "string"}},
                "owner": {"type": "string"},
                "metadata": {"type": "object", "additionalProperties": True},
            },
            "required": ["taskId"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "taskId": {"type": "string"},
                "updatedFields": {"type": "array", "items": {"type": "string"}},
                "error": {"type": "string"},
            },
            "required": ["success", "taskId", "updatedFields"],
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = context
        tid = str(input.get("taskId", ""))
        if not tid:
            out = TaskUpdateOutput(
                success=False,
                taskId="",
                updatedFields=[],
                error="taskId is required",
            )
            return ToolResult(success=False, error=out.error, output=asdict(out))

        updated: list[str] = []
        for key in (
            "subject",
            "description",
            "activeForm",
            "status",
            "addBlocks",
            "addBlockedBy",
            "owner",
            "metadata",
        ):
            if key in input and input[key] is not None:
                updated.append(key)

        out = TaskUpdateOutput(success=True, taskId=tid, updatedFields=updated, error=None)
        return ToolResult(success=True, output=asdict(out))
