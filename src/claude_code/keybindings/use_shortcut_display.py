"""
React hook for shortcut display strings (UI layer).

``useShortcutDisplay.ts`` reads from React context. For services and CLI code,
use :func:`claude_code.keybindings.get_shortcut_display` instead.
"""

from __future__ import annotations

from .shortcut_display import get_shortcut_display

__all__ = ["get_shortcut_display"]
