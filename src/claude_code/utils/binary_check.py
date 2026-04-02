"""
Binary Check Utilities.

Check if system binaries/commands are installed.
"""

from __future__ import annotations

import shutil
from functools import lru_cache

# Session cache
_binary_cache: dict[str, bool] = {}


async def is_binary_installed(command: str) -> bool:
    """Check if a binary/command is installed.

    Args:
        command: The command name to check (e.g., 'gopls', 'rust-analyzer')

    Returns:
        True if the command exists
    """
    if not command or not command.strip():
        return False

    trimmed = command.strip()

    # Check cache
    if trimmed in _binary_cache:
        return _binary_cache[trimmed]

    # Use shutil.which for cross-platform binary detection
    exists = shutil.which(trimmed) is not None

    _binary_cache[trimmed] = exists
    return exists


def is_binary_installed_sync(command: str) -> bool:
    """Synchronously check if a binary is installed.

    Args:
        command: The command name

    Returns:
        True if the command exists
    """
    if not command or not command.strip():
        return False

    trimmed = command.strip()

    if trimmed in _binary_cache:
        return _binary_cache[trimmed]

    exists = shutil.which(trimmed) is not None
    _binary_cache[trimmed] = exists
    return exists


def clear_binary_cache() -> None:
    """Clear the binary check cache."""
    _binary_cache.clear()


@lru_cache(maxsize=100)
def which(command: str) -> str | None:
    """Find the path to a command.

    Args:
        command: The command name

    Returns:
        Path to the command or None
    """
    return shutil.which(command)
