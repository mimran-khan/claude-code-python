"""
WriteFileTool — alias for FileWriteTool.

TypeScript: tools/FileWriteTool/
"""

from ..file_write_tool import (
    FILE_WRITE_TOOL_NAME,
    FileWriteTool,
    write_file,
)

WRITE_FILE_TOOL_NAME = FILE_WRITE_TOOL_NAME
WriteFileTool = FileWriteTool

__all__ = [
    "WRITE_FILE_TOOL_NAME",
    "FILE_WRITE_TOOL_NAME",
    "WriteFileTool",
    "FileWriteTool",
    "write_file",
]
