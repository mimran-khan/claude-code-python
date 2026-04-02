"""
Glob Tool.

Fast file pattern matching tool that works with any codebase size.
"""

from .prompt import DESCRIPTION, GLOB_TOOL_NAME


def __getattr__(name: str):
    """Lazy import for GlobTool."""
    if name == "GlobTool":
        from .tool import GlobTool

        return GlobTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "GLOB_TOOL_NAME",
    "DESCRIPTION",
    "GlobTool",
]
