"""
File-backed error / MCP log sink (attaches to :mod:`claude_code.utils.log`).

Migrated from: utils/errorLogSink.ts
"""

from __future__ import annotations

import json
import os
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..bootstrap.state import get_session_id
from .cache_paths import CACHE_PATHS
from .debug import log_for_debugging
from .http import VERSION
from .log import attach_error_log_sink


def _date_filename() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%d")


_DATE = _date_filename()


def get_errors_path() -> str:
    return str(Path(CACHE_PATHS.errors()) / f"{_DATE}.jsonl")


def get_mcp_logs_path(server_name: str) -> str:
    return str(Path(CACHE_PATHS.mcp_logs(server_name)) / f"{_DATE}.jsonl")


def _ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _append_jsonl(path: str, payload: dict[str, Any]) -> None:
    _ensure_parent(path)
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    try:
        with Path(path).open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        _ensure_parent(path)
        with Path(path).open("a", encoding="utf-8") as fh:
            fh.write(line)


def _should_write_ant_logs() -> bool:
    return os.environ.get("USER_TYPE") == "ant"


def _extract_server_message(data: Any) -> str | None:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        msg = data.get("message")
        if isinstance(msg, str):
            return msg
        err = data.get("error")
        if isinstance(err, dict):
            em = err.get("message")
            if isinstance(em, str):
                return em
    return None


def _format_error(error: BaseException) -> str:
    if error.__traceback__ is not None:
        return "".join(traceback.format_exception(type(error), error, error.__traceback__)).strip()
    return str(error)


def _log_error_impl(error: Exception) -> None:
    error_str = _format_error(error)
    context = ""
    try:
        import httpx

        if isinstance(error, httpx.HTTPError):
            req = getattr(error, "request", None)
            if req is not None:
                parts = [f"url={getattr(req, 'url', '')}"]
                resp = getattr(error, "response", None)
                if resp is not None and getattr(resp, "status_code", None) is not None:
                    parts.append(f"status={resp.status_code}")
                body = getattr(resp, "text", None) if resp is not None else None
                sm = _extract_server_message(body)
                if sm:
                    parts.append(f"body={sm}")
                context = f"[{', '.join(parts)}] "
    except ImportError:
        pass

    log_for_debugging(f"{type(error).__name__}: {context}{error_str}", level="error")

    if not _should_write_ant_logs():
        return

    _append_jsonl(
        get_errors_path(),
        {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "error": f"{context}{error_str}",
            "cwd": os.getcwd(),
            "userType": os.environ.get("USER_TYPE"),
            "sessionId": str(get_session_id()),
            "version": VERSION,
        },
    )


def _log_mcp_error_impl(server_name: str, error: Any) -> None:
    log_for_debugging(f'MCP server "{server_name}" {error!s}', level="error")
    error_str = _format_error(error) if isinstance(error, BaseException) else str(error)
    _append_jsonl(
        get_mcp_logs_path(server_name),
        {
            "error": error_str,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "sessionId": str(get_session_id()),
            "cwd": os.getcwd(),
        },
    )


def _log_mcp_debug_impl(server_name: str, message: str) -> None:
    log_for_debugging(f'MCP server "{server_name}": {message}')
    _append_jsonl(
        get_mcp_logs_path(server_name),
        {
            "debug": message,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "sessionId": str(get_session_id()),
            "cwd": os.getcwd(),
        },
    )


class _FileErrorLogSink:
    def log_error(self, error: Exception) -> None:
        _log_error_impl(error)

    def log_mcp_error(self, server_name: str, error: Any) -> None:
        _log_mcp_error_impl(server_name, error)

    def log_mcp_debug(self, server_name: str, message: str) -> None:
        _log_mcp_debug_impl(server_name, message)

    def get_errors_path(self) -> str:
        return get_errors_path()

    def get_mcp_logs_path(self, server_name: str) -> str:
        return get_mcp_logs_path(server_name)


def initialize_error_log_sink() -> None:
    """Attach the JSONL file sink; idempotent."""

    attach_error_log_sink(_FileErrorLogSink())
    log_for_debugging("Error log sink initialized")


__all__ = [
    "get_errors_path",
    "get_mcp_logs_path",
    "initialize_error_log_sink",
]
