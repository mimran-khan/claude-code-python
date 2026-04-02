"""
Thinking command placeholder.

Extended thinking toggle placeholder.
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ThinkingCommand(Command):
    @property
    def name(self) -> str:
        return "thinking"

    @property
    def description(self) -> str:
        return "Extended thinking toggle placeholder."

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "thinking", "args": context.args},
        )
