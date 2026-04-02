"""
Conversation branch (fork) helpers.

Migrated from: commands/branch/branch.ts
"""

from __future__ import annotations

from typing import Any


def derive_first_prompt(
    first_user_message: dict[str, Any] | None,
) -> str:
    """
    Derive a single-line title base from the first user message.

    Collapses whitespace so multiline pastes do not break resume titles.
    """
    if not first_user_message or first_user_message.get("type") != "user":
        return "Branched conversation"
    message = first_user_message.get("message") or {}
    content: Any = message.get("content")
    if not content:
        return "Branched conversation"
    raw: str | None
    if isinstance(content, str):
        raw = content
    elif isinstance(content, list):
        raw = None
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                raw = block.get("text")
                break
    else:
        raw = None
    if not raw:
        return "Branched conversation"
    collapsed = " ".join(raw.split()).strip()[:100]
    return collapsed or "Branched conversation"


__all__ = ["derive_first_prompt"]
