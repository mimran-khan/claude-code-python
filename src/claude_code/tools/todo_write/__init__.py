"""
Todo Write Tool.

Manages task lists for tracking progress.
"""

from .prompt import (
    DESCRIPTION,
    PROMPT,
    TODO_WRITE_TOOL_NAME,
)


def __getattr__(name: str):
    """Lazy import for TodoWriteTool."""
    if name == "TodoWriteTool":
        from .tool import TodoWriteTool

        return TodoWriteTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "TODO_WRITE_TOOL_NAME",
    "DESCRIPTION",
    "PROMPT",
    "TodoWriteTool",
]
