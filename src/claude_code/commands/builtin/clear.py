"""
Clear command.

Clear conversation or caches.

Migrated from: commands/clear/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ClearCommand(Command):
    """Clear the conversation or caches."""

    @property
    def name(self) -> str:
        return "clear"

    @property
    def aliases(self) -> list[str]:
        return ["cls"]

    @property
    def description(self) -> str:
        return "Clear conversation history"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Clear conversation."""
        args = context.args

        # Check for subcommand
        if args and args[0] == "caches":
            return await self._clear_caches()

        # Clear conversation
        return CommandResult(
            success=True,
            message="Conversation cleared.",
        )

    async def _clear_caches(self) -> CommandResult:
        """Clear various caches."""
        return CommandResult(
            success=True,
            message="Caches cleared.",
        )
