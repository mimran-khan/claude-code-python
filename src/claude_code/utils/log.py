"""
Logging utilities.

Functions for logging errors and MCP-related events.

Migrated from: utils/log.ts (363 lines)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

# In-memory error log
MAX_IN_MEMORY_ERRORS = 100
_in_memory_error_log: list[dict[str, str]] = []


class ErrorLogSink(Protocol):
    """Protocol for error log backends."""

    def log_error(self, error: Exception) -> None: ...
    def log_mcp_error(self, server_name: str, error: Any) -> None: ...
    def log_mcp_debug(self, server_name: str, message: str) -> None: ...
    def get_errors_path(self) -> str: ...
    def get_mcp_logs_path(self, server_name: str) -> str: ...


@dataclass
class QueuedErrorEvent:
    """Queued error event for events logged before sink is attached."""

    event_type: str  # "error", "mcpError", "mcpDebug"
    error: Exception | None = None
    server_name: str = ""
    message: str = ""


_error_queue: list[QueuedErrorEvent] = []
_error_log_sink: ErrorLogSink | None = None


def _add_to_in_memory_error_log(error: str) -> None:
    """Add an error to the in-memory log."""
    global _in_memory_error_log

    if len(_in_memory_error_log) >= MAX_IN_MEMORY_ERRORS:
        _in_memory_error_log.pop(0)

    _in_memory_error_log.append(
        {
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }
    )


def attach_error_log_sink(sink: ErrorLogSink) -> None:
    """
    Attach the error log sink.

    Queued events are drained immediately.
    Idempotent: if a sink is already attached, this is a no-op.
    """
    global _error_log_sink, _error_queue

    if _error_log_sink is not None:
        return

    _error_log_sink = sink

    # Drain the queue
    if _error_queue:
        queued_events = list(_error_queue)
        _error_queue.clear()

        for event in queued_events:
            if event.event_type == "error" and event.error:
                sink.log_error(event.error)
            elif event.event_type == "mcpError":
                sink.log_mcp_error(event.server_name, event.error)
            elif event.event_type == "mcpDebug":
                sink.log_mcp_debug(event.server_name, event.message)


def log_for_diagnostics(
    level: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Structured diagnostics for context/setup timing (parity with TS logForDiagnostics).

    Forwards to debug logging when debug mode is active; otherwise no-op.
    """
    from .debug import is_debug_mode, log_for_debugging

    if not is_debug_mode():
        return
    suffix = f" {details!r}" if details else ""
    dbg_level = "debug"
    if level == "error":
        dbg_level = "error"
    elif level in ("warn", "warning"):
        dbg_level = "warn"
    elif level == "info":
        dbg_level = "info"
    elif level == "verbose":
        dbg_level = "verbose"
    log_for_debugging(f"[diag:{level}] {message}{suffix}", level=dbg_level)


def log_error(error: BaseException) -> None:
    """
    Log an error to multiple destinations.

    Logs to:
    - Debug logs
    - In-memory error log
    - Persistent error log file (for ant users)
    """
    from .debug import log_for_debugging
    from .errors import to_error

    err = to_error(error)

    # Log to debug
    log_for_debugging(f"Error: {err}", level="error")

    # Add to in-memory log
    _add_to_in_memory_error_log(str(err))

    # Forward to sink or queue
    if _error_log_sink:
        _error_log_sink.log_error(err)
    else:
        _error_queue.append(
            QueuedErrorEvent(
                event_type="error",
                error=err,
            )
        )


def log_mcp_error(server_name: str, error: Any) -> None:
    """Log an MCP error."""
    from .debug import log_for_debugging

    log_for_debugging(f"MCP error ({server_name}): {error}", level="error")

    if _error_log_sink:
        _error_log_sink.log_mcp_error(server_name, error)
    else:
        _error_queue.append(
            QueuedErrorEvent(
                event_type="mcpError",
                server_name=server_name,
                error=error,
            )
        )


def log_mcp_debug(server_name: str, message: str) -> None:
    """Log an MCP debug message."""
    from .debug import log_for_debugging

    log_for_debugging(f"MCP ({server_name}): {message}", level="debug")

    if _error_log_sink:
        _error_log_sink.log_mcp_debug(server_name, message)
    else:
        _error_queue.append(
            QueuedErrorEvent(
                event_type="mcpDebug",
                server_name=server_name,
                message=message,
            )
        )


def get_in_memory_errors() -> list[dict[str, str]]:
    """Get the in-memory error log."""
    return list(_in_memory_error_log)


def clear_in_memory_errors() -> None:
    """Clear the in-memory error log."""
    global _in_memory_error_log
    _in_memory_error_log.clear()


def get_log_display_title(
    log: dict[str, Any],
    default_title: str = "",
) -> str:
    """
    Get the display title for a log/session.

    Falls back through: agentName → customTitle → summary → firstPrompt → sessionId
    """
    # Skip firstPrompt if it's an autonomous mode auto-prompt
    first_prompt = log.get("firstPrompt", "")
    is_autonomous_prompt = first_prompt.startswith("<tick>")

    # Try various title sources in order
    title = (
        log.get("agentName")
        or log.get("customTitle")
        or log.get("summary")
        or (first_prompt if first_prompt and not is_autonomous_prompt else None)
        or default_title
        or ("Autonomous session" if is_autonomous_prompt else None)
        or (log.get("sessionId", "")[:8] if log.get("sessionId") else "")
    )

    return (title or "").strip()


def date_to_filename(date: datetime) -> str:
    """Convert a datetime to a filename-safe string."""
    return date.isoformat().replace(":", "-").replace(".", "-")


def set_last_api_request(request: dict[str, Any]) -> None:
    """Store the last API request for debugging."""
    from ..bootstrap.state import set_state

    set_state("last_api_request", request)


def set_last_api_request_messages(messages: list[dict[str, Any]]) -> None:
    """Store the last API request messages for debugging."""
    from ..bootstrap.state import set_state

    set_state("last_api_request_messages", messages)
