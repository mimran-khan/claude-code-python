"""
Path utilities.

Functions for path manipulation, expansion, and validation.

Migrated from: utils/path.ts (156 lines)
"""

from __future__ import annotations

import os
import re


def expand_path(path: str, base_dir: str | None = None) -> str:
    """
    Expand a path that may contain tilde notation (~) to an absolute path.

    On Windows, POSIX-style paths are converted to Windows format.

    Args:
        path: The path to expand
        base_dir: Base directory for resolving relative paths

    Returns:
        The expanded absolute path

    Raises:
        ValueError: If path is invalid or contains null bytes
    """
    from .cwd import get_cwd

    actual_base_dir = base_dir or get_cwd() or os.getcwd()

    if not isinstance(path, str):
        raise TypeError(f"Path must be a string, received {type(path).__name__}")

    if not isinstance(actual_base_dir, str):
        raise TypeError(f"Base directory must be a string, received {type(actual_base_dir).__name__}")

    # Security: Check for null bytes
    if "\0" in path or "\0" in actual_base_dir:
        raise ValueError("Path contains null bytes")

    # Handle empty or whitespace-only paths
    trimmed = path.strip()
    if not trimmed:
        return os.path.normpath(actual_base_dir)

    # Handle home directory notation
    if trimmed == "~":
        return os.path.expanduser("~")

    if trimmed.startswith("~/"):
        return os.path.join(os.path.expanduser("~"), trimmed[2:])

    # Handle absolute paths
    if os.path.isabs(trimmed):
        return os.path.normpath(trimmed)

    # Handle relative paths
    return os.path.normpath(os.path.join(actual_base_dir, trimmed))


def to_relative_path(absolute_path: str) -> str:
    """
    Convert an absolute path to a relative path from cwd.

    If the path is outside cwd (would start with ..), returns
    the absolute path unchanged.
    """
    from .cwd import get_cwd

    relative = os.path.relpath(absolute_path, get_cwd())

    # If would go outside cwd, keep absolute
    if relative.startswith(".."):
        return absolute_path

    return relative


def get_directory_for_path(path: str) -> str:
    """
    Get the directory path for a given file or directory path.

    If the path is a directory, returns the path itself.
    If the path is a file or doesn't exist, returns the parent directory.
    """
    absolute_path = expand_path(path)

    # Security: Skip UNC paths
    if absolute_path.startswith("\\\\") or absolute_path.startswith("//"):
        return os.path.dirname(absolute_path)

    try:
        if os.path.isdir(absolute_path):
            return absolute_path
    except Exception:
        pass

    return os.path.dirname(absolute_path)


def contains_path_traversal(path: str) -> bool:
    """
    Check if a path contains directory traversal patterns.

    Returns True if the path contains ../ or ..\\ patterns.
    """
    return bool(re.search(r"(?:^|[\\/])\.\.(?:[\\/]|$)", path))


def sanitize_path(path: str) -> str:
    """
    Sanitize a path by removing dangerous characters.

    Removes null bytes and normalizes the path.
    """
    # Remove null bytes
    sanitized = path.replace("\0", "")

    # Normalize
    return os.path.normpath(sanitized)


def normalize_path_for_config_key(path: str) -> str:
    """
    Normalize a path for use as a JSON config key.

    Uses forward slashes for consistent serialization.
    """
    # Normalize first
    normalized = os.path.normpath(path)

    # Convert to forward slashes
    return normalized.replace("\\", "/")


def join_paths(*paths: str) -> str:
    """Join paths together."""
    return os.path.join(*paths)


def get_basename(path: str) -> str:
    """Get the base name of a path."""
    return os.path.basename(path)


def get_dirname(path: str) -> str:
    """Get the directory name of a path."""
    return os.path.dirname(path)


def get_extension(path: str) -> str:
    """Get the file extension of a path."""
    return os.path.splitext(path)[1]


def split_extension(path: str) -> tuple[str, str]:
    """Split a path into root and extension."""
    return os.path.splitext(path)


def is_absolute(path: str) -> bool:
    """Check if a path is absolute."""
    return os.path.isabs(path)


def is_relative(path: str) -> bool:
    """Check if a path is relative."""
    return not os.path.isabs(path)


def get_common_prefix(*paths: str) -> str:
    """Get the common prefix of multiple paths."""
    return os.path.commonprefix(list(paths))


def get_common_path(paths: list[str]) -> str:
    """Get the longest common subpath of multiple paths."""
    if not paths:
        return ""
    try:
        return os.path.commonpath(paths)
    except ValueError:
        return ""


def normalize_separators(path: str) -> str:
    """Normalize path separators to the OS default."""
    return path.replace("/", os.sep).replace("\\", os.sep)


def to_posix_path(path: str) -> str:
    """Convert a path to POSIX format (forward slashes)."""
    return path.replace("\\", "/")


def resolve_path(path: str) -> str:
    """Resolve a path to an absolute path."""
    return os.path.abspath(path)
