"""Migrated from: commands/config/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

CONFIG_COMMAND = CommandSpec(
    type="local-jsx",
    name="config",
    description="Open config panel",
    aliases=("settings",),
    load_symbol="claude_code.commands.config.ui",
)

__all__ = ["CONFIG_COMMAND"]
