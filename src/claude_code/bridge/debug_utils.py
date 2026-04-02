"""Debug helpers for bridge HTTP/logging (ported from bridge/debugUtils.py)."""

from __future__ import annotations

import json
import re
from typing import Any

# TODO: log_event from services.analytics
# TODO: log_for_debugging from utils.debug

DEBUG_MSG_LIMIT = 2000
SECRET_FIELD_NAMES = (
    "session_ingress_token",
    "environment_secret",
    "access_token",
    "secret",
    "token",
)
_SECRET_PATTERN = re.compile(
    rf'"({"|".join(SECRET_FIELD_NAMES)})"\s*:\s*"([^"]*)"',
    re.MULTILINE,
)
REDACT_MIN_LENGTH = 16


def redact_secrets(s: str) -> str:
    def _repl(_m: re.Match[str]) -> str:
        field = _m.group(1)
        value = _m.group(2)
        if len(value) < REDACT_MIN_LENGTH:
            return f'"{field}":"[REDACTED]"'
        redacted = f"{value[:8]}...{value[-4:]}"
        return f'"{field}":"{redacted}"'

    return _SECRET_PATTERN.sub(_repl, s)


def debug_truncate(s: str) -> str:
    flat = s.replace("\n", "\\n")
    if len(flat) <= DEBUG_MSG_LIMIT:
        return flat
    return flat[:DEBUG_MSG_LIMIT] + f"... ({len(flat)} chars)"


def debug_body(data: Any) -> str:
    raw = data if isinstance(data, str) else json.dumps(data, default=str)
    s = redact_secrets(raw)
    if len(s) <= DEBUG_MSG_LIMIT:
        return s
    return s[:DEBUG_MSG_LIMIT] + f"... ({len(s)} chars)"


def error_message(err: BaseException | Any) -> str:
    if isinstance(err, BaseException):
        return str(err)
    return str(err)


def describe_axios_error(err: Any) -> str:
    """HTTP error detail extraction (httpx/requests-style response)."""
    msg = error_message(err)
    if isinstance(err, dict):
        response = err.get("response")
    elif hasattr(err, "response"):
        response = getattr(err, "response", None)
    else:
        response = None
    if response is not None:
        data = getattr(response, "json", lambda: None)()
        if data is None and hasattr(response, "text"):
            try:
                data = json.loads(response.text)
            except Exception:
                data = None
        if isinstance(data, dict):
            detail = extract_error_detail(data)
            if detail:
                return f"{msg}: {detail}"
    return msg


def extract_http_status(err: Any) -> int | None:
    response = getattr(err, "response", None)
    if response is None:
        return None
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        return status
    return None


def extract_error_detail(data: Any) -> str | None:
    if not data or not isinstance(data, dict):
        return None
    m = data.get("message")
    if isinstance(m, str):
        return m
    err = data.get("error")
    if isinstance(err, dict):
        em = err.get("message")
        if isinstance(em, str):
            return em
    return None


def log_bridge_skip(reason: str, debug_msg: str | None = None, v2: bool | None = None) -> None:
    # TODO: log_for_debugging(debug_msg); log_event('tengu_bridge_repl_skipped', ...)
    if debug_msg:
        pass
