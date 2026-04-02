"""
Skill-loaded analytics at session startup.

Migrated from: utils/telemetry/skillLoadedEvent.ts
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

SKILL_BUDGET_CONTEXT_PERCENT = 0.01
CHARS_PER_TOKEN = 4
DEFAULT_CHAR_BUDGET = 8000


def get_char_budget(context_window_tokens: int | None = None) -> int:
    raw = os.environ.get("SLASH_COMMAND_TOOL_CHAR_BUDGET")
    if raw and raw.strip().isdigit():
        return int(raw)
    if context_window_tokens:
        return int(context_window_tokens * CHARS_PER_TOKEN * SKILL_BUDGET_CONTEXT_PERCENT)
    return DEFAULT_CHAR_BUDGET


@runtime_checkable
class SkillPromptCommand(Protocol):
    type: str
    name: str
    source: str
    loaded_from: str
    kind: str | None


SkillsProvider = Callable[[str], Awaitable[list[SkillPromptCommand]]]

_skill_commands_provider: SkillsProvider | None = None


def set_skill_commands_provider(fn: SkillsProvider | None) -> None:
    global _skill_commands_provider
    _skill_commands_provider = fn


async def log_skills_loaded(cwd: str, context_window_tokens: int) -> None:
    from ...services.analytics import log_event

    provider = _skill_commands_provider
    if provider is None:
        try:
            from ...commands.skills_telemetry import get_skill_tool_commands_for_telemetry

            provider = get_skill_tool_commands_for_telemetry
        except ImportError:
            return
    skills = await provider(cwd)
    skill_budget = get_char_budget(context_window_tokens)
    for skill in skills:
        if skill.type != "prompt":
            continue
        payload: dict[str, Any] = {
            "_PROTO_skill_name": skill.name,
            "skill_source": skill.source,
            "skill_loaded_from": skill.loaded_from,
            "skill_budget": skill_budget,
        }
        if skill.kind:
            payload["skill_kind"] = skill.kind
        log_event("tengu_skill_loaded", payload)
