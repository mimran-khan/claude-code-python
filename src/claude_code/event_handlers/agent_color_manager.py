"""
Per-agent ANSI theme colors for subagent display.

Migrated from: tools/AgentTool/agentColorManager.ts
(useAgentColorManager.ts is not present in the leaked tree; this module ports the shared helpers.)
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Literal

AgentColorName = Literal["red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"]

AGENT_COLORS: tuple[AgentColorName, ...] = (
    "red",
    "blue",
    "green",
    "yellow",
    "purple",
    "orange",
    "pink",
    "cyan",
)

AGENT_COLOR_TO_THEME_COLOR: dict[AgentColorName, str] = {
    "red": "red_FOR_SUBAGENTS_ONLY",
    "blue": "blue_FOR_SUBAGENTS_ONLY",
    "green": "green_FOR_SUBAGENTS_ONLY",
    "yellow": "yellow_FOR_SUBAGENTS_ONLY",
    "purple": "purple_FOR_SUBAGENTS_ONLY",
    "orange": "orange_FOR_SUBAGENTS_ONLY",
    "pink": "pink_FOR_SUBAGENTS_ONLY",
    "cyan": "cyan_FOR_SUBAGENTS_ONLY",
}


def get_agent_color(
    agent_type: str,
    agent_color_map: MutableMapping[str, AgentColorName],
) -> str | None:
    """Map agent type to theme token, or None for the default general-purpose agent."""
    if agent_type == "general-purpose":
        return None
    existing = agent_color_map.get(agent_type)
    if existing in AGENT_COLORS:
        return AGENT_COLOR_TO_THEME_COLOR[existing]
    return None


def set_agent_color(
    agent_type: str,
    color: AgentColorName | None,
    agent_color_map: MutableMapping[str, AgentColorName],
) -> None:
    """Assign or clear a stable color for ``agent_type``."""
    if color is None:
        agent_color_map.pop(agent_type, None)
        return
    if color in AGENT_COLORS:
        agent_color_map[agent_type] = color
