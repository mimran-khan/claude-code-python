"""
File Edit Tool.

Edit files using string replacement.

Migrated from: tools/FileEditTool/*.ts
"""

from .file_edit_tool import (
    FILE_EDIT_TOOL_NAME,
    FileEditTool,
    edit_file,
)

__all__ = [
    "FileEditTool",
    "FILE_EDIT_TOOL_NAME",
    "edit_file",
]
