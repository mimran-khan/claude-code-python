"""
Task List Tool.

List all tasks in the task list.
"""

from .prompt import (
    DESCRIPTION,
    TASK_LIST_TOOL_NAME,
    get_prompt,
)


def __getattr__(name: str):
    """Lazy import for TaskListTool."""
    if name == "TaskListTool":
        from .tool import TaskListTool

        return TaskListTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "TASK_LIST_TOOL_NAME",
    "DESCRIPTION",
    "get_prompt",
    "TaskListTool",
]
