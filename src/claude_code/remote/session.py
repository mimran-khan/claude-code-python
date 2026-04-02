"""
Remote session manager.

Migrated from: remote/RemoteSessionManager.ts
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

logger = logging.getLogger(__name__)


@dataclass
class RemotePermissionResponseAllow:
    """Allow permission response."""

    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] = field(default_factory=dict)


@dataclass
class RemotePermissionResponseDeny:
    """Deny permission response."""

    behavior: Literal["deny"] = "deny"
    message: str = ""


RemotePermissionResponse = RemotePermissionResponseAllow | RemotePermissionResponseDeny


@dataclass
class RemoteSessionConfig:
    """Configuration for remote session."""

    session_id: str
    get_access_token: Callable[[], str]
    org_uuid: str
    has_initial_prompt: bool = False
    viewer_only: bool = False


class RemoteSessionCallbacks(Protocol):
    """Callbacks for remote session events."""

    def on_message(self, message: Any) -> None:
        """Called when SDK message received."""
        ...

    def on_permission_request(self, request: Any, request_id: str) -> None:
        """Called when permission request received."""
        ...

    def on_permission_cancelled(self, request_id: str, tool_use_id: str | None) -> None:
        """Called when permission request cancelled."""
        ...

    def on_connected(self) -> None:
        """Called when connected."""
        ...

    def on_disconnected(self) -> None:
        """Called when disconnected."""
        ...

    def on_reconnecting(self) -> None:
        """Called when reconnecting."""
        ...


@dataclass
class RemoteSessionManager:
    """Manages connection to remote Claude Code session.

    Handles WebSocket communication with the remote session server,
    including permission requests, message routing, and reconnection.
    """

    config: RemoteSessionConfig
    callbacks: RemoteSessionCallbacks
    _ws: Any | None = None
    _connected: bool = False
    _reconnecting: bool = False
    _should_reconnect: bool = True
    _pending_permissions: dict[str, Any] = field(default_factory=dict)

    async def connect(self) -> None:
        """Connect to the remote session."""
        try:
            # Would establish WebSocket connection
            self._connected = True
            logger.info(f"Connected to remote session {self.config.session_id}")
            self.callbacks.on_connected()
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            await self._handle_disconnect()

    async def disconnect(self) -> None:
        """Disconnect from remote session."""
        self._should_reconnect = False
        self._connected = False
        if self._ws:
            # await self._ws.close()
            self._ws = None
        self.callbacks.on_disconnected()

    async def send_permission_response(
        self,
        request_id: str,
        response: RemotePermissionResponse,
    ) -> None:
        """Send permission decision to remote session."""
        if isinstance(response, RemotePermissionResponseAllow):
            await self._send_event(
                {
                    "type": "permission_response",
                    "request_id": request_id,
                    "behavior": "allow",
                    "updated_input": response.updated_input,
                }
            )
        else:
            await self._send_event(
                {
                    "type": "permission_response",
                    "request_id": request_id,
                    "behavior": "deny",
                    "message": response.message,
                }
            )

    async def send_interrupt(self) -> None:
        """Send interrupt signal to remote session."""
        if self.config.viewer_only:
            return  # Viewers can't interrupt
        await self._send_event({"type": "interrupt"})

    async def send_user_input(self, input_text: str) -> None:
        """Send user input to remote session."""
        await self._send_event(
            {
                "type": "user_input",
                "content": input_text,
            }
        )

    async def _send_event(self, event: dict[str, Any]) -> None:
        """Send event to remote session."""
        if not self._connected:
            logger.warning("Cannot send event - not connected")
            return
        # Would send via WebSocket
        logger.debug(f"Sent event: {event.get('type', 'unknown')}")

    async def _handle_disconnect(self) -> None:
        """Handle disconnection."""
        self._connected = False
        if self._should_reconnect and not self.config.viewer_only:
            self._reconnecting = True
            self.callbacks.on_reconnecting()
            await self._attempt_reconnect()
        else:
            self.callbacks.on_disconnected()

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        backoff = 1.0
        max_backoff = 60.0

        while self._should_reconnect and not self._connected:
            try:
                await asyncio.sleep(backoff)
                await self.connect()
                if self._connected:
                    self._reconnecting = False
                    return
            except Exception as e:
                logger.warning(f"Reconnect failed: {e}")
                backoff = min(backoff * 2, max_backoff)

        self._reconnecting = False
        self.callbacks.on_disconnected()

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected

    @property
    def is_reconnecting(self) -> bool:
        """Check if reconnecting."""
        return self._reconnecting
