"""
ReadFileTool — alias for FileReadTool.

TypeScript: tools/FileReadTool/
"""

from ..file_read_tool import (
    FILE_READ_TOOL_NAME,
    FileReadTool,
    MaxFileReadTokenExceededError,
    read_file,
)

# Naming parity with TS / user migration checklist
READ_FILE_TOOL_NAME = FILE_READ_TOOL_NAME
ReadFileTool = FileReadTool

__all__ = [
    "READ_FILE_TOOL_NAME",
    "FILE_READ_TOOL_NAME",
    "ReadFileTool",
    "FileReadTool",
    "read_file",
    "MaxFileReadTokenExceededError",
]
