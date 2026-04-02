"""
Logout command.

Sign out of Anthropic account.

Migrated from: commands/logout/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class LogoutCommand(Command):
    """Sign out of Anthropic account."""

    @property
    def name(self) -> str:
        return "logout"

    @property
    def description(self) -> str:
        return "Sign out of your Anthropic account"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Sign out."""
        return CommandResult(
            success=True,
            message="Signed out successfully.",
            output={"action": "logout"},
        )
