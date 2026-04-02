"""
Search / slash dialog key handling depends on :mod:`claude_code.utils.cursor`.

Migrated from: hooks/useSearchInput.ts

The TypeScript hook is ~350 lines of Cursor + kill-ring integration. Python TUI
implementations should reuse :class:`claude_code.utils.cursor.Cursor` (when
ported) or prompt-toolkit search mode; this module holds shared key name sets only.
"""

from __future__ import annotations

UNHANDLED_SPECIAL_KEYS = frozenset(
    {
        "pageup",
        "pagedown",
        "insert",
        "wheelup",
        "wheeldown",
        "mouse",
        "f1",
        "f2",
        "f3",
        "f4",
        "f5",
        "f6",
        "f7",
        "f8",
        "f9",
        "f10",
        "f11",
        "f12",
    }
)
