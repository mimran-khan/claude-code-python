"""
Agent color names for subagent UI (compat shim for TS import path).

Migrated from: tools/AgentTool/agentColorManager.ts

Canonical implementation: :mod:`claude_code.utils.agent_color_manager`.
"""

from __future__ import annotations

from ...utils.agent_color_manager import (
    AGENT_COLOR_TO_THEME_COLOR,
    AGENT_COLORS,
    AgentColorName,
    get_agent_color,
    get_agent_color_map,
    set_agent_color,
    set_agent_color_map_store,
)

__all__ = [
    "AGENT_COLOR_TO_THEME_COLOR",
    "AGENT_COLORS",
    "AgentColorName",
    "get_agent_color",
    "get_agent_color_map",
    "set_agent_color",
    "set_agent_color_map_store",
]
