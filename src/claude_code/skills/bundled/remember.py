"""Bundled /remember skill. Migrated from: skills/bundled/remember.ts"""

from __future__ import annotations

import os

from ...memdir import is_auto_memory_enabled
from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition

SKILL_PROMPT = """# Memory Review

## Goal
Review the user's memory landscape and produce a clear report of proposed changes, grouped by action type. Do NOT apply changes — present proposals for user approval.

## Steps

### 1. Gather all memory layers
Read CLAUDE.md and CLAUDE.local.md from the project root (if they exist).

### 2. Classify each auto-memory entry
Determine the best destination: CLAUDE.md, CLAUDE.local.md, team memory, or stay in auto-memory.

### 3. Identify cleanup opportunities
Duplicates, outdated entries, conflicts across layers.

### 4. Present the report
Grouped by Promotions, Cleanup, Ambiguous, No action needed.

## Rules
- Present ALL proposals before making any changes
- Do NOT modify files without explicit user approval
"""


def register_remember_skill() -> None:
    if os.environ.get("USER_TYPE") != "ant":
        return

    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        prompt = SKILL_PROMPT
        if args:
            prompt += f"\n## Additional context from user\n\n{args}"
        return [{"type": "text", "text": prompt}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="remember",
            description=(
                "Review auto-memory entries and propose promotions to CLAUDE.md, CLAUDE.local.md, or shared memory."
            ),
            when_to_use=("Use when the user wants to review, organize, or promote their auto-memory entries."),
            user_invocable=True,
            is_enabled=is_auto_memory_enabled,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
