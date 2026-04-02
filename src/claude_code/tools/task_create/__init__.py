"""
Task Create Tool.

Create new tasks in the task list.
"""

from .prompt import (
    DESCRIPTION,
    TASK_CREATE_TOOL_NAME,
    get_prompt,
)


def __getattr__(name: str):
    """Lazy import for TaskCreateTool."""
    if name == "TaskCreateTool":
        from .tool import TaskCreateTool

        return TaskCreateTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "TASK_CREATE_TOOL_NAME",
    "DESCRIPTION",
    "get_prompt",
    "TaskCreateTool",
]
