"""
Diff command.

Show file changes.

Migrated from: commands/diff/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class DiffCommand(Command):
    """Show file changes and diffs."""

    @property
    def name(self) -> str:
        return "diff"

    @property
    def description(self) -> str:
        return "Show file changes made in this session"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Show file diffs."""
        # Would fetch actual file changes
        return CommandResult(
            success=True,
            output={
                "changes": [],
                "message": "No file changes in this session.",
            },
        )
