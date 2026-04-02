"""
Vim command.

Toggle vim mode.

Migrated from: commands/vim/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class VimCommand(Command):
    """Toggle vim keybindings."""

    @property
    def name(self) -> str:
        return "vim"

    @property
    def description(self) -> str:
        return "Toggle vim keybindings"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Toggle vim mode."""
        args = context.args

        if args:
            mode = args[0].lower()
            if mode == "on":
                return CommandResult(
                    success=True,
                    message="Vim mode enabled.",
                    output={"vimMode": True},
                )
            elif mode == "off":
                return CommandResult(
                    success=True,
                    message="Vim mode disabled.",
                    output={"vimMode": False},
                )

        # Toggle
        return CommandResult(
            success=True,
            message="Toggling vim mode...",
            output={"action": "toggleVim"},
        )
