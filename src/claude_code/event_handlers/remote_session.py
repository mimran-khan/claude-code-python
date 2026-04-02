"""
Remote CCR session bridge (WebSocket + permission queue).

Migrated from: hooks/useRemoteSession.ts

Wire :class:`claude_code.remote.RemoteSessionManager` (or successor) with these
lifecycle hooks; this module documents the callback surface only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


class RemoteSessionCallbacks(Protocol):
    on_message: Callable[[Any], None]
    on_permission_request: Callable[[Any, str], None]
    on_permission_cancelled: Callable[[str, str | None], None]
    on_connected: Callable[[], None]
    on_reconnecting: Callable[[], None]
    on_disconnected: Callable[[], None]
    on_error: Callable[[BaseException], None]


@dataclass
class RemoteSessionHandles:
    send_message: Callable[..., Any]
    cancel_request: Callable[[], None]
    disconnect: Callable[[], None]
