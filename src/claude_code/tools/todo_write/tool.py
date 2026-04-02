"""
Todo Write Tool Implementation.

Manages task lists for tracking progress.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import DESCRIPTION, TODO_WRITE_TOOL_NAME


class TodoItem(BaseModel):
    """A single todo item."""

    id: str = Field(..., description="Unique identifier for the todo item.")
    content: str = Field(..., description="The description/content of the todo item.")
    status: Literal["pending", "in_progress", "completed", "cancelled"] = Field(
        default="pending",
        description="The current status of the todo item.",
    )


class TodoWriteInput(BaseModel):
    """Input parameters for todo write tool."""

    todos: list[TodoItem] = Field(
        ...,
        description="Array of TODO items to update or create.",
        min_length=1,
    )
    merge: bool = Field(
        default=True,
        description="Whether to merge with existing todos. If false, replaces all.",
    )


@dataclass
class TodoWriteSuccess:
    """Successful todo write result."""

    type: Literal["success"] = "success"
    todos_count: int = 0
    message: str = ""


@dataclass
class TodoWriteError:
    """Failed todo write result."""

    type: Literal["error"] = "error"
    error: str = ""


TodoWriteOutput = TodoWriteSuccess | TodoWriteError


class TodoWriteTool(Tool[TodoWriteInput, TodoWriteOutput]):
    """
    Tool for managing task lists.

    Allows creating, updating, and tracking todo items
    for the current session.
    """

    _todos: dict[str, TodoItem] = {}

    @property
    def name(self) -> str:
        return TODO_WRITE_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
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
                    "description": "Array of TODO items.",
                    "minItems": 1,
                },
                "merge": {
                    "type": "boolean",
                    "description": "Whether to merge with existing todos.",
                    "default": True,
                },
            },
            "required": ["todos"],
        }

    def is_read_only(self, input_data: TodoWriteInput) -> bool:
        return True  # Todos don't modify files

    async def call(
        self,
        input_data: TodoWriteInput,
        context: Any,
    ) -> ToolResult[TodoWriteOutput]:
        """Execute the todo write operation."""
        todos = input_data.todos
        merge = input_data.merge

        if not merge:
            self._todos.clear()

        for item in todos:
            self._todos[item.id] = item

        return ToolResult(
            success=True,
            output=TodoWriteSuccess(
                todos_count=len(self._todos),
                message=f"Updated {len(todos)} todo(s). Total: {len(self._todos)}",
            ),
        )

    def user_facing_name(self, input_data: TodoWriteInput | None = None) -> str:
        """Get the user-facing name for this tool."""
        return "Todos"

    def get_todos(self) -> list[TodoItem]:
        """Get all current todos."""
        return list(self._todos.values())

    def clear_todos(self) -> None:
        """Clear all todos."""
        self._todos.clear()
