"""
Shared prompt strings and small prompt helpers used by system prompt assembly.

Migrated from: constants/prompts.ts (exported constants and prependBullets only).
"""

from __future__ import annotations

from collections.abc import Sequence

CLAUDE_CODE_DOCS_MAP_URL = "https://code.claude.com/docs/en/claude_code_docs_map.md"

# Boundary marker for cross-org cacheable vs dynamic system prompt segments.
# WARNING: Keep in sync with API cache split logic when changing.
SYSTEM_PROMPT_DYNAMIC_BOUNDARY = "__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__"

# @[MODEL LAUNCH]: Update the latest frontier model name when the product ships it.
FRONTIER_MODEL_NAME = "Claude Opus 4.6"

# @[MODEL LAUNCH]: Update model family IDs to the latest in each tier.
CLAUDE_4_5_OR_4_6_MODEL_IDS: dict[str, str] = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

DEFAULT_AGENT_PROMPT = (
    "You are an agent for Claude Code, Anthropic's official CLI for Claude. "
    "Given the user's message, you should use the tools available to complete "
    "the task. Complete the task fully—don't gold-plate, but don't leave it "
    "half-done. When you complete the task, respond with a concise report "
    "covering what was done and any key findings — the caller will relay this "
    "to the user, so it only needs the essentials."
)


def prepend_bullets(items: Sequence[str | Sequence[str]]) -> list[str]:
    """Format list items as markdown bullet lines (matches TS prependBullets)."""
    out: list[str] = []
    for item in items:
        if isinstance(item, (list, tuple)):
            out.extend(f"  - {subitem}" for subitem in item)
        else:
            out.append(f" - {item}")
    return out
