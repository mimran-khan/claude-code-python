"""
Exit command.

Exit the application.

Migrated from: commands/exit/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ExitCommand(Command):
    """Exit the application."""

    @property
    def name(self) -> str:
        return "exit"

    @property
    def aliases(self) -> list[str]:
        return ["quit", "q"]

    @property
    def description(self) -> str:
        return "Exit Claude Code"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Exit the application."""
        # In a full implementation, this would signal app exit
        return CommandResult(
            success=True,
            message="Goodbye!",
            output={"action": "exit"},
        )
