"""
DirectConnect WebSocket session façade (remote ``claude`` server).

Migrated from: hooks/useDirectConnect.ts — state + callback wiring surface for Python host.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

TContent = TypeVar("TContent")


@dataclass
class DirectConnectCallbacks:
    on_message: Callable[[Any], None] | None = None
    on_permission_request: Callable[[Any, str], None] | None = None
    on_connected: Callable[[], None] | None = None
    on_disconnected: Callable[[], None] | None = None
    on_error: Callable[[BaseException], None] | None = None


@dataclass
class DirectConnectSessionState(Generic[TContent]):
    """Host-owned manager; inject send/interrupt/disconnect callables from server port."""

    is_remote_mode: bool = False
    has_received_init: bool = False
    is_connected: bool = False
    send_message_fn: Callable[[TContent], Awaitable[bool]] | None = field(default=None, repr=False)
    send_interrupt_fn: Callable[[], None] | None = field(default=None, repr=False)
    disconnect_fn: Callable[[], None] | None = field(default=None, repr=False)

    async def send_message(self, content: TContent) -> bool:
        if self.send_message_fn is None:
            return False
        return await self.send_message_fn(content)

    def cancel_request(self) -> None:
        if self.send_interrupt_fn is not None:
            self.send_interrupt_fn()

    def disconnect(self) -> None:
        if self.disconnect_fn is not None:
            self.disconnect_fn()
        self.is_connected = False
