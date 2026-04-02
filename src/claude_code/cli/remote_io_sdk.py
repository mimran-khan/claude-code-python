"""
Remote SDK I/O: transport-backed stdin + structured stdout.

Migrated from: cli/remoteIO.ts (condensed).
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator, Callable
from urllib.parse import urlparse, urlunparse

from .structured_io_sdk import StructuredIOSDK
from .transports import CCRClient, SSETransport, get_transport_for_url
from .transports.session_ingress_headers import (
    get_session_ingress_auth_token,
    is_env_truthy,
)

logger = logging.getLogger(__name__)


class RemoteIOSDK(StructuredIOSDK):
    """NDJSON over WebSocket/SSE with optional CCR v2 client."""

    def __init__(
        self,
        stream_url: str,
        initial_prompt: AsyncIterator[str] | None = None,
        replay_user_messages: bool = False,
        session_id: str | None = None,
    ) -> None:
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._closed = False

        async def chunk_source() -> AsyncIterator[str]:
            while True:
                item = await self._queue.get()
                if item is None:
                    break
                yield item

        super().__init__(chunk_source(), replay_user_messages=replay_user_messages)

        self._url = stream_url
        self._headers = _build_headers()
        self._refresh_headers: Callable[[], dict[str, str]] = _build_headers

        self._transport = get_transport_for_url(
            stream_url,
            headers=self._headers,
            session_id=session_id,
            refresh_headers=self._refresh_headers,
        )
        self._transport.set_on_data(self._on_data)
        self._transport.set_on_close(lambda *_: self._on_close())

        self._ccr: CCRClient | None = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as exc:
            raise RuntimeError(
                "RemoteIOSDK must be constructed with a running asyncio event loop.",
            ) from exc

        if is_env_truthy("CLAUDE_CODE_USE_CCR_V2"):
            if not isinstance(self._transport, SSETransport):
                raise RuntimeError("CCR v2 requires SSETransport")
            self._ccr = CCRClient(self._transport, _http_session_url(stream_url))
            loop.create_task(self._init_ccr())

        loop.create_task(self._transport.connect())

        if initial_prompt is not None:
            loop.create_task(self._pump_initial_prompt(initial_prompt))

    def _on_data(self, data: str) -> None:
        if not self._closed:
            self._queue.put_nowait(data)

    def _on_close(self) -> None:
        if not self._closed:
            self._queue.put_nowait(None)

    async def _pump_initial_prompt(self, initial_prompt: AsyncIterator[str]) -> None:
        async for chunk in initial_prompt:
            text = str(chunk).rstrip("\n") + "\n"
            self._queue.put_nowait(text)

    async def _init_ccr(self) -> None:
        if self._ccr:
            try:
                await self._ccr.initialize()
            except Exception as exc:
                logger.debug("CCR initialize failed: %s", exc)

    async def write(self, message: dict[str, object]) -> None:
        msg = dict(message)
        if self._ccr:
            await self._ccr.write_event(msg)
        else:
            await self._transport.write(msg)

    async def flush_internal_events(self) -> None:
        if self._ccr:
            await self._ccr.flush_internal_events()

    @property
    def internal_events_pending(self) -> int:
        return self._ccr.internal_events_pending if self._ccr else 0

    def close(self) -> None:
        self._closed = True
        self._transport.close()
        if self._ccr:
            self._ccr.close()


def _build_headers() -> dict[str, str]:
    h: dict[str, str] = {}
    tok = get_session_ingress_auth_token()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    er = os.environ.get("CLAUDE_CODE_ENVIRONMENT_RUNNER_VERSION")
    if er:
        h["x-environment-runner-version"] = er
    return h


def _http_session_url(stream_url: str) -> str:
    p = urlparse(stream_url)
    scheme = "https" if p.scheme == "wss" else "http" if p.scheme == "ws" else p.scheme
    return urlunparse((scheme, p.netloc, p.path, "", p.query, ""))
