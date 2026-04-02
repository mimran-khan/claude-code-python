"""Migrated from: commands/color/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

COLOR_COMMAND = CommandSpec(
    type="local-jsx",
    name="color",
    description="Set the prompt bar color for this session",
    immediate=True,
    argument_hint="<color|default>",
    load_symbol="claude_code.commands.color.ui",
)

__all__ = ["COLOR_COMMAND"]
