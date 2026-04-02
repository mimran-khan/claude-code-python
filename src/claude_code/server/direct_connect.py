"""
Direct connect session manager.

Migrated from: server/directConnectManager.ts
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass
class DirectConnectConfig:
    """Configuration for direct connect session."""

    server_url: str
    session_id: str
    ws_url: str
    auth_token: str | None = None


class DirectConnectCallbacks(Protocol):
    """Callbacks for direct connect events."""

    def on_message(self, message: Any) -> None:
        """Called when SDK message received."""
        ...

    def on_permission_request(self, request: Any, request_id: str) -> None:
        """Called when permission request received."""
        ...

    def on_connected(self) -> None:
        """Called when connected."""
        ...

    def on_disconnected(self) -> None:
        """Called when disconnected."""
        ...

    def on_error(self, error: Exception) -> None:
        """Called on error."""
        ...


@dataclass
class DirectConnectSessionManager:
    """Manages WebSocket connection for direct connect sessions.

    In full implementation, would handle:
    - WebSocket connection lifecycle
    - Message parsing and routing
    - Permission request handling
    - Reconnection logic
    """

    config: DirectConnectConfig
    callbacks: DirectConnectCallbacks
    _ws: Any | None = None
    _connected: bool = False
    _reconnect_task: asyncio.Task | None = None
    _pending_requests: dict[str, Any] = field(default_factory=dict)

    async def connect(self) -> None:
        """Connect to the WebSocket server.

        Note: Full implementation would use websockets library.
        """
        try:
            # Would connect via websockets
            # self._ws = await websockets.connect(self.config.ws_url, ...)
            self._connected = True
            logger.info(f"Connected to {self.config.ws_url}")
            self.callbacks.on_connected()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.callbacks.on_error(e)

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        self._connected = False
        if self._ws:
            # await self._ws.close()
            self._ws = None
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
        self.callbacks.on_disconnected()

    async def send_message(self, message: dict[str, Any]) -> None:
        """Send a message to the server."""
        if not self._connected or not self._ws:
            raise RuntimeError("Not connected")
        # await self._ws.send(json.dumps(message))
        logger.debug(f"Sent message: {message.get('type', 'unknown')}")

    async def respond_to_permission(
        self,
        request_id: str,
        response: dict[str, Any],
    ) -> None:
        """Send permission response."""
        await self.send_message(
            {
                "type": "permission_response",
                "request_id": request_id,
                **response,
            }
        )

    def _handle_message(self, raw_data: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            lines = raw_data.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if not isinstance(data, dict) or "type" not in data:
                    continue

                msg_type = data.get("type")

                if msg_type == "permission_request":
                    request_id = data.get("request_id", "")
                    self.callbacks.on_permission_request(data, request_id)
                elif msg_type not in (
                    "control_request",
                    "control_response",
                    "control_cancel_request",
                ):
                    self.callbacks.on_message(data)

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected
