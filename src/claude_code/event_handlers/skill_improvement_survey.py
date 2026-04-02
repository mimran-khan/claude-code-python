"""
Skill improvement survey open/close + apply flow.

Migrated from: hooks/useSkillImprovementSurvey.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any


async def apply_skill_improvement_survey_selection(
    *,
    skill_name: str,
    updates: Sequence[Mapping[str, Any]],
    applied: bool,
    apply_skill_improvement: Callable[[str, Sequence[Mapping[str, Any]]], Awaitable[None]],
    append_system_message: Callable[[str], None],
    clear_suggestion: Callable[[], None],
) -> None:
    if applied:
        await apply_skill_improvement(skill_name, updates)
        append_system_message(f'Skill "{skill_name}" updated with improvements.')
    clear_suggestion()
