"""
Task Update Tool.

Update tasks in the task list.
"""

from .prompt import (
    DESCRIPTION,
    PROMPT,
    TASK_UPDATE_TOOL_NAME,
)


def __getattr__(name: str):
    """Lazy import for TaskUpdateTool."""
    if name == "TaskUpdateTool":
        from .tool import TaskUpdateTool

        return TaskUpdateTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "TASK_UPDATE_TOOL_NAME",
    "DESCRIPTION",
    "PROMPT",
    "TaskUpdateTool",
]
