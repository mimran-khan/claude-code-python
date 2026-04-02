"""
CLI exit handling.

Exit codes and cleanup.

Migrated from: cli/exit.ts
"""

from __future__ import annotations

import sys

# Exit codes
EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_ABORT = 130  # SIGINT (Ctrl+C)
EXIT_CODE_CONFIG_ERROR = 2
EXIT_CODE_AUTH_ERROR = 3


def exit_with_code(
    code: int = EXIT_CODE_SUCCESS,
    message: str | None = None,
) -> None:
    """
    Exit the process with a code.

    Args:
        code: Exit code
        message: Optional message to print
    """
    if message:
        if code == EXIT_CODE_SUCCESS:
            print(message)
        else:
            print(message, file=sys.stderr)

    sys.exit(code)


def exit_success(message: str | None = None) -> None:
    """Exit successfully."""
    exit_with_code(EXIT_CODE_SUCCESS, message)


def exit_error(message: str) -> None:
    """Exit with an error."""
    exit_with_code(EXIT_CODE_ERROR, f"Error: {message}")


def exit_abort() -> None:
    """Exit due to user abort (Ctrl+C)."""
    exit_with_code(EXIT_CODE_ABORT)


def exit_config_error(message: str) -> None:
    """Exit due to configuration error."""
    exit_with_code(EXIT_CODE_CONFIG_ERROR, f"Configuration Error: {message}")


def exit_auth_error(message: str) -> None:
    """Exit due to authentication error."""
    exit_with_code(EXIT_CODE_AUTH_ERROR, f"Authentication Error: {message}")


def cli_error(msg: str | None = None) -> None:
    """Print optional error to stderr and exit with code 1 (TS cliError parity)."""
    if msg:
        print(msg, file=sys.stderr)
    sys.exit(EXIT_CODE_ERROR)


def cli_ok(msg: str | None = None) -> None:
    """Print optional message to stdout and exit with code 0 (TS cliOk parity)."""
    if msg:
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()
    sys.exit(EXIT_CODE_SUCCESS)
