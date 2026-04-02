"""Migrated from: commands/rewind/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

REWIND_COMMAND = CommandSpec(
    type="local",
    name="rewind",
    description="Restore the code and/or conversation to a previous point",
    aliases=("checkpoint",),
    argument_hint="",
    supports_non_interactive=False,
    load_symbol="claude_code.commands.rewind.rewind_impl",
)

__all__ = ["REWIND_COMMAND"]
