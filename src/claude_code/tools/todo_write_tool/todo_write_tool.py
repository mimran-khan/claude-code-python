"""
Todo Write Tool implementation.

Manage task lists.

Migrated from: tools/TodoWriteTool/TodoWriteTool.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..base import Tool, ToolResult, ToolUseContext

TODO_WRITE_TOOL_NAME = "TodoWrite"


TODO_WRITE_DESCRIPTION = """Create and manage a structured task list.

Use this tool for:
- Complex multi-step tasks (3+ distinct steps)
- Non-trivial tasks requiring careful planning
- When the user explicitly requests a todo list
- After receiving new instructions to capture requirements

When NOT to use:
- Simple, straightforward tasks
- Tasks completable in < 3 trivial steps
- Purely conversational/informational requests
"""


TODO_WRITE_PROMPT = """Manage your task list.

Important:
- Mark tasks as completed immediately after finishing
- Only ONE task should be in_progress at a time
- Update status in real-time
"""


TodoStatus = Literal["pending", "in_progress", "completed", "cancelled"]


@dataclass
class TodoItem:
    """A single todo item."""

    id: str
    content: str
    status: TodoStatus


@dataclass
class TodoWriteInput:
    """Input for the Todo Write tool."""

    todos: list[TodoItem]
    merge: bool = True


class TodoWriteTool(Tool[dict[str, Any], list[TodoItem]]):
    """Tool for managing todo lists."""

    @property
    def name(self) -> str:
        return TODO_WRITE_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "create todo list, manage tasks, track progress"

    async def description(self) -> str:
        return TODO_WRITE_DESCRIPTION

    async def prompt(self) -> str:
        return TODO_WRITE_PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "content": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed", "cancelled"],
                            },
                        },
                        "required": ["id", "content", "status"],
                    },
                    "minItems": 2,
                },
                "merge": {
                    "type": "boolean",
                    "description": "Whether to merge with existing todos",
                },
            },
            "required": ["todos", "merge"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "content": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
        }

    def user_facing_name(self, input: dict[str, Any] | None = None) -> str:
        return TODO_WRITE_TOOL_NAME

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        """Execute the todo write."""
        todos_data = input.get("todos", [])
        input.get("merge", True)

        if not todos_data:
            return ToolResult(
                success=False,
                error="todos array is required and must have at least 2 items",
                error_code=1,
            )

        # Parse todos
        todos = []
        for item in todos_data:
            todos.append(
                TodoItem(
                    id=item.get("id", ""),
                    content=item.get("content", ""),
                    status=item.get("status", "pending"),
                )
            )

        # In a full implementation, would store in app state
        return ToolResult(
            success=True,
            output=todos,
        )
