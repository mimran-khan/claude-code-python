"""
Migrated from: commands/security-review.ts
"""

from __future__ import annotations

from claude_code.commands.base import Command, CommandContext, CommandResult
from claude_code.commands.moved_to_plugin import resolve_moved_to_plugin_prompt
from claude_code.commands.pr_comments.moved_plugin import PromptTextBlock
from claude_code.commands.security_review.markdown_body import SECURITY_REVIEW_PROMPT_BODY


async def get_security_review_private_prompt(args: str) -> list[PromptTextBlock]:
    body = SECURITY_REVIEW_PROMPT_BODY.strip()
    if args.strip():
        body = f"{body}\n\nAdditional user input: {args.strip()}"
    return [PromptTextBlock(text=body)]


class SecurityReviewCommand(Command):
    @property
    def name(self) -> str:
        return "security-review"

    @property
    def description(self) -> str:
        return "Complete a security review of the pending changes on the current branch"

    @property
    def command_type(self):
        return "prompt"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        arg_str = " ".join(context.args)
        blocks = await resolve_moved_to_plugin_prompt(
            plugin_name="security-review",
            plugin_command="security-review",
            get_prompt_while_marketplace_is_private=get_security_review_private_prompt,
            args=arg_str,
        )
        return CommandResult(
            success=True,
            output={
                "progress_message": "analyzing code changes for security risks",
                "source": "builtin",
                "prompt_blocks": [b.__dict__ for b in blocks],
            },
        )


__all__ = ["SecurityReviewCommand", "get_security_review_private_prompt"]
