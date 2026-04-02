"""
Todo list types.

Migrated from: utils/todo/types.ts
"""

from dataclasses import dataclass
from typing import Literal

TodoStatus = Literal["pending", "in_progress", "completed"]


@dataclass
class TodoItem:
    """A single todo item."""

    content: str
    status: TodoStatus
    active_form: str

    def __post_init__(self):
        if not self.content:
            raise ValueError("Content cannot be empty")
        if not self.active_form:
            raise ValueError("Active form cannot be empty")


TodoList = list[TodoItem]


def create_todo_item(
    content: str,
    status: TodoStatus = "pending",
    active_form: str | None = None,
) -> TodoItem:
    """Create a new todo item.

    Args:
        content: The todo content
        status: Status (pending, in_progress, completed)
        active_form: The active form (defaults to content)
    """
    return TodoItem(
        content=content,
        status=status,
        active_form=active_form or content,
    )


def validate_todo_list(items: list[dict]) -> TodoList:
    """Validate and convert a list of dicts to TodoList.

    Raises ValueError if any item is invalid.
    """
    result: TodoList = []

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each item must be a dictionary")

        content = item.get("content", "")
        status = item.get("status", "pending")
        active_form = item.get("active_form", content)

        if status not in ("pending", "in_progress", "completed"):
            raise ValueError(f"Invalid status: {status}")

        result.append(
            TodoItem(
                content=content,
                status=status,
                active_form=active_form,
            )
        )

    return result


def filter_by_status(items: TodoList, status: TodoStatus) -> TodoList:
    """Filter todo list by status."""
    return [item for item in items if item.status == status]


def count_by_status(items: TodoList) -> dict:
    """Count items by status."""
    return {
        "pending": len([i for i in items if i.status == "pending"]),
        "in_progress": len([i for i in items if i.status == "in_progress"]),
        "completed": len([i for i in items if i.status == "completed"]),
    }
