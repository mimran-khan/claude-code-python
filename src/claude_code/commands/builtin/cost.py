"""
Cost command.

Show cost and usage information.

Migrated from: commands/cost/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class CostCommand(Command):
    """Show cost and usage information."""

    @property
    def name(self) -> str:
        return "cost"

    @property
    def aliases(self) -> list[str]:
        return ["usage"]

    @property
    def description(self) -> str:
        return "Show session cost and usage"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Show cost information."""
        # Would fetch actual cost data
        return CommandResult(
            success=True,
            output={
                "session": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                },
                "total": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                },
            },
        )
