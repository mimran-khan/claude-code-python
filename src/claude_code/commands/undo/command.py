"""
Undo command placeholder.

Undo / rewind placeholder (see rewind in TS tree).
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class UndoCommand(Command):
    @property
    def name(self) -> str:
        return "undo"

    @property
    def description(self) -> str:
        return "Undo / rewind placeholder"

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "undo", "args": context.args},
        )
