"""JWT helpers and token refresh scheduler (ported from bridge/jwtUtils.ts)."""

from __future__ import annotations

import asyncio
import base64
import inspect
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, cast

logger = logging.getLogger(__name__)

TOKEN_REFRESH_BUFFER_MS = 5 * 60 * 1000
FALLBACK_REFRESH_INTERVAL_MS = 30 * 60 * 1000
MAX_REFRESH_FAILURES = 3
REFRESH_RETRY_DELAY_MS = 60_000


def decode_jwt_payload(token: str) -> Any | None:
    jwt = token[len("sk-ant-si-") :] if token.startswith("sk-ant-si-") else token
    parts = jwt.split(".")
    if len(parts) != 3 or not parts[1]:
        return None
    try:
        seg = parts[1]
        pad = 4 - len(seg) % 4
        if pad != 4:
            seg += "=" * pad
        raw = base64.urlsafe_b64decode(seg.encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def decode_jwt_expiry(token: str) -> int | None:
    payload = decode_jwt_payload(token)
    if isinstance(payload, dict) and isinstance(payload.get("exp"), (int, float)):
        return int(payload["exp"])
    return None


def _format_duration(ms: float) -> str:
    if ms < 60_000:
        return f"{round(ms / 1000)}s"
    m = int(ms // 60_000)
    s = round((ms % 60_000) / 1000)
    return f"{m}m {s}s" if s > 0 else f"{m}m"


class _TokenRefreshScheduler:
    def __init__(
        self,
        get_access_token: Callable[[], str | None | Awaitable[str | None]],
        on_refresh: Callable[[str, str], None],
        label: str,
        refresh_buffer_ms: int,
    ) -> None:
        self._get_access_token = get_access_token
        self._on_refresh = on_refresh
        self._label = label
        self._refresh_buffer_ms = refresh_buffer_ms
        self._timers: dict[str, asyncio.Task[None]] = {}
        self._failure_counts: dict[str, int] = {}
        self._generations: dict[str, int] = {}

    def _next_gen(self, session_id: str) -> int:
        self._generations[session_id] = self._generations.get(session_id, 0) + 1
        return self._generations[session_id]

    async def _resolve_token(self) -> str | None:
        t = self._get_access_token()
        if inspect.isawaitable(t):
            return cast(str | None, await t)
        return cast(str | None, t)

    def _cancel_timer(self, session_id: str) -> None:
        task = self._timers.pop(session_id, None)
        if task is not None and not task.done():
            task.cancel()

    async def _do_refresh(self, session_id: str, gen: int) -> None:
        try:
            oauth_token = await self._resolve_token()
        except Exception as e:
            logger.debug("[%s:token] getAccessToken threw: %s", self._label, e)
            oauth_token = None

        if self._generations.get(session_id) != gen:
            return

        if not oauth_token:
            failures = self._failure_counts.get(session_id, 0) + 1
            self._failure_counts[session_id] = failures
            logger.debug(
                "[%s:token] No OAuth token (failure %s/%s)",
                self._label,
                failures,
                MAX_REFRESH_FAILURES,
            )
            if failures < MAX_REFRESH_FAILURES:

                async def retry() -> None:
                    await asyncio.sleep(REFRESH_RETRY_DELAY_MS / 1000)
                    await self._do_refresh(session_id, gen)

                self._timers[session_id] = asyncio.create_task(retry())
            return

        self._failure_counts.pop(session_id, None)
        self._on_refresh(session_id, oauth_token)

        async def follow_up() -> None:
            await asyncio.sleep(FALLBACK_REFRESH_INTERVAL_MS / 1000)
            await self._do_refresh(session_id, gen)

        self._timers[session_id] = asyncio.create_task(follow_up())

    def schedule(self, session_id: str, token: str) -> None:
        expiry = decode_jwt_expiry(token)
        if expiry is None:
            logger.debug(
                "[%s:token] Could not decode JWT expiry sessionId=%s",
                self._label,
                session_id,
            )
            return
        self._cancel_timer(session_id)
        gen = self._next_gen(session_id)
        delay_ms = expiry * 1000 - time.time() * 1000 - self._refresh_buffer_ms
        expiry_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(expiry))

        async def run() -> None:
            if delay_ms <= 0:
                logger.debug(
                    "[%s:token] Token expires=%s past or within buffer, refresh now",
                    self._label,
                    expiry_iso,
                )
                await self._do_refresh(session_id, gen)
            else:
                logger.debug(
                    "[%s:token] Scheduled refresh in %s (expires=%s)",
                    self._label,
                    _format_duration(delay_ms),
                    expiry_iso,
                )
                await asyncio.sleep(delay_ms / 1000)
                await self._do_refresh(session_id, gen)

        self._timers[session_id] = asyncio.create_task(run())

    def schedule_from_expires_in(self, session_id: str, expires_in_seconds: int) -> None:
        self._cancel_timer(session_id)
        gen = self._next_gen(session_id)
        delay_ms = max(expires_in_seconds * 1000 - self._refresh_buffer_ms, 30_000)

        async def run() -> None:
            await asyncio.sleep(delay_ms / 1000)
            await self._do_refresh(session_id, gen)

        self._timers[session_id] = asyncio.create_task(run())

    def cancel(self, session_id: str) -> None:
        self._next_gen(session_id)
        self._cancel_timer(session_id)
        self._failure_counts.pop(session_id, None)

    def cancel_all(self) -> None:
        for sid in list(self._generations.keys()):
            self._next_gen(sid)
        for t in self._timers.values():
            if not t.done():
                t.cancel()
        self._timers.clear()
        self._failure_counts.clear()


def create_token_refresh_scheduler(
    *,
    get_access_token: Callable[[], str | None | Awaitable[str | None]],
    on_refresh: Callable[[str, str], None],
    label: str,
    refresh_buffer_ms: int = TOKEN_REFRESH_BUFFER_MS,
) -> dict[str, Any]:
    s = _TokenRefreshScheduler(get_access_token, on_refresh, label, refresh_buffer_ms)
    return {
        "schedule": s.schedule,
        "schedule_from_expires_in": s.schedule_from_expires_in,
        "cancel": s.cancel,
        "cancel_all": s.cancel_all,
    }
