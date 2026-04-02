"""
Update command placeholder.

Update check placeholder.
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class UpdateCommand(Command):
    @property
    def name(self) -> str:
        return "update"

    @property
    def description(self) -> str:
        return "Update check placeholder."

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "update", "args": context.args},
        )
