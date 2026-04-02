"""
Notebook Edit Tool.

Edit Jupyter notebook cells.
"""

from .prompt import (
    DESCRIPTION,
    NOTEBOOK_EDIT_TOOL_NAME,
    PROMPT,
)


def __getattr__(name: str):
    """Lazy import for NotebookEditTool."""
    if name == "NotebookEditTool":
        from .tool import NotebookEditTool

        return NotebookEditTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "NOTEBOOK_EDIT_TOOL_NAME",
    "DESCRIPTION",
    "PROMPT",
    "NotebookEditTool",
]
