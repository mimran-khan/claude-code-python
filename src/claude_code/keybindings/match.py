"""
Map terminal / Ink-style key events to parsed keystrokes and bindings.

Migrated from: ``keybindings/match.ts``. Implementation lives in
:mod:`claude_code.keybindings.ink_match`; this module preserves the original
TypeScript module name for parity with the JS tree.
"""

from __future__ import annotations

from .ink_match import (
    KeyEventLike,
    get_key_name,
    keystroke_matches_binding,
    matches_binding,
    matches_keystroke,
    modifiers_match,
)

__all__ = [
    "KeyEventLike",
    "get_key_name",
    "keystroke_matches_binding",
    "matches_binding",
    "matches_keystroke",
    "modifiers_match",
]
