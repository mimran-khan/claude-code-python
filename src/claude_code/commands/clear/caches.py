"""
Session cache clearing (subset of /clear without transcript wipe).

Migrated from: commands/clear/caches.ts
"""

from __future__ import annotations

import os


def clear_session_caches(preserved_agent_ids: set[str] | frozenset[str] | None = None) -> None:
    """
    Clear session-related caches.

    When ``preserved_agent_ids`` is non-empty, some subsystems skip full resets
    so background agents keep functioning (mirrors TypeScript preserved set).
    """
    _preserved = preserved_agent_ids or set()
    has_preserved = len(_preserved) > 0

    try:
        from claude_code.context import clear_context_caches

        clear_context_caches()
    except Exception:
        pass

    try:
        from claude_code.utils.plugins.loader import clear_plugin_cache

        clear_plugin_cache("session_clear")
    except Exception:
        pass

    try:
        from claude_code.services.magic_docs.magic_docs import clear_tracked_magic_docs

        clear_tracked_magic_docs()
    except Exception:
        pass

    if os.environ.get("USER_TYPE") == "ant" and not has_preserved:
        try:
            from claude_code.services.tips.registry import clear_tips

            clear_tips()
        except Exception:
            pass


__all__ = ["clear_session_caches"]
