"""Bundled /simplify skill. Migrated from: skills/bundled/simplify.ts"""

from __future__ import annotations

from ...constants.tools import AGENT_TOOL_NAME
from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition

SIMPLIFY_PROMPT = f"""# Simplify: Code Review and Cleanup

Review all changed files for reuse, quality, and efficiency. Fix any issues found.

## Phase 1: Identify Changes

Run `git diff` (or `git diff HEAD` if there are staged changes) to see what changed. If there are no git changes, review the most recently modified files that the user mentioned or that you edited earlier in this conversation.

## Phase 2: Launch Three Review Agents in Parallel

Use the {AGENT_TOOL_NAME} tool to launch all three agents concurrently in a single message. Pass each agent the full diff so it has the complete context.

### Agent 1: Code Reuse Review
### Agent 2: Code Quality Review
### Agent 3: Efficiency Review

## Phase 3: Fix Issues

Wait for all three agents to complete. Aggregate their findings and fix each issue directly.
"""


def register_simplify_skill() -> None:
    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        prompt = SIMPLIFY_PROMPT
        if args:
            prompt += f"\n\n## Additional Focus\n\n{args}"
        return [{"type": "text", "text": prompt}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="simplify",
            description="Review changed code for reuse, quality, and efficiency, then fix any issues found.",
            user_invocable=True,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
