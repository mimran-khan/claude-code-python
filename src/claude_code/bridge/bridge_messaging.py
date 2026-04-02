"""Bridge ingress parsing and control-request handling (ported from bridge/bridgeMessaging.ts)."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable
from typing import Any, Protocol, TypedDict, cast

# TODO: log_event tengu_bridge_message_received
# TODO: normalize_control_message_keys

logger = logging.getLogger(__name__)


def is_sdk_message(value: object) -> bool:
    return value is not None and isinstance(value, dict) and isinstance(value.get("type"), str)


def is_sdk_control_response(value: object) -> bool:
    return isinstance(value, dict) and value.get("type") == "control_response" and "response" in value


def is_sdk_control_request(value: object) -> bool:
    return (
        isinstance(value, dict)
        and value.get("type") == "control_request"
        and "request_id" in value
        and "request" in value
    )


def is_eligible_bridge_message(m: dict[str, Any]) -> bool:
    t = m.get("type")
    if t in ("user", "assistant") and m.get("isVirtual"):
        return False
    if t in ("user", "assistant"):
        return True
    return bool(t == "system" and m.get("subtype") == "local_command")


def extract_title_text(m: dict[str, Any]) -> str | None:
    if m.get("type") != "user" or m.get("isMeta") or m.get("toolUseResult") or m.get("isCompactSummary"):
        return None
    origin = m.get("origin")
    if isinstance(origin, dict) and origin.get("kind") != "human":
        return None
    inner = m.get("message")
    if not isinstance(inner, dict):
        return None
    content = inner.get("content")
    raw: str | None = None
    if isinstance(content, str):
        raw = content
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                raw = str(block.get("text", ""))
                break
    if not raw:
        return None
    # TODO: strip_display_tags_allow_empty(raw)
    clean = raw.strip()
    return clean or None


class ReplBridgeTransport(Protocol):
    def write(self, message: dict[str, Any]) -> Any: ...


class ServerControlRequestHandlers(TypedDict, total=False):
    transport: ReplBridgeTransport | None
    session_id: str
    outbound_only: bool
    on_interrupt: Callable[[], None] | None
    on_set_model: Callable[[str | None], None] | None
    on_set_max_thinking_tokens: Callable[[int | None], None] | None
    on_set_permission_mode: Callable[[str], dict[str, Any]] | None


OUTBOUND_ONLY_ERROR = "This session is outbound-only. Enable Remote Control locally to allow inbound control."


class BoundedUUIDSet:
    def __init__(self, capacity: int) -> None:
        self._capacity = max(1, capacity)
        self._ring: list[str | None] = [None] * self._capacity
        self._set: set[str] = set()
        self._write_idx = 0

    def add(self, uid: str) -> None:
        if uid in self._set:
            return
        evicted = self._ring[self._write_idx]
        if evicted is not None:
            self._set.discard(evicted)
        self._ring[self._write_idx] = uid
        self._set.add(uid)
        self._write_idx = (self._write_idx + 1) % self._capacity

    def has(self, uid: str) -> bool:
        return uid in self._set

    def clear(self) -> None:
        self._set.clear()
        self._ring = [None] * self._capacity
        self._write_idx = 0


def handle_server_control_request(
    request: dict[str, Any],
    handlers: ServerControlRequestHandlers,
) -> None:
    transport = handlers.get("transport")
    session_id = handlers.get("session_id") or ""
    outbound_only = handlers.get("outbound_only", False)
    if transport is None:
        logger.debug("[bridge:repl] Cannot respond to control_request: no transport")
        return
    req = request.get("request")
    if not isinstance(req, dict):
        return
    subtype = req.get("subtype")
    rid = request.get("request_id")
    if outbound_only and subtype != "initialize":
        event = {
            "type": "control_response",
            "response": {
                "subtype": "error",
                "request_id": rid,
                "error": OUTBOUND_ONLY_ERROR,
            },
            "session_id": session_id,
        }
        transport.write(event)
        return
    response: dict[str, Any]
    if subtype == "initialize":
        import os

        response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": rid,
                "response": {
                    "commands": [],
                    "output_style": "normal",
                    "available_output_styles": ["normal"],
                    "models": [],
                    "account": {},
                    "pid": os.getpid(),
                },
            },
        }
    elif subtype == "set_model":
        cb = handlers.get("on_set_model")
        if cb:
            cb(req.get("model") if isinstance(req.get("model"), str) else None)
        response = {
            "type": "control_response",
            "response": {"subtype": "success", "request_id": rid},
        }
    elif subtype == "set_max_thinking_tokens":
        cb = handlers.get("on_set_max_thinking_tokens")
        if cb:
            v = req.get("max_thinking_tokens")
            cb(int(v) if isinstance(v, int) else None)
        response = {
            "type": "control_response",
            "response": {"subtype": "success", "request_id": rid},
        }
    elif subtype == "set_permission_mode":
        mode = str(req.get("mode") or "")
        cb = handlers.get("on_set_permission_mode")
        default_verdict = {"ok": False, "error": "on_set_permission_mode not registered"}
        verdict = cb(mode) if cb else default_verdict
        if verdict.get("ok"):
            response = {
                "type": "control_response",
                "response": {"subtype": "success", "request_id": rid},
            }
        else:
            response = {
                "type": "control_response",
                "response": {
                    "subtype": "error",
                    "request_id": rid,
                    "error": str(verdict.get("error", "error")),
                },
            }
    elif subtype == "interrupt":
        cb = handlers.get("on_interrupt")
        if cb:
            cb()
        response = {
            "type": "control_response",
            "response": {"subtype": "success", "request_id": rid},
        }
    else:
        response = {
            "type": "control_response",
            "response": {
                "subtype": "error",
                "request_id": rid,
                "error": f"REPL bridge does not handle control_request subtype: {subtype}",
            },
        }
    event = {**response, "session_id": session_id}
    transport.write(event)


def handle_ingress_message(
    data: str,
    recent_posted_uuids: BoundedUUIDSet,
    recent_inbound_uuids: BoundedUUIDSet,
    on_inbound_message: Callable[[dict[str, Any]], Any] | None = None,
    on_permission_response: Callable[[dict[str, Any]], None] | None = None,
    on_control_request: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    try:
        parsed: Any = json.loads(data)
        # TODO: parsed = normalize_control_message_keys(parsed)
        if is_sdk_control_response(parsed):
            if on_permission_response:
                on_permission_response(cast(dict[str, Any], parsed))
            return
        if is_sdk_control_request(parsed):
            if on_control_request:
                on_control_request(cast(dict[str, Any], parsed))
            return
        if not is_sdk_message(parsed):
            return
        p = cast(dict[str, Any], parsed)
        uid = p.get("uuid") if isinstance(p.get("uuid"), str) else None
        if uid and recent_posted_uuids.has(uid):
            return
        if uid and recent_inbound_uuids.has(uid):
            return
        if p.get("type") == "user":
            if uid:
                recent_inbound_uuids.add(uid)
            if on_inbound_message:
                res = on_inbound_message(p)
                if hasattr(res, "__await__"):
                    # caller may fire-and-forget asyncio.create_task
                    pass
    except Exception as e:
        logger.debug("[bridge:repl] Failed to parse ingress message: %s", e)


def make_result_message(session_id: str) -> dict[str, Any]:
    return {
        "type": "result",
        "subtype": "success",
        "duration_ms": 0,
        "duration_api_ms": 0,
        "is_error": False,
        "num_turns": 0,
        "result": "",
        "stop_reason": None,
        "total_cost_usd": 0,
        "usage": {},
        "modelUsage": {},
        "permission_denials": [],
        "session_id": session_id,
        "uuid": str(uuid.uuid4()),
    }
