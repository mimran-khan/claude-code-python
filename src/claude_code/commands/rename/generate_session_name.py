"""
Migrated from: commands/rename/generateSessionName.ts

LLM-backed session title generation; wire query_haiku / messages when API layer exists.
"""

from __future__ import annotations

from typing import Any


async def generate_session_name(
    messages: list[Any],
    signal: Any | None = None,
) -> str | None:
    """Return a kebab-case session name or None if conversation text is empty."""

    if not messages:
        return None
    return None


__all__ = ["generate_session_name"]
