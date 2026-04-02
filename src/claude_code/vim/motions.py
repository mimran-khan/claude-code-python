"""
Vim motion resolution (pure cursor math).

Migrated from: vim/motions.ts
"""

from __future__ import annotations

from typing import Any

_MOTION_ALIASES: dict[str, tuple[str, ...]] = {
    "h": ("left",),
    "l": ("right",),
    "j": ("down_logical_line", "downLogicalLine"),
    "k": ("up_logical_line", "upLogicalLine"),
    "gj": ("down",),
    "gk": ("up",),
    "w": ("next_vim_word", "nextVimWord"),
    "b": ("prev_vim_word", "prevVimWord"),
    "e": ("end_of_vim_word", "endOfVimWord"),
    "W": ("next_w_o_r_d", "nextWORD"),
    "B": ("prev_w_o_r_d", "prevWORD"),
    "E": ("end_of_w_o_r_d", "endOfWORD"),
    "0": ("start_of_logical_line", "startOfLogicalLine"),
    "^": ("first_non_blank_in_logical_line", "firstNonBlankInLogicalLine"),
    "$": ("end_of_logical_line", "endOfLogicalLine"),
    "G": ("start_of_last_line", "startOfLastLine"),
}


def _apply_single_motion(key: str, cursor: Any) -> Any:
    for name in _MOTION_ALIASES.get(key, ()):
        fn = getattr(cursor, name, None)
        if callable(fn):
            return fn()
    return cursor


def resolve_motion(key: str, cursor: Any, count: int) -> Any:
    """Apply motion ``key`` ``count`` times (stops when cursor stops moving)."""
    result = cursor
    for _ in range(max(1, count)):
        nxt = _apply_single_motion(key, result)
        equals = getattr(nxt, "equals", None)
        if callable(equals) and equals(result):
            break
        result = nxt
    return result


def is_inclusive_motion(key: str) -> bool:
    return key in frozenset("eE$")


def is_linewise_motion(key: str) -> bool:
    return key in frozenset("jkG")
