"""
Migrated from: commands/pr_comments/index.ts (createMovedToPluginCommand payload).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTextBlock:
    type: str = "text"
    text: str = ""


@dataclass(frozen=True)
class MovedToPluginConfig:
    name: str
    description: str
    progress_message: str
    plugin_name: str
    plugin_command: str


PR_COMMENTS_CONFIG = MovedToPluginConfig(
    name="pr-comments",
    description="Get comments from a GitHub pull request",
    progress_message="fetching PR comments",
    plugin_name="pr-comments",
    plugin_command="pr-comments",
)


async def get_prompt_while_marketplace_is_private(
    args: str | None,
) -> list[PromptTextBlock]:
    """Fallback prompt when marketplace plugin is not yet available."""

    suffix = f"\n\nAdditional user input: {args}" if args else ""
    body = f"""You are an AI assistant integrated into a git-based version control system. Your task is to fetch and display comments from a GitHub pull request.

Follow these steps:

1. Use `gh pr view --json number,headRepository` to get the PR number and repository info
2. Use `gh api /repos/{{owner}}/{{repo}}/issues/{{number}}/comments` to get PR-level comments
3. Use `gh api /repos/{{owner}}/{{repo}}/pulls/{{number}}/comments` to get review comments. Pay particular attention to the following fields: `body`, `diff_hunk`, `path`, `line`, etc. If the comment references some code, consider fetching it using eg `gh api /repos/{{owner}}/{{repo}}/contents/{{path}}?ref={{branch}} | jq .content -r | base64 -d`
4. Parse and format all comments in a readable way
5. Return ONLY the formatted comments, with no additional text

Format the comments as:

## Comments

[For each comment thread:]
- @author file.ts#line:
  ```diff
  [diff_hunk from the API response]
  ```
  > quoted comment text

  [any replies indented]

If there are no comments, return "No comments found."

Remember:
1. Only show the actual comments, no explanatory text
2. Include both PR-level and code review comments
3. Preserve the threading/nesting of comment replies
4. Show the file and line number context for code review comments
5. Use jq to parse the JSON responses from the GitHub API
{suffix}"""
    return [PromptTextBlock(text=body)]
