"""
Debug utilities.

Functions for debug logging and diagnostics.

Migrated from: utils/debug.ts (269 lines)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any, Literal

from .env_utils import is_env_truthy

DebugLogLevel = Literal["verbose", "debug", "info", "warn", "error"]

LEVEL_ORDER: dict[DebugLogLevel, int] = {
    "verbose": 0,
    "debug": 1,
    "info": 2,
    "warn": 3,
    "error": 4,
}

_runtime_debug_enabled = False
_has_formatted_output = False


@cache
def get_min_debug_log_level() -> DebugLogLevel:
    """Get the minimum debug log level."""
    raw = os.getenv("CLAUDE_CODE_DEBUG_LOG_LEVEL", "").lower().strip()
    if raw in LEVEL_ORDER:
        return raw  # type: ignore
    return "debug"


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    global _runtime_debug_enabled

    if _runtime_debug_enabled:
        return True

    if is_env_truthy(os.getenv("DEBUG")):
        return True

    if is_env_truthy(os.getenv("DEBUG_SDK")):
        return True

    if "--debug" in sys.argv or "-d" in sys.argv:
        return True

    if is_debug_to_stderr():
        return True

    # Check for --debug=pattern syntax
    if any(arg.startswith("--debug=") for arg in sys.argv):
        return True

    # --debug-file implicitly enables debug mode
    return get_debug_file_path() is not None


def enable_debug_logging() -> bool:
    """
    Enable debug logging mid-session.

    Returns True if logging was already active.
    """
    global _runtime_debug_enabled
    was_active = is_debug_mode() or os.getenv("USER_TYPE") == "ant"
    _runtime_debug_enabled = True
    return was_active


@cache
def is_debug_to_stderr() -> bool:
    """Check if debug output should go to stderr."""
    return "--debug-to-stderr" in sys.argv or "-d2e" in sys.argv


@cache
def get_debug_file_path() -> str | None:
    """Get the debug file path from command line args."""
    for i, arg in enumerate(sys.argv):
        if arg.startswith("--debug-file="):
            return arg[len("--debug-file=") :]
        if arg == "--debug-file" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def get_debug_filter() -> str | None:
    """Get the debug filter pattern from command line args."""
    for arg in sys.argv:
        if arg.startswith("--debug="):
            return arg[len("--debug=") :]
    return None


def should_show_debug_message(message: str, filter_pattern: str | None) -> bool:
    """Check if a debug message should be shown based on the filter."""
    if filter_pattern is None:
        return True

    # Simple substring match
    return filter_pattern.lower() in message.lower()


def should_log_debug_message(message: str) -> bool:
    """Check if a debug message should be logged."""
    if os.getenv("NODE_ENV") == "test" and not is_debug_to_stderr():
        return False

    # Non-ants only write debug logs when debug mode is active
    if os.getenv("USER_TYPE") != "ant" and not is_debug_mode():
        return False

    filter_pattern = get_debug_filter()
    return should_show_debug_message(message, filter_pattern)


def set_has_formatted_output(value: bool) -> None:
    """Set whether there is formatted output."""
    global _has_formatted_output
    _has_formatted_output = value


def get_has_formatted_output() -> bool:
    """Get whether there is formatted output."""
    return _has_formatted_output


def log_for_debugging(
    message: str,
    *,
    level: DebugLogLevel = "debug",
    data: dict[str, Any] | None = None,
) -> None:
    """
    Log a debug message.

    Args:
        message: The message to log
        level: Log level
        data: Optional additional data to include
    """
    if not should_log_debug_message(message):
        return

    min_level = get_min_debug_log_level()
    if LEVEL_ORDER.get(level, 1) < LEVEL_ORDER.get(min_level, 1):
        return

    timestamp = datetime.now().isoformat()
    formatted = f"[{timestamp}] [{level.upper()}] {message}"

    if data:
        from .json_utils import safe_json_stringify

        data_str = safe_json_stringify(data)
        formatted = f"{formatted} {data_str}"

    if is_debug_to_stderr():
        print(formatted, file=sys.stderr)
        return

    # Write to debug file if specified
    debug_file = get_debug_file_path()
    if debug_file:
        _write_to_debug_file(debug_file, formatted)
        return

    # Write to default debug log location
    _write_to_default_debug_log(formatted)


def _write_to_debug_file(path: str, message: str) -> None:
    """Write a message to a specific debug file."""
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass


def _write_to_default_debug_log(message: str) -> None:
    """Write a message to the default debug log location."""
    try:
        from .env_utils import get_claude_config_home_dir

        debug_dir = Path(get_claude_config_home_dir()) / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        # Use session-based filename
        from ..bootstrap.state import get_session_id

        session_id = get_session_id()

        log_file = debug_dir / f"{session_id}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")

        # Update latest symlink
        latest_link = debug_dir / "latest"
        try:
            if latest_link.is_symlink():
                latest_link.unlink()
            latest_link.symlink_to(log_file.name)
        except Exception:
            pass
    except Exception:
        pass


def log_ant_error(error: BaseException, context: str = "") -> None:
    """Log an error for ant users."""
    message = f"Error: {error}"
    if context:
        message = f"{context}: {message}"
    log_for_debugging(message, level="error")
