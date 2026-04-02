"""
Version command.

Show version information.

Migrated from: commands/version.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class VersionCommand(Command):
    """Show version information."""

    @property
    def name(self) -> str:
        return "version"

    @property
    def aliases(self) -> list[str]:
        return ["ver", "v"]

    @property
    def description(self) -> str:
        return "Show version information"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Show version."""
        return CommandResult(
            success=True,
            output={
                "version": "0.1.0",
                "python_version": "3.11+",
                "platform": "Python",
            },
            message="Claude Code Python v0.1.0",
        )
