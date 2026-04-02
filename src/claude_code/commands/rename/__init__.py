"""Migrated from: commands/rename/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

RENAME_COMMAND = CommandSpec(
    type="local-jsx",
    name="rename",
    description="Rename the current conversation",
    immediate=True,
    argument_hint="[name]",
    load_symbol="claude_code.commands.rename.ui",
)

__all__ = ["RENAME_COMMAND"]
