"""
Migrated from: commands/pr_comments/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult
from .moved_plugin import PR_COMMENTS_CONFIG, get_prompt_while_marketplace_is_private


class PrCommentsCommand(Command):
    @property
    def name(self) -> str:
        return PR_COMMENTS_CONFIG.name

    @property
    def description(self) -> str:
        return PR_COMMENTS_CONFIG.description

    @property
    def command_type(self):
        return "prompt"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        args = " ".join(context.args) if context.args else None
        blocks = await get_prompt_while_marketplace_is_private(args)
        return CommandResult(
            success=True,
            output={
                "progress_message": PR_COMMENTS_CONFIG.progress_message,
                "plugin_name": PR_COMMENTS_CONFIG.plugin_name,
                "plugin_command": PR_COMMENTS_CONFIG.plugin_command,
                "prompt_blocks": [b.__dict__ for b in blocks],
            },
        )
