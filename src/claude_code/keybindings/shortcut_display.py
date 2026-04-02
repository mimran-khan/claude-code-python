"""
Resolve shortcut display text for an action (non-React).

Migrated from: keybindings/shortcutFormat.ts
"""

from __future__ import annotations

from .load_user_bindings import load_keybindings_sync, log_keybinding_fallback
from .resolver import get_binding_display_text

_LOGGED_FALLBACKS: set[str] = set()


def get_shortcut_display(action: str, context: str, fallback: str) -> str:
    """
    Configured chord string for ``action`` in ``context``, or ``fallback``.

    Logs at most once per (action, context) when falling back (optional logger).
    """
    bindings = load_keybindings_sync()
    resolved = get_binding_display_text(action, context, bindings)
    if resolved is None:
        key = f"{action}:{context}"
        if key not in _LOGGED_FALLBACKS:
            _LOGGED_FALLBACKS.add(key)
            log_keybinding_fallback(action, context, fallback, "action_not_found")
        return fallback
    return resolved


def reset_shortcut_display_fallback_log() -> None:
    """Clear fallback dedupe set (tests)."""
    _LOGGED_FALLBACKS.clear()


__all__ = ["get_shortcut_display", "reset_shortcut_display_fallback_log"]
