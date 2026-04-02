"""Migrated from: commands/skills/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

SKILLS_COMMAND = CommandSpec(
    type="local-jsx",
    name="skills",
    description="List available skills",
    load_symbol="claude_code.commands.skills.ui",
)

__all__ = ["SKILLS_COMMAND"]
