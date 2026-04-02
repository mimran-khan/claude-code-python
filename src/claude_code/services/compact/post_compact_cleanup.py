"""Post-compaction cache cleanup hooks.

Migrated from: services/compact/postCompactCleanup.ts (behavior simplified).
"""

from __future__ import annotations

from collections.abc import Callable

from .micro_compact import reset_microcompact_state

QuerySource = str


def run_post_compact_cleanup(
    query_source: QuerySource | None = None,
    *,
    reset_context_collapse: Callable[[], None] | None = None,
    clear_user_context_cache: Callable[[], None] | None = None,
    reset_memory_files_cache: Callable[[str], None] | None = None,
) -> None:
    """Clear shared caches after compaction; optional hooks for main-thread-only resets."""
    is_main_thread = query_source is None or query_source.startswith("repl_main_thread") or query_source == "sdk"
    reset_microcompact_state()
    if is_main_thread and reset_context_collapse is not None:
        reset_context_collapse()
    if is_main_thread:
        if clear_user_context_cache is not None:
            clear_user_context_cache()
        if reset_memory_files_cache is not None:
            reset_memory_files_cache("compact")
