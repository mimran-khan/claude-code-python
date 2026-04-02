"""
Migrated from: commands/plan/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class PlanCommand(Command):
    @property
    def name(self) -> str:
        return "plan"

    @property
    def description(self) -> str:
        return "Enable plan mode or view the current session plan"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={
                "action": "load_jsx",
                "module": "plan",
                "argument_hint": "[open|<description>]",
                "args": context.args,
            },
        )
