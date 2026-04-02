"""
Profile command placeholder.

User profile (no matching commands/*.ts in this workspace).
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ProfileCommand(Command):
    @property
    def name(self) -> str:
        return "profile"

    @property
    def description(self) -> str:
        return "User profile"

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="Placeholder: wire UI or prompt when TS source is available.",
            output={"module": "profile", "args": context.args},
        )
