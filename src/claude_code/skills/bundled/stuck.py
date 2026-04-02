"""Bundled /stuck skill. Migrated from: skills/bundled/stuck.ts"""

from __future__ import annotations

import os

from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition

STUCK_PROMPT = """# /stuck — diagnose frozen/slow Claude Code sessions

The user thinks another Claude Code session on this machine is frozen, stuck, or very slow. Investigate and post a report.

## What to look for

Scan for other Claude Code processes. Signs: high CPU, D/T/Z state, high RSS, stuck child processes.

## Investigation steps

1. List processes (platform-appropriate).
2. Gather child processes and debug log tails from ~/.claude/debug/ when possible.

## Report

Summarize findings for the user. Do not kill processes — diagnostic only.
"""


def register_stuck_skill() -> None:
    if os.environ.get("USER_TYPE") != "ant":
        return

    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        prompt = STUCK_PROMPT
        if args:
            prompt += f"\n## User-provided context\n\n{args}\n"
        return [{"type": "text", "text": prompt}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="stuck",
            description=("[ANT-ONLY] Investigate frozen/stuck/slow Claude Code sessions on this machine."),
            user_invocable=True,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
