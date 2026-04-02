"""
Map agent color names to Ink / terminal theme keys.

Migrated from: utils/ink.ts
"""

from __future__ import annotations

from typing import TypeGuard

from .agent_color_manager import AGENT_COLOR_TO_THEME_COLOR, AgentColorName

DEFAULT_AGENT_THEME_COLOR = "cyan_FOR_SUBAGENTS_ONLY"


def _is_agent_color_name(value: str) -> TypeGuard[AgentColorName]:
    return value in AGENT_COLOR_TO_THEME_COLOR


def to_ink_color(color: str | None) -> str:
    """
    Convert an agent color string to a theme key or ``ansi:<raw>`` fallback.
    """
    if not color:
        return DEFAULT_AGENT_THEME_COLOR
    if _is_agent_color_name(color):
        return AGENT_COLOR_TO_THEME_COLOR[color]
    return f"ansi:{color}"
