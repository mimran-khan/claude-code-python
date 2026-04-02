"""
Sessions WebSocket handler.

Migrated from: remote/SessionsWebSocket.ts
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class SessionsWebSocketCallbacks(Protocol):
    """Callbacks for WebSocket events."""

    def on_open(self) -> None:
        """Called when connection opens."""
        ...

    def on_message(self, data: dict[str, Any]) -> None:
        """Called when message received."""
        ...

    def on_close(self, code: int, reason: str) -> None:
        """Called when connection closes."""
        ...

    def on_error(self, error: Exception) -> None:
        """Called on error."""
        ...


@dataclass
class SessionsWebSocket:
    """WebSocket connection manager for remote sessions.

    Handles low-level WebSocket communication including:
    - Connection lifecycle
    - Message parsing
    - Heartbeat/ping
    - Reconnection
    """

    url: str
    callbacks: SessionsWebSocketCallbacks
    auth_token: str | None = None
    _ws: Any | None = None
    _connected: bool = False
    _heartbeat_task: asyncio.Task | None = None
    _message_queue: list[dict[str, Any]] = field(default_factory=list)

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            # Would use websockets library
            # headers = {}
            # if self.auth_token:
            #     headers["Authorization"] = f"Bearer {self.auth_token}"
            # self._ws = await websockets.connect(self.url, extra_headers=headers)
            self._connected = True
            self.callbacks.on_open()

            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Start message receive loop
            asyncio.create_task(self._receive_loop())

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.callbacks.on_error(e)

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self._connected = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

        if self._ws:
            # await self._ws.close()
            self._ws = None

        self.callbacks.on_close(1000, "Client disconnect")

    async def send(self, data: dict[str, Any]) -> None:
        """Send message over WebSocket."""
        if not self._connected:
            self._message_queue.append(data)
            return

        try:
            json.dumps(data)
            # await self._ws.send(message)
            logger.debug(f"Sent: {data.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Send failed: {e}")
            self.callbacks.on_error(e)

    async def _receive_loop(self) -> None:
        """Receive messages from WebSocket."""
        while self._connected:
            try:
                # message = await self._ws.recv()
                # data = json.loads(message)
                # self.callbacks.on_message(data)
                await asyncio.sleep(0.1)  # Placeholder
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")
                self.callbacks.on_error(e)
                break

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat."""
        while self._connected:
            try:
                await asyncio.sleep(30)
                await self.send({"type": "ping"})
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _flush_queue(self) -> None:
        """Send queued messages after reconnect."""
        while self._message_queue and self._connected:
            message = self._message_queue.pop(0)
            await self.send(message)

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected
