"""
Migrated from: commands/vim/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class VimCommand(Command):
    @property
    def name(self) -> str:
        return "vim"

    @property
    def description(self) -> str:
        return "Toggle between Vim and Normal editing modes"

    async def execute(self, context: CommandContext) -> CommandResult:
        _ = context
        from .vim_call import call as vim_call

        result = await vim_call()
        return CommandResult(
            success=True,
            message=result.get("value", ""),
            output={"action": "vim_toggle", **result},
        )
