"""
Review command.

Review code changes.

Migrated from: commands/review.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ReviewCommand(Command):
    """Review code changes."""

    @property
    def name(self) -> str:
        return "review"

    @property
    def description(self) -> str:
        return "Review code changes or PR"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Start code review."""
        args = context.args

        # Optional PR URL or branch
        target = args[0] if args else None

        return CommandResult(
            success=True,
            message="Starting code review...",
            output={
                "action": "review",
                "target": target,
            },
        )
