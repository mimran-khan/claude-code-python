"""
File Read Tool.

Reads files from the local filesystem, supporting text, images,
PDFs, and Jupyter notebooks.
"""

from .limits import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    FileReadingLimits,
    get_default_file_reading_limits,
)
from .prompt import (
    DESCRIPTION,
    FILE_READ_TOOL_NAME,
    FILE_UNCHANGED_STUB,
    MAX_LINES_TO_READ,
)


def __getattr__(name: str):
    """Lazy import for FileReadTool to avoid dependency issues."""
    if name == "FileReadTool":
        from .tool import FileReadTool

        return FileReadTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "FileReadTool",
    "FILE_READ_TOOL_NAME",
    "FILE_UNCHANGED_STUB",
    "MAX_LINES_TO_READ",
    "DESCRIPTION",
    "DEFAULT_MAX_OUTPUT_TOKENS",
    "FileReadingLimits",
    "get_default_file_reading_limits",
]
