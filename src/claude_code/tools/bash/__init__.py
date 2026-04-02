"""
Bash Tool.

Executes shell commands in the user's environment.
"""

from .prompt import (
    BASH_TOOL_NAME,
    get_default_timeout_ms,
    get_max_timeout_ms,
    get_simple_prompt,
)


def __getattr__(name: str):
    """Lazy import for BashTool to avoid loading subprocess dependencies."""
    if name == "BashTool":
        from .tool import BashTool

        return BashTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BASH_TOOL_NAME",
    "BashTool",
    "get_default_timeout_ms",
    "get_max_timeout_ms",
    "get_simple_prompt",
]
