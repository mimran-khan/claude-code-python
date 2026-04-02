"""
Project command placeholder.

Project commands (no matching commands/*.ts in this workspace).
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ProjectCommand(Command):
    @property
    def name(self) -> str:
        return "project"

    @property
    def description(self) -> str:
        return "Project commands"

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "project", "args": context.args},
        )
