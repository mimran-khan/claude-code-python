"""
Thinking / ultrathink configuration helpers.

Migrated from: utils/thinking.ts
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal

from .effort import _get_3p_model_capability_override
from .model.model import get_canonical_name
from .model.providers import get_api_provider


@dataclass(frozen=True, slots=True)
class ThinkingConfigAdaptive:
    type: Literal["adaptive"] = "adaptive"


@dataclass(frozen=True, slots=True)
class ThinkingConfigEnabled:
    budget_tokens: int
    type: Literal["enabled"] = "enabled"


@dataclass(frozen=True, slots=True)
class ThinkingConfigDisabled:
    type: Literal["disabled"] = "disabled"


ThinkingConfig = ThinkingConfigAdaptive | ThinkingConfigEnabled | ThinkingConfigDisabled


def is_ultrathink_enabled() -> bool:
    if os.environ.get("CLAUDE_ULTRATHINK_DISABLED", "").lower() in ("1", "true", "yes"):
        return False
    try:
        from claude_code.services.analytics.growthbook import get_feature_value_cached

        return bool(get_feature_value_cached("tengu_turtle_carbon", True))
    except Exception:
        return True


def has_ultrathink_keyword(text: str) -> bool:
    return bool(re.search(r"\bultrathink\b", text, re.I))


@dataclass(frozen=True, slots=True)
class ThinkingTriggerPosition:
    word: str
    start: int
    end: int


def find_thinking_trigger_positions(text: str) -> list[ThinkingTriggerPosition]:
    out: list[ThinkingTriggerPosition] = []
    for m in re.finditer(r"\bultrathink\b", text, re.I):
        out.append(ThinkingTriggerPosition(word=m.group(0), start=m.start(), end=m.end()))
    return out


_RAINBOW_COLORS = (
    "rainbow_red",
    "rainbow_orange",
    "rainbow_yellow",
    "rainbow_green",
    "rainbow_blue",
    "rainbow_indigo",
    "rainbow_violet",
)
_RAINBOW_SHIMMER = tuple(f"{c}_shimmer" for c in _RAINBOW_COLORS)


def get_rainbow_color(char_index: int, shimmer: bool = False) -> str:
    colors = _RAINBOW_SHIMMER if shimmer else _RAINBOW_COLORS
    return colors[char_index % len(colors)]


def _resolve_ant_model(_model_lower: str) -> bool:
    return False


def model_supports_thinking(model: str) -> bool:
    supported = _get_3p_model_capability_override(model, "thinking")
    if supported is not None:
        return supported
    if os.environ.get("USER_TYPE") == "ant" and _resolve_ant_model(model.lower()):
        return True
    canonical = get_canonical_name(model)
    provider = get_api_provider()
    if provider in ("foundry", "firstParty"):
        return "claude-3-" not in canonical
    return "sonnet-4" in canonical or "opus-4" in canonical


def model_supports_adaptive_thinking(model: str) -> bool:
    supported = _get_3p_model_capability_override(model, "adaptive_thinking")
    if supported is not None:
        return supported
    canonical = get_canonical_name(model)
    if "opus-4-6" in canonical or "sonnet-4-6" in canonical:
        return True
    if any(x in canonical for x in ("opus", "sonnet", "haiku")):
        return False
    provider = get_api_provider()
    return provider in ("firstParty", "foundry")


def should_enable_thinking_by_default() -> bool:
    raw = os.environ.get("MAX_THINKING_TOKENS")
    if raw:
        try:
            return int(raw, 10) > 0
        except ValueError:
            pass
    try:
        from claude_code.utils.settings.settings import get_merged_settings

        merged = get_merged_settings() or {}
        if merged.get("alwaysThinkingEnabled") is False:
            return False
    except Exception:
        pass
    return True
