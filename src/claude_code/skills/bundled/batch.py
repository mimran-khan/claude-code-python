"""Bundled /batch skill. Migrated from: skills/bundled/batch.ts"""

from __future__ import annotations

from ...constants.tools import (
    AGENT_TOOL_NAME,
    ASK_USER_QUESTION_TOOL_NAME,
    ENTER_PLAN_MODE_TOOL_NAME,
    EXIT_PLAN_MODE_TOOL_NAME,
    SKILL_TOOL_NAME,
)
from ...utils.git import get_is_git
from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition

MIN_AGENTS = 5
MAX_AGENTS = 30

WORKER_INSTRUCTIONS = f"""After you finish implementing the change:
1. **Simplify** — Invoke the `{SKILL_TOOL_NAME}` tool with `skill: "simplify"` to review and clean up your changes.
2. **Run unit tests** — Run the project's test suite (check for package.json scripts, Makefile targets, or common commands like `npm test`, `pytest`, `go test`). If tests fail, fix them.
3. **Test end-to-end** — Follow the e2e test recipe from the coordinator's prompt (below). If the recipe says to skip e2e for this unit, skip it.
4. **Commit and push** — Commit all changes with a clear message, push the branch, and create a PR with `gh pr create`. Use a descriptive title. If `gh` is not available or the push fails, note it in your final message.
5. **Report** — End with a single line: `PR: <url>` so the coordinator can track it. If no PR was created, end with `PR: none — <reason>`."""


def _build_prompt(instruction: str) -> str:
    return f"""# Batch: Parallel Work Orchestration

You are orchestrating a large, parallelizable change across this codebase.

## User Instruction

{instruction}

## Phase 1: Research and Plan (Plan Mode)

Call the `{ENTER_PLAN_MODE_TOOL_NAME}` tool now to enter plan mode, then:

1. **Understand the scope.** Launch one or more subagents (in the foreground — you need their results) to deeply research what this instruction touches.
2. **Decompose into independent units.** Break the work into {MIN_AGENTS}–{MAX_AGENTS} self-contained units.
3. **Determine the e2e test recipe.** If unclear, use the `{ASK_USER_QUESTION_TOOL_NAME}` tool to ask the user how to verify end-to-end.
4. **Write the plan** and call `{EXIT_PLAN_MODE_TOOL_NAME}` to present it for approval.

## Phase 2: Spawn Workers (After Plan Approval)

Spawn one background agent per work unit using the `{AGENT_TOOL_NAME}` tool. **All agents must use `isolation: "worktree"` and `run_in_background: true`.**

Include this worker template verbatim:

```
{WORKER_INSTRUCTIONS}
```

## Phase 3: Track Progress

Render a status table and update it as agents complete. Parse `PR: <url>` from each result.
"""


NOT_A_GIT_REPO_MESSAGE = """This is not a git repository. The `/batch` command requires a git repo because it spawns agents in isolated git worktrees and creates PRs from each."""

MISSING_INSTRUCTION_MESSAGE = """Provide an instruction describing the batch change you want to make.

Examples:
  /batch migrate from react to vue
  /batch replace all uses of lodash with native equivalents
  /batch add type annotations to all untyped function parameters"""


def register_batch_skill() -> None:
    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        instruction = args.strip()
        if not instruction:
            return [{"type": "text", "text": MISSING_INSTRUCTION_MESSAGE}]
        is_git = await get_is_git()
        if not is_git:
            return [{"type": "text", "text": NOT_A_GIT_REPO_MESSAGE}]
        return [{"type": "text", "text": _build_prompt(instruction)}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="batch",
            description=(
                "Research and plan a large-scale change, then execute it in parallel across "
                "5–30 isolated worktree agents that each open a PR."
            ),
            when_to_use=(
                "Use when the user wants to make a sweeping, mechanical change across many files "
                "(migrations, refactors, bulk renames) that can be decomposed into independent "
                "parallel units."
            ),
            argument_hint="<instruction>",
            user_invocable=True,
            disable_model_invocation=True,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
