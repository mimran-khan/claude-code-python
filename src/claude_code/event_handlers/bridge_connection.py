"""
REPL bridge connection lifecycle (ported from hooks/useReplBridge.tsx).

Holds connection state, consecutive failure accounting, and init/teardown entry points.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from claude_code.bridge.init_repl_bridge import init_repl_bridge
from claude_code.bridge.repl_bridge import ReplBridgeHandle

MAX_CONSECUTIVE_INIT_FAILURES = 3


InitOptionsFactory = Callable[[], dict[str, Any]]


@dataclass
class BridgeConnectionHandler:
    """
    Manages a single Repl bridge handle with session-local fuse semantics
    matching the React hook (stop retrying after repeated init failures).
    """

    consecutive_failures: int = 0
    _handle: ReplBridgeHandle | None = field(default=None, repr=False)
    _teardown_task: asyncio.Task[None] | None = field(default=None, repr=False)
    _build_options: InitOptionsFactory | None = field(default=None, repr=False)

    @property
    def handle(self) -> ReplBridgeHandle | None:
        return self._handle

    @property
    def fuse_blown(self) -> bool:
        return self.consecutive_failures >= MAX_CONSECUTIVE_INIT_FAILURES

    def set_options_factory(self, factory: InitOptionsFactory | None) -> None:
        self._build_options = factory

    async def init_bridge(self) -> ReplBridgeHandle | None:
        if self.fuse_blown:
            return None
        opts: dict[str, Any] = {}
        if self._build_options:
            opts = self._build_options()
        try:
            handle = await init_repl_bridge(opts)
        except Exception:
            self.consecutive_failures += 1
            raise
        if handle is None:
            self.consecutive_failures += 1
            return None
        self.consecutive_failures = 0
        self._handle = handle
        return handle

    def reset_fuse(self) -> None:
        self.consecutive_failures = 0

    async def teardown(
        self,
        async_teardown: Callable[[ReplBridgeHandle], Awaitable[None]] | None = None,
    ) -> None:
        if self._teardown_task is not None:
            await self._teardown_task
            self._teardown_task = None
        h = self._handle
        self._handle = None
        if h is not None and async_teardown is not None:
            await async_teardown(h)
