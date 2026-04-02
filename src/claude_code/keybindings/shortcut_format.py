"""
Resolve configured shortcut display text without React.

Migrated from: ``keybindings/shortcutFormat.ts``. Implementation:
:mod:`claude_code.keybindings.shortcut_display`.
"""

from __future__ import annotations

from .shortcut_display import get_shortcut_display, reset_shortcut_display_fallback_log

__all__ = ["get_shortcut_display", "reset_shortcut_display_fallback_log"]
