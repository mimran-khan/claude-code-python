"""
REPL Primitive Tools.

Tools accessible within the REPL VM context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


_primitive_tools: list[str] | None = None


def get_repl_primitive_tools() -> list[str]:
    """Get the list of primitive tool names for REPL.

    These tools are hidden from direct model use when REPL mode is on,
    but still accessible inside the REPL VM context.

    Returns:
        List of primitive tool names
    """
    global _primitive_tools
    if _primitive_tools is None:
        _primitive_tools = [
            "Read",
            "Write",
            "StrReplace",
            "Glob",
            "Grep",
            "Shell",
            "NotebookEdit",
            "Task",
        ]
    return _primitive_tools
