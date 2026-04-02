"""
Status command.

Show session status.

Migrated from: commands/status/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class StatusCommand(Command):
    """Show session status."""

    @property
    def name(self) -> str:
        return "status"

    @property
    def description(self) -> str:
        return "Show session status"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Show status."""
        return CommandResult(
            success=True,
            output={
                "session_id": "unknown",
                "mode": "agent",
                "model": "claude-sonnet-4-20250514",
                "authenticated": False,
            },
        )
