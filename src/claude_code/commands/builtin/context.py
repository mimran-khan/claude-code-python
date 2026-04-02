"""
Context command.

Manage context.

Migrated from: commands/context/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ContextCommand(Command):
    """Manage conversation context."""

    @property
    def name(self) -> str:
        return "context"

    @property
    def aliases(self) -> list[str]:
        return ["ctx"]

    @property
    def description(self) -> str:
        return "View and manage context"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Manage context."""
        args = context.args

        if not args:
            return CommandResult(
                success=True,
                message="Context Commands: show, clear, add",
                output={"action": "showContextHelp"},
            )

        subcommand = args[0]

        if subcommand == "show":
            return CommandResult(
                success=True,
                output={
                    "files": [],
                    "tokens": 0,
                    "message": "Context is empty.",
                },
            )

        elif subcommand == "clear":
            return CommandResult(
                success=True,
                message="Context cleared.",
            )

        elif subcommand == "add":
            if len(args) < 2:
                return CommandResult(
                    success=False,
                    error="Usage: /context add <file-or-directory>",
                )
            path = args[1]
            return CommandResult(
                success=True,
                message=f"Adding to context: {path}",
            )

        return CommandResult(
            success=False,
            error=f"Unknown subcommand: {subcommand}",
        )
