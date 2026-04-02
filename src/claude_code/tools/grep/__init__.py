"""
Grep Tool.

A powerful search tool built on ripgrep.
"""

from .prompt import GREP_TOOL_NAME, get_description


def __getattr__(name: str):
    """Lazy import for GrepTool."""
    if name == "GrepTool":
        from .tool import GrepTool

        return GrepTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "GREP_TOOL_NAME",
    "get_description",
    "GrepTool",
]
