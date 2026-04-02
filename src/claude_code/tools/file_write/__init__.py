"""
File Write Tool.

Writes files to the local filesystem.
"""

from .prompt import (
    DESCRIPTION,
    FILE_WRITE_TOOL_NAME,
    get_write_tool_description,
)


def __getattr__(name: str):
    """Lazy import for FileWriteTool."""
    if name == "FileWriteTool":
        from .tool import FileWriteTool

        return FileWriteTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "FILE_WRITE_TOOL_NAME",
    "DESCRIPTION",
    "get_write_tool_description",
    "FileWriteTool",
]
