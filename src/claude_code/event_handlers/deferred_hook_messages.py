"""
Defer SessionStart hook messages until after first paint / before first API call.

Migrated from: hooks/useDeferredHookMessages.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeferredHookMessagesState:
    """
    Holds pending hook messages. Call ``ensure_flushed_before_submit`` before
    the first model request so the transcript includes hook context.
    """

    _pending: Awaitable[list[Any]] | None = None
    _resolved: bool = True
    _prepend: Callable[[Sequence[Any]], None] | None = field(default=None, repr=False)

    def set_prepend_handler(self, fn: Callable[[Sequence[Any]], None]) -> None:
        self._prepend = fn

    def arm(self, messages_coro: Awaitable[list[Any]] | None) -> None:
        if messages_coro is None:
            self._pending = None
            self._resolved = True
        else:
            self._pending = messages_coro
            self._resolved = False

    async def ensure_flushed_before_submit(self) -> None:
        if self._resolved or self._pending is None:
            return
        msgs = await self._pending
        if self._resolved:
            return
        self._resolved = True
        self._pending = None
        if msgs and self._prepend is not None:
            self._prepend(msgs)

    def apply_resolved_messages(self, msgs: Sequence[Any]) -> None:
        """Apply messages after async effect resolved (non-blocking path)."""
        self._resolved = True
        self._pending = None
        if msgs and self._prepend is not None:
            self._prepend(msgs)
