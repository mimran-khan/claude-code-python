"""
Hooks command.

Manage hooks.

Migrated from: commands/hooks/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class HooksCommand(Command):
    """Manage hooks."""

    @property
    def name(self) -> str:
        return "hooks"

    @property
    def description(self) -> str:
        return "View and manage hooks"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Manage hooks."""
        args = context.args

        if not args:
            return CommandResult(
                success=True,
                message="Hooks Commands: list, add, remove",
                output={"action": "showHooksHelp"},
            )

        subcommand = args[0]

        if subcommand == "list":
            return CommandResult(
                success=True,
                output={
                    "hooks": [],
                    "message": "No hooks configured.",
                },
            )

        return CommandResult(
            success=False,
            error=f"Unknown subcommand: {subcommand}",
        )
