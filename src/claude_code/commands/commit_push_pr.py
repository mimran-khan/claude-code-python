"""
/commit-push-pr — commit, push, open PR (prompt command).

Migrated from: commands/commit-push-pr.ts
"""

from __future__ import annotations

from typing import Any

from claude_code.commands.spec import CommandSpec, PromptCommandBundle

COMMIT_PUSH_PR_ALLOWED_TOOLS: tuple[str, ...] = (
    "Bash(git checkout --branch:*)",
    "Bash(git checkout -b:*)",
    "Bash(git add:*)",
    "Bash(git status:*)",
    "Bash(git push:*)",
    "Bash(git commit:*)",
    "Bash(gh pr create:*)",
    "Bash(gh pr edit:*)",
    "Bash(gh pr view:*)",
    "Bash(gh pr merge:*)",
    "ToolSearch",
)


def _build_pr_prompt(default_branch: str = "main") -> str:
    return f"""## Context

- `git status`: !`git status`
- `git diff HEAD`: !`git diff HEAD`
- `git branch --show-current`: !`git branch --show-current`
- `git diff {default_branch}...HEAD`: !`git diff {default_branch}...HEAD`
- `gh pr view --json number 2>/dev/null || true`: !`gh pr view --json number 2>/dev/null || true`

## Git Safety Protocol

- NEVER update the git config
- NEVER run destructive/irreversible git commands unless the user explicitly requests them
- NEVER skip hooks unless the user explicitly requests it
- Do not commit files that likely contain secrets

## Your task

1. Create a branch if on {default_branch}
2. Commit with an appropriate message
3. Push and create or update a PR with `gh`

Return the PR URL when done.
"""


async def get_prompt_for_commit_push_pr(args: str, _context: Any) -> list[dict[str, Any]]:
    text = _build_pr_prompt()
    extra = (args or "").strip()
    if extra:
        text += f"\n\n## Additional instructions from user\n\n{extra}"
    return [{"type": "text", "text": text}]


COMMIT_PUSH_PR_SPEC = CommandSpec(
    type="prompt",
    name="commit-push-pr",
    description="Commit, push, and open a PR",
    allowed_tools=COMMIT_PUSH_PR_ALLOWED_TOOLS,
    progress_message="creating commit and PR",
)

COMMIT_PUSH_PR_BUNDLE = PromptCommandBundle(
    spec=COMMIT_PUSH_PR_SPEC,
    get_prompt_for_command=get_prompt_for_commit_push_pr,
)

__all__ = [
    "COMMIT_PUSH_PR_ALLOWED_TOOLS",
    "COMMIT_PUSH_PR_BUNDLE",
    "COMMIT_PUSH_PR_SPEC",
    "get_prompt_for_commit_push_pr",
]
