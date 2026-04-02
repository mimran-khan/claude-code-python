"""
File Edit Tool.

Performs exact string replacements in files.
"""

from .prompt import (
    DESCRIPTION,
    FILE_EDIT_TOOL_NAME,
    get_edit_tool_description,
)


def __getattr__(name: str):
    """Lazy import for FileEditTool."""
    if name == "FileEditTool":
        from .tool import FileEditTool

        return FileEditTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "FILE_EDIT_TOOL_NAME",
    "DESCRIPTION",
    "get_edit_tool_description",
    "FileEditTool",
]
