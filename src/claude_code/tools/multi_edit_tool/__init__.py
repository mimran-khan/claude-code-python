"""
MultiEditTool — alias for FileEditTool (TS: tools/FileEditTool/).
"""

from ..file_edit_tool import (
    FILE_EDIT_TOOL_NAME,
    FileEditTool,
)

MULTI_EDIT_TOOL_NAME = FILE_EDIT_TOOL_NAME
MultiEditTool = FileEditTool

__all__ = [
    "MULTI_EDIT_TOOL_NAME",
    "FILE_EDIT_TOOL_NAME",
    "MultiEditTool",
    "FileEditTool",
]
