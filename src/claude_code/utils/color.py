"""
Theme color key names (subset for agents and UI).

Migrated from: utils/theme.ts (agent + semantic keys used outside full theme).
"""

from __future__ import annotations

from typing import Literal

# Semantic / agent theme keys referenced across the codebase
ThemeColorKey = Literal[
    "red_FOR_SUBAGENTS_ONLY",
    "blue_FOR_SUBAGENTS_ONLY",
    "green_FOR_SUBAGENTS_ONLY",
    "yellow_FOR_SUBAGENTS_ONLY",
    "purple_FOR_SUBAGENTS_ONLY",
    "orange_FOR_SUBAGENTS_ONLY",
    "pink_FOR_SUBAGENTS_ONLY",
    "cyan_FOR_SUBAGENTS_ONLY",
    "success",
    "error",
    "warning",
    "text",
    "subtle",
]
