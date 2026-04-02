"""
Send Message Tool.

Sends messages between agents/teammates.
"""

from .prompt import (
    DESCRIPTION,
    SEND_MESSAGE_TOOL_NAME,
    get_prompt,
)


def __getattr__(name: str):
    """Lazy import for SendMessageTool."""
    if name == "SendMessageTool":
        from .tool import SendMessageTool

        return SendMessageTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "SEND_MESSAGE_TOOL_NAME",
    "DESCRIPTION",
    "get_prompt",
    "SendMessageTool",
]
