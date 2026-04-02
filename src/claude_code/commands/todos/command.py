"""
Todos command placeholder.

Todo integration placeholder.
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class TodosCommand(Command):
    @property
    def name(self) -> str:
        return "todos"

    @property
    def description(self) -> str:
        return "Todo integration placeholder."

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "todos", "args": context.args},
        )
