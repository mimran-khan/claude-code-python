"""Migrated from: commands/theme/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

THEME_COMMAND = CommandSpec(
    type="local-jsx",
    name="theme",
    description="Change the theme",
    load_symbol="claude_code.commands.theme.ui",
)

__all__ = ["THEME_COMMAND"]
