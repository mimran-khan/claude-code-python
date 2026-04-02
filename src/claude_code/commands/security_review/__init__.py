"""Migrated from: commands/security-review.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

from .command import SecurityReviewCommand

SECURITY_REVIEW_COMMAND_SPEC = CommandSpec(
    type="prompt",
    name="security-review",
    description="Complete a security review of the pending changes on the current branch",
    progress_message="analyzing code changes for security risks",
    content_length=0,
    allowed_tools=(
        "Bash(git diff:*)",
        "Bash(git status:*)",
        "Bash(git log:*)",
        "Bash(git show:*)",
        "Bash(git remote show:*)",
        "Read",
        "Glob",
        "Grep",
        "LS",
        "Task",
    ),
    supports_non_interactive=False,
    load_symbol="claude_code.commands.security_review.command",
)

__all__ = ["SECURITY_REVIEW_COMMAND_SPEC", "SecurityReviewCommand"]
