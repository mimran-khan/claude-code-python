"""
Remote session management.

Migrated from: remote/*.ts
"""

from .message_adapter import (
    adapt_remote_message,
    adapt_sdk_message,
)
from .permission_bridge import (
    RemotePermissionBridge,
)
from .session import (
    RemotePermissionResponse,
    RemoteSessionCallbacks,
    RemoteSessionConfig,
    RemoteSessionManager,
)
from .websocket import (
    SessionsWebSocket,
    SessionsWebSocketCallbacks,
)

__all__ = [
    # Session
    "RemoteSessionConfig",
    "RemoteSessionCallbacks",
    "RemoteSessionManager",
    "RemotePermissionResponse",
    # WebSocket
    "SessionsWebSocket",
    "SessionsWebSocketCallbacks",
    # Message adapter
    "adapt_sdk_message",
    "adapt_remote_message",
    # Permission bridge
    "RemotePermissionBridge",
]
