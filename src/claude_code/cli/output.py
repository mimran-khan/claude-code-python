"""
CLI output utilities.

Formatted output for terminal.

Migrated from: cli/print.ts (partial)
"""

from __future__ import annotations

import json
import sys
from typing import Any


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def _supports_color() -> bool:
    """Check if terminal supports colors."""
    import os

    # Check NO_COLOR environment variable
    if os.getenv("NO_COLOR"):
        return False

    # Check if stdout is a TTY
    if not hasattr(sys.stdout, "isatty"):
        return False

    return sys.stdout.isatty()


def _colorize(text: str, color: str) -> str:
    """Apply color to text if supported."""
    if _supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def print_message(message: str, prefix: str = "", color: str = "") -> None:
    """
    Print a message.

    Args:
        message: Message to print
        prefix: Optional prefix
        color: Optional color code
    """
    if prefix:
        if color:
            prefix = _colorize(prefix, color)
        print(f"{prefix} {message}")
    else:
        if color:
            print(_colorize(message, color))
        else:
            print(message)


def print_error(message: str, prefix: str = "Error:") -> None:
    """Print an error message."""
    print_message(message, prefix, Colors.RED)


def print_warning(message: str, prefix: str = "Warning:") -> None:
    """Print a warning message."""
    print_message(message, prefix, Colors.YELLOW)


def print_info(message: str, prefix: str = "Info:") -> None:
    """Print an info message."""
    print_message(message, prefix, Colors.BLUE)


def print_success(message: str, prefix: str = "Success:") -> None:
    """Print a success message."""
    print_message(message, prefix, Colors.GREEN)


def print_json(data: Any, indent: int = 2) -> None:
    """
    Print JSON data.

    Args:
        data: Data to print as JSON
        indent: Indentation level
    """
    print(json.dumps(data, indent=indent, default=str))


def print_table(
    headers: list[str],
    rows: list[list[str]],
    column_widths: list[int] | None = None,
) -> None:
    """
    Print a simple table.

    Args:
        headers: Column headers
        rows: Table rows
        column_widths: Optional column widths
    """
    if not column_widths:
        # Calculate widths from content
        column_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(column_widths):
                    column_widths[i] = max(column_widths[i], len(str(cell)))

    # Print header
    header_line = " | ".join(h.ljust(column_widths[i]) for i, h in enumerate(headers))
    print(_colorize(header_line, Colors.BOLD))

    # Print separator
    separator = "-+-".join("-" * w for w in column_widths)
    print(separator)

    # Print rows
    for row in rows:
        row_line = " | ".join(str(cell).ljust(column_widths[i]) for i, cell in enumerate(row))
        print(row_line)


def print_progress(current: int, total: int, width: int = 40) -> None:
    """
    Print a progress bar.

    Args:
        current: Current progress
        total: Total value
        width: Bar width in characters
    """
    progress = current / total if total > 0 else 0
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    percent = int(progress * 100)

    sys.stdout.write(f"\r[{bar}] {percent}%")
    sys.stdout.flush()

    if current >= total:
        print()  # Newline when complete
