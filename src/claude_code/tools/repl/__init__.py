"""
REPL Tool.

Interactive Read-Eval-Print-Loop execution tool.
"""

from .primitive_tools import get_repl_primitive_tools


def __getattr__(name: str):
    """Lazy import for REPLTool."""
    if name == "REPLTool":
        from .tool import REPLTool

        return REPLTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "get_repl_primitive_tools",
    "REPLTool",
]
