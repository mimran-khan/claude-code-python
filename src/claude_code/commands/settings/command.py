"""
Settings command placeholder.

Settings UI placeholder.
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class SettingsCommand(Command):
    @property
    def name(self) -> str:
        return "settings"

    @property
    def description(self) -> str:
        return "Settings UI placeholder."

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "settings", "args": context.args},
        )
