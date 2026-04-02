"""
Login command.

Authenticate with Anthropic.

Migrated from: commands/login/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class LoginCommand(Command):
    """Authenticate with Anthropic."""

    @property
    def name(self) -> str:
        return "login"

    @property
    def description(self) -> str:
        return "Authenticate with your Anthropic account"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Start authentication flow."""
        return CommandResult(
            success=True,
            message="Starting authentication...",
            output={"action": "startAuth"},
        )
