"""
Error types and utilities.

Provides custom error classes and error handling utilities.

Migrated from: utils/errors.ts (239 lines)
"""

from __future__ import annotations

from typing import Any

try:
    from anthropic import APIUserAbortError
except ImportError:  # pragma: no cover - optional at edge versions

    class APIUserAbortError(Exception):
        """Fallback when anthropic SDK class is unavailable."""

        pass


class ClaudeError(Exception):
    """Base error class for Claude Code errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.name = self.__class__.__name__


class MalformedCommandError(Exception):
    """Error for malformed commands."""

    pass


class AbortError(Exception):
    """Error indicating an operation was aborted."""

    def __init__(self, message: str = "Operation aborted"):
        super().__init__(message)
        self.name = "AbortError"


class ConfigParseError(Exception):
    """Error for configuration file parsing failures."""

    def __init__(
        self,
        message: str,
        file_path: str,
        default_config: Any = None,
    ):
        super().__init__(message)
        self.name = "ConfigParseError"
        self.file_path = file_path
        self.default_config = default_config


class ShellError(Exception):
    """Error from shell command execution."""

    def __init__(
        self,
        stdout: str,
        stderr: str,
        code: int,
        interrupted: bool = False,
    ):
        super().__init__("Shell command failed")
        self.name = "ShellError"
        self.stdout = stdout
        self.stderr = stderr
        self.code = code
        self.interrupted = interrupted


class TeleportOperationError(Exception):
    """Error from teleport operations."""

    def __init__(self, message: str, formatted_message: str):
        super().__init__(message)
        self.name = "TeleportOperationError"
        self.formatted_message = formatted_message


class TelemetrySafeError(Exception):
    """
    Error with a message safe to log to telemetry.

    Use when you've verified the message contains no sensitive data
    (file paths, URLs, code snippets).
    """

    def __init__(self, message: str, telemetry_message: str | None = None):
        super().__init__(message)
        self.name = "TelemetrySafeError"
        self.telemetry_message = telemetry_message or message


class ImageSizeError(Exception):
    """Error when an image exceeds size limits."""

    def __init__(self, message: str):
        super().__init__(message)
        self.name = "ImageSizeError"


class ImageResizeError(Exception):
    """Error when image resizing fails."""

    def __init__(self, message: str):
        super().__init__(message)
        self.name = "ImageResizeError"


class ToolExecutionError(Exception):
    """Error during tool execution."""

    def __init__(self, message: str, tool_name: str = ""):
        super().__init__(message)
        self.name = "ToolExecutionError"
        self.tool_name = tool_name


class PermissionDeniedError(Exception):
    """Error when permission is denied."""

    def __init__(self, message: str, tool_name: str = ""):
        super().__init__(message)
        self.name = "PermissionDeniedError"
        self.tool_name = tool_name


def is_abort_error(e: BaseException) -> bool:
    """
    Check if an error is an abort-type error.

    Matches our AbortError, the SDK's APIUserAbortError (via isinstance —
    minified builds may mangle class names), or Error.name == 'AbortError'.
    """
    if isinstance(e, AbortError):
        return True
    if isinstance(e, APIUserAbortError):
        return True
    if isinstance(e, Exception):
        return getattr(e, "name", "") == "AbortError"
    return False


def has_exact_error_message(error: BaseException, message: str) -> bool:
    """Check if an error has an exact message."""
    return isinstance(error, Exception) and str(error) == message


def to_error(e: Any) -> Exception:
    """
    Normalize an unknown value into an Exception.

    Use at catch-site boundaries when you need an Exception instance.
    """
    if isinstance(e, Exception):
        return e
    return Exception(str(e))


def error_message(e: Any) -> str:
    """
    Extract a string message from an unknown error-like value.

    Use when you only need the message (e.g., for logging or display).
    """
    if isinstance(e, Exception):
        return str(e)
    return str(e)


def get_errno_code(e: Any) -> str | None:
    """
    Extract the errno code (e.g., 'ENOENT', 'EACCES') from a caught error.

    Returns None if the error has no code.
    """
    if hasattr(e, "errno"):
        import errno as errno_module

        err_num = e.errno
        # Try to get the name from errno
        for name in dir(errno_module):
            if not name.startswith("_") and getattr(errno_module, name) == err_num:
                return name
        return str(err_num)
    return None


def is_enoent(e: Any) -> bool:
    """
    Check if the error is ENOENT (file or directory does not exist).
    """
    import errno

    if isinstance(e, FileNotFoundError):
        return True
    if hasattr(e, "errno"):
        return e.errno == errno.ENOENT
    return False


def is_eacces(e: Any) -> bool:
    """
    Check if the error is EACCES (permission denied).
    """
    import errno

    if isinstance(e, PermissionError):
        return True
    if hasattr(e, "errno"):
        return e.errno == errno.EACCES
    return False


def get_errno_path(e: Any) -> str | None:
    """
    Extract the filesystem path from an error.

    Returns None if the error has no path.
    """
    if hasattr(e, "filename"):
        return e.filename
    return None
