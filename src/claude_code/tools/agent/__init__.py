"""
Agent Tool.

Launches specialized agents to handle complex tasks.
"""

from .prompt import (
    AGENT_TOOL_NAME,
    format_agent_line,
    get_prompt,
)


def __getattr__(name: str):
    """Lazy import for AgentTool."""
    if name == "AgentTool":
        from .tool import AgentTool

        return AgentTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AGENT_TOOL_NAME",
    "format_agent_line",
    "get_prompt",
    "AgentTool",
]
