"""
Message kind checks (human vs tool-result user turns).

Migrated from: utils/messagePredicates.ts
"""

from __future__ import annotations

from typing import Any


def is_human_turn(m: Any) -> bool:
    """True for a real user turn (not meta, not a tool-result wrapper)."""

    mtype = getattr(m, "type", None)
    if mtype is None:
        mtype = getattr(m, "role", None)
    if mtype != "user":
        return False
    if getattr(m, "is_meta", None) or getattr(m, "isMeta", None):
        return False
    tool_res = getattr(m, "tool_use_result", None)
    if tool_res is None:
        tool_res = getattr(m, "toolUseResult", None)
    return tool_res is None


__all__ = ["is_human_turn"]
