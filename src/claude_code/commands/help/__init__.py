"""Migrated from: commands/help/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

HELP_COMMAND = CommandSpec(
    type="local-jsx",
    name="help",
    description="Show help and available commands",
    load_symbol="claude_code.commands.help.ui",
)

__all__ = ["HELP_COMMAND"]
