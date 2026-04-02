"""
React/Ink hooks for keybindings (UI layer).

The TypeScript module ``useKeybinding.ts`` exports ``useKeybinding`` and
``useKeybindings`` (plural), registering handlers with Ink ``useInput`` and
``KeybindingContext``. The Python CLI has no React tree; use
:func:`~claude_code.keybindings.resolve_key` and
:func:`~claude_code.keybindings.resolve_key_with_chord_state` with your TUI
input layer, or :class:`~claude_code.keybindings.KeybindingResolver`.
"""

from __future__ import annotations

# Re-export backend entry points for discoverability
from .resolver import KeybindingResolver, resolve_key, resolve_key_with_chord_state

__all__ = ["KeybindingResolver", "resolve_key", "resolve_key_with_chord_state"]
