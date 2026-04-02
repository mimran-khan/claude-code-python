"""
CCR v2 worker client (SSE transport + HTTP worker API).

Migrated from: cli/transports/ccrClient.ts (condensed; same protocol surface).
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from .serial_batch_event_uploader import (
    RetryableError,
    SerialBatchEventUploader,
    SerialBatchEventUploaderConfig,
)
from .session_ingress_headers import get_claude_code_user_agent, get_session_ingress_auth_token
from .sse_transport import SSETransport, StreamClientEvent
from .transport_base import StdoutMessage
from .worker_state_uploader import WorkerStateUploader, WorkerStateUploaderConfig

logger = logging.getLogger(__name__)

CCRInitFailReason = Literal["no_auth_headers", "missing_epoch", "worker_register_failed"]


class CCRInitError(Exception):
    def __init__(self, reason: CCRInitFailReason) -> None:
        super().__init__(f"CCRClient init failed: {reason}")
        self.reason = reason


def decode_jwt_expiry(token: str) -> int | None:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        pad = "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
        exp = payload.get("exp")
        return int(exp) if isinstance(exp, (int, float)) else None
    except (ValueError, json.JSONDecodeError, TypeError):
        return None


@dataclass
class StreamAccumulatorState:
    by_message: dict[str, list[list[str]]]
    scope_to_message: dict[str, str]


def create_stream_accumulator() -> StreamAccumulatorState:
    return StreamAccumulatorState(by_message={}, scope_to_message={})


def _scope_key(session_id: str, parent_tool_use_id: str | None) -> str:
    return f"{session_id}:{parent_tool_use_id or ''}"


def accumulate_stream_events(
    buffer: list[dict[str, Any]],
    state: StreamAccumulatorState,
) -> list[dict[str, Any]]:
    """Coalesce text_delta stream_events (TS accumulateStreamEvents parity)."""
    out: list[dict[str, Any]] = []
    touched: dict[int, dict[str, Any]] = {}
    for msg in buffer:
        ev = msg.get("event")
        if not isinstance(ev, dict):
            out.append(msg)
            continue
        et = ev.get("type")
        if et == "message_start":
            mid = ev.get("message", {}).get("id") if isinstance(ev.get("message"), dict) else None
            if isinstance(mid, str):
                sk = _scope_key(str(msg.get("session_id", "")), msg.get("parent_tool_use_id"))  # type: ignore[arg-type]
                prev = state.scope_to_message.get(sk)
                if prev:
                    state.by_message.pop(prev, None)
                state.scope_to_message[sk] = mid
                state.by_message[mid] = []
            out.append(msg)
        elif et == "content_block_delta":
            delta = ev.get("delta")
            if not isinstance(delta, dict) or delta.get("type") != "text_delta":
                out.append(msg)
                continue
            text = delta.get("text", "")
            if not isinstance(text, str):
                out.append(msg)
                continue
            sk = _scope_key(str(msg.get("session_id", "")), msg.get("parent_tool_use_id"))  # type: ignore[arg-type]
            message_id = state.scope_to_message.get(sk)
            blocks = state.by_message.get(message_id) if message_id else None
            if blocks is None:
                out.append(msg)
                continue
            idx = int(ev.get("index", 0))
            while len(blocks) <= idx:
                blocks.append([])
            chunks = blocks[idx]
            chunks.append(text)
            snap_text = "".join(chunks)
            id_chunks = id(chunks)
            if id_chunks in touched:
                existing = touched[id_chunks]
                existing["event"]["delta"]["text"] = snap_text
            else:
                snapshot = {
                    "type": "stream_event",
                    "uuid": msg.get("uuid"),
                    "session_id": msg.get("session_id"),
                    "parent_tool_use_id": msg.get("parent_tool_use_id"),
                    "event": {
                        "type": "content_block_delta",
                        "index": idx,
                        "delta": {"type": "text_delta", "text": snap_text},
                    },
                }
                touched[id_chunks] = snapshot
                out.append(snapshot)
        else:
            out.append(msg)
    return out


def clear_stream_accumulator_for_message(
    state: StreamAccumulatorState,
    assistant: dict[str, Any],
) -> None:
    msg = assistant.get("message")
    mid = msg.get("id") if isinstance(msg, dict) else None
    if isinstance(mid, str):
        state.by_message.pop(mid, None)
    sk = _scope_key(
        str(assistant.get("session_id", "")),
        assistant.get("parent_tool_use_id"),  # type: ignore[arg-type]
    )
    if state.scope_to_message.get(sk) == mid:
        state.scope_to_message.pop(sk, None)


@dataclass
class InternalEvent:
    event_id: str
    event_type: str
    payload: dict[str, Any]
    is_compaction: bool
    created_at: str
    event_metadata: dict[str, Any] | None = None
    agent_id: str | None = None


class CCRClient:
    def __init__(
        self,
        transport: SSETransport,
        session_url: str,
        opts: dict[str, Any] | None = None,
    ) -> None:
        opts = opts or {}
        self._transport = transport
        self._on_epoch_mismatch: Callable[[], None] = opts.get(
            "on_epoch_mismatch",
            lambda: sys.exit(1),
        )
        self._get_auth_headers: Callable[[], dict[str, str]] | None = opts.get("get_auth_headers")
        self._worker_epoch = 0
        self._session_base = _session_base_url(session_url)
        self._session_id = self._session_base.rstrip("/").split("/")[-1]
        self._closed = False
        self._stream_buf: list[dict[str, Any]] = []
        self._stream_timer: asyncio.Handle | None = None
        self._accumulator = create_stream_accumulator()

        self._worker_state = WorkerStateUploader(
            WorkerStateUploaderConfig(
                send=self._put_worker,
                base_delay_ms=500,
                max_delay_ms=30_000,
                jitter_ms=500,
            )
        )

        async def send_events(batch: list[dict[str, Any]]) -> None:
            ok = await self._request(
                "post",
                "/worker/events",
                {"worker_epoch": self._worker_epoch, "events": batch},
            )
            if not ok:
                raise RetryableError("client events failed")

        self._event_uploader = SerialBatchEventUploader(
            SerialBatchEventUploaderConfig(
                max_batch_size=100,
                max_queue_size=100_000,
                max_batch_bytes=10 * 1024 * 1024,
                send=send_events,
                base_delay_ms=500,
                max_delay_ms=30_000,
                jitter_ms=500,
            )
        )

        async def send_internal(batch: list[dict[str, Any]]) -> None:
            ok = await self._request(
                "post",
                "/worker/internal-events",
                {"worker_epoch": self._worker_epoch, "events": batch},
            )
            if not ok:
                raise RetryableError("internal events failed")

        self._internal_uploader = SerialBatchEventUploader(
            SerialBatchEventUploaderConfig(
                max_batch_size=100,
                max_queue_size=200,
                max_batch_bytes=10 * 1024 * 1024,
                send=send_internal,
                base_delay_ms=500,
                max_delay_ms=30_000,
                jitter_ms=500,
            )
        )

        async def send_delivery_updates(batch: list[dict[str, str]]) -> None:
            ok = await self._request(
                "post",
                "/worker/events/delivery",
                {
                    "worker_epoch": self._worker_epoch,
                    "updates": [{"event_id": b["event_id"], "status": b["status"]} for b in batch],
                },
            )
            if not ok:
                raise RetryableError("delivery failed")

        self._delivery_uploader = SerialBatchEventUploader(
            SerialBatchEventUploaderConfig(
                max_batch_size=64,
                max_queue_size=64,
                send=send_delivery_updates,
                base_delay_ms=500,
                max_delay_ms=30_000,
                jitter_ms=500,
            )
        )

        transport.set_on_event(self._on_sse_event)

    def _auth_headers(self) -> dict[str, str]:
        if self._get_auth_headers:
            return self._get_auth_headers()
        tok = get_session_ingress_auth_token()
        return {"Authorization": f"Bearer {tok}"} if tok else {}

    def _on_sse_event(self, event: StreamClientEvent) -> None:
        asyncio.create_task(self._enqueue_delivery(event.event_id, "received"))

    async def _enqueue_delivery(
        self,
        event_id: str,
        status: Literal["received", "processing", "processed"],
    ) -> None:
        await self._delivery_uploader.enqueue([{"event_id": event_id, "status": status}])

    async def _put_worker(self, body: dict[str, Any]) -> bool:
        payload = {"worker_epoch": self._worker_epoch, **body}
        return await self._request("put", "/worker", payload)

    async def _request(self, method: str, path: str, body: dict[str, Any]) -> bool:
        auth = self._auth_headers()
        if not auth:
            return False
        url = f"{self._session_base}{path}"
        headers = {
            **auth,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "User-Agent": get_claude_code_user_agent(),
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.request(method.upper(), url, json=body, headers=headers)
            if 200 <= r.status_code < 300:
                return True
            if r.status_code == 409:
                self._on_epoch_mismatch()
            if r.status_code in (401, 403):
                tok = get_session_ingress_auth_token()
                exp = decode_jwt_expiry(tok) if tok else None
                import time

                if exp is not None and exp * 1000 < time.time() * 1000:
                    self._on_epoch_mismatch()
            return False
        except httpx.HTTPError:
            return False

    async def initialize(self, epoch: int | None = None) -> dict[str, Any] | None:
        if not self._auth_headers():
            raise CCRInitError("no_auth_headers")
        if epoch is None:
            raw = os.environ.get("CLAUDE_CODE_WORKER_EPOCH", "")
            epoch = int(raw) if re.fullmatch(r"\d+", raw or "") else None
        if epoch is None:
            raise CCRInitError("missing_epoch")
        self._worker_epoch = int(epoch)
        ok = await self._request(
            "put",
            "/worker",
            {
                "worker_status": "idle",
                "worker_epoch": self._worker_epoch,
                "external_metadata": {"pending_action": None, "task_summary": None},
            },
        )
        if not ok:
            raise CCRInitError("worker_register_failed")
        return await self._fetch_worker_metadata()

    async def _fetch_worker_metadata(self) -> dict[str, Any] | None:
        auth = self._auth_headers()
        if not auth:
            return None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{self._session_base}/worker",
                    headers={
                        **auth,
                        "User-Agent": get_claude_code_user_agent(),
                    },
                )
            if r.status_code == 200:
                data = r.json()
                w = data.get("worker")
                if isinstance(w, dict):
                    em = w.get("external_metadata")
                    if isinstance(em, dict):
                        return em
            return None
        except (httpx.HTTPError, json.JSONDecodeError, TypeError):
            return None

    async def write_event(self, message: StdoutMessage) -> None:
        if message.get("type") == "stream_event":
            self._stream_buf.append(dict(message))
            if self._stream_timer is None:
                loop = asyncio.get_event_loop()

                def _fire() -> None:
                    asyncio.create_task(self._flush_stream_buf())

                self._stream_timer = loop.call_later(0.1, _fire)
            return
        await self._flush_stream_buf()
        if message.get("type") == "assistant":
            clear_stream_accumulator_for_message(self._accumulator, dict(message))
        uid = message.get("uuid")
        if not isinstance(uid, str) or not uid:
            message = {**dict(message), "uuid": str(uuid.uuid4())}
        await self._event_uploader.enqueue([{"payload": dict(message), "ephemeral": False}])

    async def _flush_stream_buf(self) -> None:
        if self._stream_timer:
            self._stream_timer.cancel()
            self._stream_timer = None
        if not self._stream_buf:
            return
        merged = accumulate_stream_events(list(self._stream_buf), self._accumulator)
        self._stream_buf.clear()
        for p in merged:
            await self._event_uploader.enqueue([{"payload": p, "ephemeral": False}])

    async def write_internal_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> None:
        options = options or {}
        pl = {**payload, "uuid": payload.get("uuid") or str(uuid.uuid4())}
        ev = {
            "payload": {"type": event_type, **pl},
            "is_compaction": options.get("is_compaction", False),
            "agent_id": options.get("agent_id"),
        }
        await self._internal_uploader.enqueue([ev])

    async def flush_internal_events(self) -> None:
        await self._internal_uploader.flush()

    @property
    def internal_events_pending(self) -> int:
        return self._internal_uploader.pending_count

    def report_delivery(
        self,
        msg_uuid: str,
        status: Literal["received", "processing", "processed"],
    ) -> None:
        asyncio.create_task(self._enqueue_delivery(msg_uuid, status))

    def report_state(self, state: str, details: dict[str, Any] | None = None) -> None:
        body: dict[str, Any] = {"worker_status": state}
        if details:
            body["requires_action_details"] = {
                "tool_name": details.get("tool_name"),
                "action_description": details.get("action_description"),
                "request_id": details.get("request_id"),
            }
        self._worker_state.enqueue(body)

    def report_metadata(self, metadata: dict[str, Any]) -> None:
        self._worker_state.enqueue({"external_metadata": metadata})

    def close(self) -> None:
        self._closed = True
        self._worker_state.close()
        self._event_uploader.close()
        self._internal_uploader.close()
        self._delivery_uploader.close()


def _session_base_url(session_url: str) -> str:
    from urllib.parse import urlparse

    p = urlparse(session_url)
    if p.scheme not in ("http", "https"):
        raise ValueError(f"CCRClient: Expected http(s) URL, got {p.scheme}")
    path = p.path.rstrip("/")
    return f"{p.scheme}://{p.netloc}{path}"
