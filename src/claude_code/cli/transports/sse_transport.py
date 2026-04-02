"""
SSE read + HTTP POST write transport (CCR v2).

Migrated from: cli/transports/SSETransport.ts
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

from .session_ingress_headers import (
    get_claude_code_user_agent,
    get_session_ingress_auth_headers,
)

logger = logging.getLogger(__name__)

StdoutMessage = dict[str, Any]

RECONNECT_BASE_DELAY_MS = 1000
RECONNECT_MAX_DELAY_MS = 30_000
RECONNECT_GIVE_UP_MS = 600_000
LIVENESS_TIMEOUT_MS = 45_000
PERMANENT_HTTP_CODES = {401, 403, 404}
POST_MAX_RETRIES = 10
POST_BASE_DELAY_MS = 500
POST_MAX_DELAY_MS = 8000


@dataclass
class SSEFrame:
    event: str | None = None
    id: str | None = None
    data: str | None = None


def parse_sse_frames(buffer: str) -> tuple[list[SSEFrame], str]:
    frames: list[SSEFrame] = []
    pos = 0
    while True:
        idx = buffer.find("\n\n", pos)
        if idx == -1:
            return frames, buffer[pos:]
        raw_frame = buffer[pos:idx]
        pos = idx + 2
        if not raw_frame.strip():
            continue
        frame = SSEFrame()
        is_comment = False
        for line in raw_frame.split("\n"):
            if line.startswith(":"):
                is_comment = True
                continue
            colon = line.find(":")
            if colon == -1:
                continue
            field = line[:colon]
            value = line[colon + 1 :]
            if value.startswith(" "):
                value = value[1:]
            if field == "event":
                frame.event = value
            elif field == "id":
                frame.id = value
            elif field == "data":
                frame.data = (frame.data + "\n" + value) if frame.data else value
        if frame.data or is_comment:
            frames.append(frame)


@dataclass
class StreamClientEvent:
    event_id: str
    sequence_num: int
    event_type: str
    source: str
    payload: dict[str, Any]
    created_at: str


class SSETransport:
    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        session_id: str | None = None,
        refresh_headers: Callable[[], dict[str, str]] | None = None,
        initial_sequence_num: int | None = None,
        get_auth_headers: Callable[[], dict[str, str]] | None = None,
    ) -> None:
        self._url = url
        self._headers = dict(headers or {})
        self._session_id = session_id
        self._refresh_headers = refresh_headers
        self._get_auth_headers = get_auth_headers or get_session_ingress_auth_headers
        self._state = "idle"
        self._on_data: Callable[[str], None] | None = None
        self._on_close: Callable[..., None] | None = None
        self._on_event: Callable[[StreamClientEvent], None] | None = None
        self._last_sequence_num = max(0, initial_sequence_num or 0)
        self._seen_sequence: set[int] = set()
        self._reconnect_attempts = 0
        self._reconnect_start: float | None = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._read_task: asyncio.Task[None] | None = None
        self._client: httpx.AsyncClient | None = None
        self._abort = asyncio.Event()
        self._post_url = _convert_sse_url_to_post_url(url)
        self._liveness_task: asyncio.Task[None] | None = None

    def get_last_sequence_num(self) -> int:
        return self._last_sequence_num

    def set_on_data(self, callback: Callable[[str], None]) -> None:
        self._on_data = callback

    def set_on_close(self, callback: Callable[..., None]) -> None:
        self._on_close = callback

    def set_on_event(self, callback: Callable[[StreamClientEvent], None]) -> None:
        self._on_event = callback

    async def connect(self) -> None:
        if self._state not in ("idle", "reconnecting"):
            return
        self._abort.clear()
        self._state = "reconnecting"
        self._read_task = asyncio.create_task(self._run_sse_loop())

    async def _run_sse_loop(self) -> None:
        try:
            while self._state not in ("closing", "closed"):
                if self._abort.is_set():
                    break
                ok = await self._open_stream_once()
                if not ok:
                    if self._state in ("closing", "closed"):
                        break
                    if not await self._schedule_reconnect():
                        break
                else:
                    self._reconnect_attempts = 0
                    self._reconnect_start = None
        except asyncio.CancelledError:
            pass
        finally:
            if self._state not in ("closing", "closed"):
                self._state = "closed"
                if self._on_close:
                    self._on_close()

    async def _open_stream_once(self) -> bool:
        from urllib.parse import parse_qsl, urlencode

        parts = urlparse(self._url)
        q = dict(parse_qsl(parts.query))
        if self._last_sequence_num > 0:
            q["from_sequence_num"] = str(self._last_sequence_num)
        new_query = urlencode(q)
        sse_url = urlunparse(parts._replace(query=new_query))

        auth = self._get_auth_headers()
        hdrs = {
            **self._headers,
            **auth,
            "Accept": "text/event-stream",
            "anthropic-version": "2023-06-01",
            "User-Agent": get_claude_code_user_agent(),
        }
        if auth.get("Cookie"):
            hdrs.pop("Authorization", None)
        if self._last_sequence_num > 0:
            hdrs["Last-Event-ID"] = str(self._last_sequence_num)

        self._client = httpx.AsyncClient(timeout=httpx.Timeout(None, read=600.0))
        try:
            async with self._client.stream("GET", sse_url, headers=hdrs) as resp:
                if resp.status_code in PERMANENT_HTTP_CODES:
                    self._state = "closed"
                    if self._on_close:
                        self._on_close(resp.status_code)
                    return False
                if resp.status_code < 200 or resp.status_code >= 300:
                    return False
                self._state = "connected"
                buffer = ""
                self._reset_liveness_timer()
                async for chunk in resp.aiter_text():
                    if self._abort.is_set():
                        break
                    buffer += chunk
                    frames, buffer = parse_sse_frames(buffer)
                    for fr in frames:
                        self._reset_liveness_timer()
                        if fr.id:
                            try:
                                seq = int(fr.id, 10)
                                if seq > self._last_sequence_num:
                                    self._last_sequence_num = seq
                                self._seen_sequence.add(seq)
                            except ValueError:
                                pass
                        if fr.event and fr.data:
                            self._handle_frame(fr.event, fr.data)
                return False
        except Exception:
            logger.exception("SSE stream error")
            return False
        finally:
            await self._client.aclose()
            self._client = None

    def _handle_frame(self, event_type: str, data: str) -> None:
        if event_type != "client_event":
            return
        try:
            ev = json.loads(data)
        except json.JSONDecodeError:
            return
        payload = ev.get("payload")
        if isinstance(payload, dict) and "type" in payload:
            line = json.dumps(payload, ensure_ascii=False) + "\n"
            if self._on_data:
                self._on_data(line)
        try:
            sce = StreamClientEvent(
                event_id=str(ev.get("event_id", "")),
                sequence_num=int(ev.get("sequence_num", 0)),
                event_type=str(ev.get("event_type", "")),
                source=str(ev.get("source", "")),
                payload=payload if isinstance(payload, dict) else {},
                created_at=str(ev.get("created_at", "")),
            )
            if self._on_event:
                self._on_event(sce)
        except (TypeError, ValueError):
            pass

    def _reset_liveness_timer(self) -> None:
        if self._liveness_task:
            self._liveness_task.cancel()
        self._liveness_task = asyncio.create_task(self._liveness_watch())

    async def _liveness_watch(self) -> None:
        try:
            await asyncio.sleep(LIVENESS_TIMEOUT_MS / 1000.0)
            self._abort.set()
        except asyncio.CancelledError:
            pass

    async def _schedule_reconnect(self) -> bool:
        import time

        now = time.monotonic()
        if self._reconnect_start is None:
            self._reconnect_start = now
        if now - self._reconnect_start > RECONNECT_GIVE_UP_MS / 1000.0:
            self._state = "closed"
            if self._on_close:
                self._on_close()
            return False
        if self._refresh_headers:
            self._headers.update(self._refresh_headers())
        self._reconnect_attempts += 1
        base = min(
            RECONNECT_BASE_DELAY_MS * (2 ** (self._reconnect_attempts - 1)),
            RECONNECT_MAX_DELAY_MS,
        )
        delay = max(0.0, base + base * 0.25 * (2 * random.random() - 1))
        await asyncio.sleep(delay / 1000.0)
        return True

    async def write(self, message: StdoutMessage) -> None:
        auth = self._get_auth_headers()
        if not auth:
            return
        headers = {
            **auth,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "User-Agent": get_claude_code_user_agent(),
        }
        for attempt in range(1, POST_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    r = await client.post(self._post_url, json=message, headers=headers)
                if 200 <= r.status_code < 300:
                    return
                if 400 <= r.status_code < 500 and r.status_code != 429:
                    return
            except httpx.HTTPError:
                pass
            if attempt == POST_MAX_RETRIES:
                return
            delay = min(POST_BASE_DELAY_MS * (2 ** (attempt - 1)), POST_MAX_DELAY_MS)
            await asyncio.sleep(delay / 1000.0)

    def is_connected_status(self) -> bool:
        return self._state == "connected"

    def is_closed_status(self) -> bool:
        return self._state == "closed"

    def close(self) -> None:
        self._state = "closing"
        self._abort.set()
        if self._read_task:
            self._read_task.cancel()
        if self._liveness_task:
            self._liveness_task.cancel()
        self._state = "closed"


def _convert_sse_url_to_post_url(sse_url: str) -> str:
    p = urlparse(sse_url)
    path = p.path
    if path.endswith("/stream"):
        path = path[: -len("/stream")]
    return urlunparse((p.scheme, p.netloc, path, "", "", ""))
