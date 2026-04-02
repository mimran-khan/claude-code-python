"""
Run command placeholder.

Run command placeholder.
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class RunCommand(Command):
    @property
    def name(self) -> str:
        return "run"

    @property
    def description(self) -> str:
        return "Run command placeholder."

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "run", "args": context.args},
        )
