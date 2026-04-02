"""
Hybrid transport: WebSocket reads + HTTP POST writes.

Migrated from: cli/transports/HybridTransport.ts
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from urllib.parse import urlparse, urlunparse

import httpx

from .serial_batch_event_uploader import SerialBatchEventUploader, SerialBatchEventUploaderConfig
from .session_ingress_headers import get_session_ingress_auth_token
from .transport_base import StdoutMessage
from .websocket_transport import WebSocketTransport, WebSocketTransportOptions

logger = logging.getLogger(__name__)

BATCH_FLUSH_INTERVAL_MS = 100
POST_TIMEOUT_S = 15.0
CLOSE_GRACE_S = 3.0


def _convert_ws_url_to_post_url(ws_url: str) -> str:
    p = urlparse(ws_url)
    scheme = "https" if p.scheme in ("wss", "https") else "http"
    path = p.path.replace("/ws/", "/session/", 1)
    if not path.endswith("/events"):
        path = path.rstrip("/") + "/events"
    return urlunparse((scheme, p.netloc, path, "", p.query, ""))


class HybridTransport(WebSocketTransport):
    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        session_id: str | None = None,
        refresh_headers: Callable[[], dict[str, str]] | None = None,
        options: WebSocketTransportOptions | None = None,
    ) -> None:
        super().__init__(url, headers, session_id, refresh_headers, options)
        self._post_url = _convert_ws_url_to_post_url(url)
        self._stream_buffer: list[StdoutMessage] = []
        self._stream_timer: asyncio.Handle | None = None
        cfg = SerialBatchEventUploaderConfig[StdoutMessage](
            max_batch_size=500,
            max_queue_size=100_000,
            base_delay_ms=500,
            max_delay_ms=8000,
            jitter_ms=1000,
            send=self._post_once,
        )
        self._uploader = SerialBatchEventUploader(cfg)

    async def _post_once(self, events: list[StdoutMessage]) -> None:
        token = get_session_ingress_auth_token()
        if not token:
            return
        hdrs = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=POST_TIMEOUT_S) as client:
            r = await client.post(self._post_url, json={"events": events}, headers=hdrs)
        if 200 <= r.status_code < 300:
            return
        if 400 <= r.status_code < 500 and r.status_code != 429:
            return
        raise RuntimeError(f"POST failed {r.status_code}")

    def _take_stream_events(self) -> list[StdoutMessage]:
        buf = self._stream_buffer
        self._stream_buffer = []
        if self._stream_timer:
            self._stream_timer.cancel()
            self._stream_timer = None
        return buf

    def _flush_stream_events(self) -> None:
        self._stream_timer = None
        batch = self._take_stream_events()
        if batch:
            asyncio.create_task(self._uploader.enqueue(batch))

    async def write(self, message: StdoutMessage) -> None:
        if message.get("type") == "stream_event":
            self._stream_buffer.append(message)
            if self._stream_timer is None:
                loop = asyncio.get_running_loop()
                self._stream_timer = loop.call_later(
                    BATCH_FLUSH_INTERVAL_MS / 1000.0,
                    self._flush_stream_events,
                )
            return
        await self._uploader.enqueue([*self._take_stream_events(), message])
        await self._uploader.flush()

    async def write_batch(self, messages: list[StdoutMessage]) -> None:
        await self._uploader.enqueue([*self._take_stream_events(), *messages])
        await self._uploader.flush()

    async def flush(self) -> None:
        batch = self._take_stream_events()
        if batch:
            await self._uploader.enqueue(batch)
        await self._uploader.flush()

    def close(self) -> None:
        if self._stream_timer:
            self._stream_timer.cancel()
            self._stream_timer = None
        self._stream_buffer.clear()

        async def _grace() -> None:
            try:
                await asyncio.wait_for(self._uploader.flush(), timeout=CLOSE_GRACE_S)
            except (TimeoutError, Exception) as exc:
                logger.debug("hybrid close flush: %s", exc)
            self._uploader.close()

        try:
            asyncio.get_running_loop().create_task(_grace())
        except RuntimeError:
            self._uploader.close()
        super().close()
