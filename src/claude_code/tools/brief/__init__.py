"""
Brief Tool.

Send messages to the user with attachments.
"""

from .prompt import (
    BRIEF_TOOL_NAME,
    BRIEF_TOOL_PROMPT,
    DESCRIPTION,
)


def __getattr__(name: str):
    """Lazy import for BriefTool."""
    if name == "BriefTool":
        from .tool import BriefTool

        return BriefTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BRIEF_TOOL_NAME",
    "DESCRIPTION",
    "BRIEF_TOOL_PROMPT",
    "BriefTool",
]
