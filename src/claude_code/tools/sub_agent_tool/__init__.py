"""
SubAgentTool — alias for AgentTool (TS: tools/AgentTool/).
"""

from ..agent_tool import (
    AGENT_TOOL_NAME,
    AgentInput,
    AgentOutput,
    AgentTool,
    run_agent,
)

SUB_AGENT_TOOL_NAME = AGENT_TOOL_NAME
SubAgentTool = AgentTool

__all__ = [
    "SUB_AGENT_TOOL_NAME",
    "AGENT_TOOL_NAME",
    "SubAgentTool",
    "AgentTool",
    "AgentInput",
    "AgentOutput",
    "run_agent",
]
