"""
Files command.

List files in context.

Migrated from: commands/files/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class FilesCommand(Command):
    """List files in the current context."""

    @property
    def name(self) -> str:
        return "files"

    @property
    def description(self) -> str:
        return "List files added to context"

    async def execute(self, context: CommandContext) -> CommandResult:
        """List files in context."""
        # Would fetch actual files
        return CommandResult(
            success=True,
            output={
                "files": [],
                "message": "No files in context.",
            },
        )
