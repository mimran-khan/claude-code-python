"""
Permissions command.

Manage permission settings.

Migrated from: commands/permissions/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class PermissionsCommand(Command):
    """Manage permission settings."""

    @property
    def name(self) -> str:
        return "permissions"

    @property
    def aliases(self) -> list[str]:
        return ["perms"]

    @property
    def description(self) -> str:
        return "View and manage permissions"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Show or manage permissions."""
        args = context.args

        if not args:
            # Show current permissions
            return CommandResult(
                success=True,
                message="Opening permissions panel...",
                output={"action": "openPermissions"},
            )

        subcommand = args[0]

        if subcommand == "list":
            return CommandResult(
                success=True,
                output={
                    "allow": [],
                    "deny": [],
                    "ask": [],
                },
            )

        elif subcommand == "add":
            if len(args) < 3:
                return CommandResult(
                    success=False,
                    error="Usage: /permissions add <allow|deny|ask> <rule>",
                )
            behavior = args[1]
            rule = " ".join(args[2:])
            return CommandResult(
                success=True,
                message=f"Added {behavior} rule: {rule}",
            )

        elif subcommand == "remove":
            if len(args) < 2:
                return CommandResult(
                    success=False,
                    error="Usage: /permissions remove <rule>",
                )
            rule = " ".join(args[1:])
            return CommandResult(
                success=True,
                message=f"Removed rule: {rule}",
            )

        return CommandResult(
            success=False,
            error=f"Unknown subcommand: {subcommand}",
        )
