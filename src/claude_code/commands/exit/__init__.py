"""Migrated from: commands/exit/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

EXIT_COMMAND = CommandSpec(
    type="local-jsx",
    name="exit",
    aliases=("quit",),
    description="Exit the REPL",
    immediate=True,
    load_symbol="claude_code.commands.exit.ui",
)

__all__ = ["EXIT_COMMAND"]
