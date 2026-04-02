"""
Migrated from: commands/resume/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ResumeCommand(Command):
    @property
    def name(self) -> str:
        return "resume"

    @property
    def aliases(self) -> list[str]:
        return ["continue"]

    @property
    def description(self) -> str:
        return "Resume a previous conversation"

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={
                "action": "load_jsx",
                "module": "resume",
                "argument_hint": "[conversation id or search term]",
                "args": context.args,
            },
        )
