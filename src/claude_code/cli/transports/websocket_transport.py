"""
WebSocket transport for CLI SDK remote mode.

Migrated from: cli/transports/WebSocketTransport.ts (simplified; asyncio + websockets).
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from collections.abc import Callable
from dataclasses import dataclass

import websockets
from websockets import ClientConnection

from .session_ingress_headers import get_claude_code_user_agent
from .transport_base import StdoutMessage

logger = logging.getLogger(__name__)

DEFAULT_MAX_BUFFER = 1000
DEFAULT_BASE_RECONNECT_DELAY = 1.0
DEFAULT_MAX_RECONNECT_DELAY = 30.0
DEFAULT_RECONNECT_GIVE_UP_S = 600.0


@dataclass
class WebSocketTransportOptions:
    auto_reconnect: bool = True
    is_bridge: bool = False


class WebSocketTransport:
    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        session_id: str | None = None,
        refresh_headers: Callable[[], dict[str, str]] | None = None,
        options: WebSocketTransportOptions | None = None,
    ) -> None:
        self._url = url
        self._headers = dict(headers or {})
        self._session_id = session_id
        self._refresh_headers = refresh_headers
        self._opts = options or WebSocketTransportOptions()
        self._state = "idle"
        self._ws: ClientConnection | None = None
        self._on_data: Callable[[str], None] | None = None
        self._on_close: Callable[..., None] | None = None
        self._on_connect: Callable[[], None] | None = None
        self._reconnect_attempts = 0
        self._reconnect_start: float | None = None
        self._recv_task: asyncio.Task[None] | None = None
        self._message_buffer: list[StdoutMessage] = []
        self._last_sent_id: str | None = None

    def set_on_data(self, callback: Callable[[str], None]) -> None:
        self._on_data = callback

    def set_on_close(self, callback: Callable[..., None]) -> None:
        self._on_close = callback

    def set_on_connect(self, callback: Callable[[], None]) -> None:
        self._on_connect = callback

    async def connect(self) -> None:
        if self._state not in ("idle", "reconnecting"):
            return
        self._state = "reconnecting"
        extra_headers = [
            (k, v)
            for k, v in {
                **self._headers,
                "User-Agent": get_claude_code_user_agent(),
            }.items()
        ]
        try:
            self._ws = await websockets.connect(
                self._url,
                additional_headers=extra_headers,
                max_size=None,
            )
            self._state = "connected"
            self._reconnect_attempts = 0
            self._reconnect_start = None
            if self._on_connect:
                self._on_connect()
            self._recv_task = asyncio.create_task(self._recv_loop())
        except Exception:
            logger.exception("WebSocket connect failed")
            await self._handle_disconnect()

    async def _recv_loop(self) -> None:
        assert self._ws is not None
        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    message = message.decode("utf-8", errors="replace")
                if self._on_data:
                    self._on_data(message if message.endswith("\n") else message + "\n")
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("WebSocket recv error")
        finally:
            await self._handle_disconnect()

    async def _handle_disconnect(self) -> None:
        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()
        self._ws = None
        if self._state == "closing" or self._state == "closed":
            return
        if not self._opts.auto_reconnect:
            self._state = "closed"
            if self._on_close:
                self._on_close()
            return
        import time

        now = time.monotonic()
        if self._reconnect_start is None:
            self._reconnect_start = now
        if now - self._reconnect_start > DEFAULT_RECONNECT_GIVE_UP_S:
            self._state = "closed"
            if self._on_close:
                self._on_close()
            return
        if self._refresh_headers:
            self._headers.update(self._refresh_headers())
        self._reconnect_attempts += 1
        base = min(
            DEFAULT_BASE_RECONNECT_DELAY * (2 ** (self._reconnect_attempts - 1)),
            DEFAULT_MAX_RECONNECT_DELAY,
        )
        delay = max(0.0, base + base * 0.25 * (2 * random.random() - 1))
        await asyncio.sleep(delay)
        self._state = "reconnecting"
        await self.connect()

    async def write(self, message: StdoutMessage) -> None:
        uid = message.get("uuid")
        if isinstance(uid, str):
            self._last_sent_id = uid
            self._message_buffer.append(message)
            if len(self._message_buffer) > DEFAULT_MAX_BUFFER:
                self._message_buffer.pop(0)
        if self._state != "connected" or not self._ws:
            return
        line = json.dumps(message, ensure_ascii=False) + "\n"
        await self._ws.send(line)

    def close(self) -> None:
        self._state = "closing"
        if self._recv_task:
            self._recv_task.cancel()
        if self._ws:
            ws = self._ws
            try:
                asyncio.get_running_loop().create_task(ws.close())
            except RuntimeError:
                logger.debug(
                    "WebSocket close: no running event loop; async close not scheduled",
                )
        self._ws = None
        self._state = "closed"

    def is_connected_status(self) -> bool:
        return self._state == "connected"

    def is_closed_status(self) -> bool:
        return self._state == "closed"

    def get_state_label(self) -> str:
        return self._state
