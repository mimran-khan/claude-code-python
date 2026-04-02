"""
Clear the active conversation and reset session-scoped state.

Migrated from: commands/clear/conversation.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from claude_code.core.tool import FileStateCache

from .caches import clear_session_caches


@dataclass
class ClearConversationParams:
    """Callbacks and mutable state required to perform a full /clear."""

    set_messages: Callable[[Callable[[list[Any]], list[Any]]], None]
    read_file_state: FileStateCache
    discovered_skill_names: set[str] | None = None
    loaded_nested_memory_paths: set[str] | None = None
    get_app_state: Callable[[], Any] | None = None
    set_app_state: Callable[[Callable[[Any], Any]], None] | None = None
    set_conversation_id: Callable[[UUID], None] | None = None
    execute_session_end_hooks: Callable[..., Awaitable[None]] | None = None
    process_session_start_hooks: Callable[..., Awaitable[list[Any]]] | None = None


async def clear_conversation(params: ClearConversationParams) -> None:
    """
    Execute session end hooks, wipe messages, clear caches, regenerate ids.

    Heavyweight AppState rewiring from the TypeScript implementation is
    represented via optional hooks; defaults preserve structure for tests.
    """
    if params.execute_session_end_hooks:
        await params.execute_session_end_hooks()

    params.set_messages(lambda _prev: [])

    if params.set_conversation_id:
        params.set_conversation_id(uuid4())

    preserved: set[str] = set()
    if params.get_app_state is not None:
        try:
            state = params.get_app_state()
            tasks = getattr(state, "tasks", {}) or {}
            for _tid, task in tasks.items():
                if getattr(task, "is_backgrounded", True) is False:
                    continue
                aid = getattr(task, "agent_id", None) or getattr(getattr(task, "identity", None), "agent_id", None)
                if aid is not None:
                    preserved.add(str(aid))
        except Exception:
            preserved = set()

    clear_session_caches(preserved)

    params.read_file_state.cache.clear()
    if params.discovered_skill_names is not None:
        params.discovered_skill_names.clear()
    if params.loaded_nested_memory_paths is not None:
        params.loaded_nested_memory_paths.clear()

    if params.process_session_start_hooks:
        hook_messages = await params.process_session_start_hooks()
        if hook_messages:
            params.set_messages(lambda _prev: list(hook_messages))


__all__ = ["ClearConversationParams", "clear_conversation"]
