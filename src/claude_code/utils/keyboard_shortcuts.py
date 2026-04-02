"""
macOS Option-key special character → logical shortcut mapping.

Migrated from: utils/keyboardShortcuts.ts
"""

from __future__ import annotations

MACOS_OPTION_SPECIAL_CHARS: dict[str, str] = {
    "†": "alt+t",
    "π": "alt+p",
    "ø": "alt+o",
}


def is_macos_option_char(char: str) -> bool:
    """Return True if ``char`` is a known Option+key sentinel."""

    return char in MACOS_OPTION_SPECIAL_CHARS


__all__ = ["MACOS_OPTION_SPECIAL_CHARS", "is_macos_option_char"]
