"""TS ``AgentTool/prompt.ts`` — re-export from :mod:`claude_code.tools.agent.prompt`."""

from __future__ import annotations

from ..agent.prompt import (
    AGENT_TOOL_NAME,
    AgentDefinition,
    format_agent_line,
    get_tools_description,
)

__all__ = [
    "AGENT_TOOL_NAME",
    "AgentDefinition",
    "format_agent_line",
    "get_tools_description",
]
