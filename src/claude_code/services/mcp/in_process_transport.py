"""In-process MCP transport pair (same-process client/server).

Migrated from: services/mcp/InProcessTransport.ts
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any


class InProcessTransport:
    """Bidirectional linked transports; send on one delivers to on_message on peer."""

    def __init__(self) -> None:
        self._peer: InProcessTransport | None = None
        self._closed = False
        self.on_close: Callable[[], None] | None = None
        self.on_error: Callable[[Exception], None] | None = None
        self.on_message: Callable[[dict[str, Any]], None] | None = None

    def _set_peer(self, peer: InProcessTransport) -> None:
        self._peer = peer

    async def start(self) -> None:
        return

    async def send(self, message: dict[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("Transport is closed")
        peer = self._peer
        if peer is None or peer.on_message is None:
            return

        async def _deliver() -> None:
            peer.on_message(message)

        asyncio.create_task(_deliver())

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._peer and not self._peer._closed:
            self._peer._closed = True
        if self.on_close:
            self.on_close()
        if self._peer and self._peer.on_close:
            self._peer.on_close()


def create_linked_transports() -> tuple[InProcessTransport, InProcessTransport]:
    a = InProcessTransport()
    b = InProcessTransport()
    a._set_peer(b)
    b._set_peer(a)
    return (a, b)
