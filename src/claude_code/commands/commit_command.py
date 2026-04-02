"""
/commit — create a git commit (prompt command).

Migrated from: commands/commit.ts
"""

from __future__ import annotations

from typing import Any

from claude_code.commands.spec import CommandSpec, PromptCommandBundle

COMMIT_ALLOWED_TOOLS: tuple[str, ...] = (
    "Bash(git add:*)",
    "Bash(git status:*)",
    "Bash(git commit:*)",
)


def _build_commit_prompt() -> str:
    return """## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Git Safety Protocol

- NEVER update the git config
- NEVER skip hooks (--no-verify, --no-gpg-sign, etc) unless the user explicitly requests it
- CRITICAL: ALWAYS create NEW commits. NEVER use git commit --amend, unless the user explicitly requests it
- Do not commit files that likely contain secrets (.env, credentials.json, etc)
- If there are no changes to commit, do not create an empty commit
- Never use git commands with the -i flag since they require interactive input which is not supported

## Your task

Based on the above changes, create a single git commit using HEREDOC syntax for the message.
You MUST do this in a single message with only the required tool calls.
"""


async def get_prompt_for_commit(_args: str, _context: Any) -> list[dict[str, Any]]:
    return [{"type": "text", "text": _build_commit_prompt()}]


COMMIT_COMMAND_SPEC = CommandSpec(
    type="prompt",
    name="commit",
    description="Create a git commit",
    allowed_tools=COMMIT_ALLOWED_TOOLS,
    content_length=0,
    progress_message="creating commit",
)

COMMIT_PROMPT_BUNDLE = PromptCommandBundle(
    spec=COMMIT_COMMAND_SPEC,
    get_prompt_for_command=get_prompt_for_commit,
)

__all__ = [
    "COMMIT_ALLOWED_TOOLS",
    "COMMIT_COMMAND_SPEC",
    "COMMIT_PROMPT_BUNDLE",
    "get_prompt_for_commit",
]
