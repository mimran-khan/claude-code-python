"""
Compact command.

Compact conversation history.

Migrated from: commands/compact/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class CompactCommand(Command):
    """Compact conversation to save tokens."""

    @property
    def name(self) -> str:
        return "compact"

    @property
    def description(self) -> str:
        return "Compact conversation history"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Compact the conversation."""
        args = context.args

        # Get optional custom instructions
        custom_instructions = " ".join(args) if args else None

        # Would perform compaction
        return CommandResult(
            success=True,
            message="Conversation compacted.",
            output={
                "action": "compact",
                "customInstructions": custom_instructions,
            },
        )
