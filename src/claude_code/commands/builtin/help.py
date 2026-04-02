"""
Help command.

Display available commands and help information.

Migrated from: commands/help/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class HelpCommand(Command):
    """Display help and available commands."""

    @property
    def name(self) -> str:
        return "help"

    @property
    def aliases(self) -> list[str]:
        return ["?", "h"]

    @property
    def description(self) -> str:
        return "Show help and available commands"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Show help information."""
        from ..registry import get_visible_commands

        commands = get_visible_commands()
        commands.sort(key=lambda c: c.name)

        lines = ["Available commands:", ""]

        for cmd in commands:
            aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"  /{cmd.name}{aliases} - {cmd.description}")

        lines.extend(
            [
                "",
                "Type /<command> to run a command.",
                "Type /help <command> for detailed help.",
            ]
        )

        return CommandResult(
            success=True,
            output="\n".join(lines),
        )
