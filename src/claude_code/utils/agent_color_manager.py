"""
Agent color names and theme mapping for subagents.

Migrated from: tools/AgentTool/agentColorManager.ts
"""

from __future__ import annotations

from typing import Literal

AgentColorName = Literal[
    "red",
    "blue",
    "green",
    "yellow",
    "purple",
    "orange",
    "pink",
    "cyan",
]

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

# Keys match Theme in utils/theme.ts (subset used by agents)
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

# In-process map; TS uses bootstrap getAgentColorMap(). Inject via set_agent_color_map.
_agent_color_map: dict[str, AgentColorName] = {}


def set_agent_color_map_store(store: dict[str, AgentColorName] | None) -> None:
    """Replace the backing store (e.g. sync with app state)."""
    global _agent_color_map
    _agent_color_map = {} if store is None else dict(store)


def get_agent_color_map() -> dict[str, AgentColorName]:
    return _agent_color_map


def get_agent_color(agent_type: str) -> str | None:
    if agent_type == "general-purpose":
        return None
    existing = _agent_color_map.get(agent_type)
    if existing and existing in AGENT_COLORS:
        return AGENT_COLOR_TO_THEME_COLOR[existing]
    return None


def set_agent_color(agent_type: str, color: AgentColorName | None) -> None:
    if color is None:
        _agent_color_map.pop(agent_type, None)
        return
    if color in AGENT_COLORS:
        _agent_color_map[agent_type] = color
