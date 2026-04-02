"""
Generate a short recap when the user returns to a session.

Migrated from: services/awaySummary.ts
"""

from __future__ import annotations

from typing import Any

from ..utils.debug import log_for_debugging
from .api.claude import query_model

RECENT_MESSAGE_WINDOW = 30


def _build_away_summary_prompt(memory: str | None) -> str:
    memory_block = f"Session memory (broader context):\n{memory}\n\n" if memory else ""
    return (
        f"{memory_block}"
        "The user stepped away and is coming back. Write exactly 1-3 short sentences. "
        "Start by stating the high-level task — what they are building or debugging, "
        "not implementation details. Next: the concrete next step. "
        "Skip status reports and commit recaps."
    )


async def generate_away_summary(
    messages: list[dict[str, Any]],
    *,
    model: str = "claude-3-5-haiku-20241022",
) -> str | None:
    if not messages:
        return None
    try:
        from .session_memory import get_session_memory

        raw = get_session_memory().content
        memory = raw if raw and raw.strip() else None

        recent = list(messages[-RECENT_MESSAGE_WINDOW:])
        recent.append({"role": "user", "content": _build_away_summary_prompt(memory)})
        result = await query_model(
            messages=recent,
            model=model,
            system="",
            max_tokens=512,
            temperature=0.5,
        )
        parts: list[str] = []
        for block in result.message.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        text = "".join(parts).strip()
        return text or None
    except Exception as err:
        log_for_debugging(f"[away_summary] generation failed: {err}")
        return None
