"""
TodoRead — returns todos from session state.

No TypeScript counterpart in leak; complements TodoWriteTool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import TODO_READ_TOOL_NAME
from .prompt_text import DESCRIPTION, PROMPT


@dataclass
class TodoReadOutput:
    todos: list[dict[str, Any]]


class TodoReadTool(Tool[dict[str, Any], TodoReadOutput]):
    @property
    def name(self) -> str:
        return TODO_READ_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "read todo list"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"todos": {"type": "array"}},
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        todos: list[dict[str, Any]] = []
        app = context.get_app_state() if context.get_app_state else None
        if app is not None and hasattr(app, "todos"):
            raw = getattr(app, "todos", [])
            if isinstance(raw, list):
                todos = [x for x in raw if isinstance(x, dict)]
        else:
            raw = context.read_file_state.get("todos")
            if isinstance(raw, list):
                todos = [x for x in raw if isinstance(x, dict)]

        return ToolResult(success=True, output=TodoReadOutput(todos=todos))
