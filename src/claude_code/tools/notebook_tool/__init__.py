"""
NotebookTool — notebook read + edit (TS: NotebookEditTool; read companion in Python).
"""

from ..notebook_edit_tool import (
    NOTEBOOK_EDIT_TOOL_NAME,
    NotebookEditTool,
)
from ..notebook_read_tool import (
    NOTEBOOK_READ_TOOL_NAME,
    NotebookReadTool,
)

NOTEBOOK_TOOL_EDIT_NAME = NOTEBOOK_EDIT_TOOL_NAME
NOTEBOOK_TOOL_READ_NAME = NOTEBOOK_READ_TOOL_NAME

__all__ = [
    "NOTEBOOK_TOOL_EDIT_NAME",
    "NOTEBOOK_TOOL_READ_NAME",
    "NOTEBOOK_EDIT_TOOL_NAME",
    "NOTEBOOK_READ_TOOL_NAME",
    "NotebookEditTool",
    "NotebookReadTool",
]
