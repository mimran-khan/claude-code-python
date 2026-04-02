"""
Setup command placeholder.

Setup wizard placeholder (see also install-github-app).
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class SetupCommand(Command):
    @property
    def name(self) -> str:
        return "setup"

    @property
    def description(self) -> str:
        return "Setup wizard placeholder"

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "setup", "args": context.args},
        )
