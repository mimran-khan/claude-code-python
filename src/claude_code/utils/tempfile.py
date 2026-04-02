"""
Temporary File Utilities.

Generate temporary file paths.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import uuid


def generate_temp_file_path(
    prefix: str = "claude-prompt",
    extension: str = ".md",
    *,
    content_hash: str | None = None,
) -> str:
    """Generate a temporary file path.

    Args:
        prefix: Optional prefix for the temp file name
        extension: Optional file extension
        content_hash: When provided, the identifier is derived from a
            SHA-256 hash of this string. This produces a path that is
            stable across process boundaries.

    Returns:
        Temp file path
    """
    if content_hash:
        # Content-based hash for stable paths
        hash_hex = hashlib.sha256(content_hash.encode()).hexdigest()[:16]
        identifier = hash_hex
    else:
        # Random UUID
        identifier = str(uuid.uuid4())

    return os.path.join(tempfile.gettempdir(), f"{prefix}-{identifier}{extension}")


def get_temp_dir() -> str:
    """Get the system temporary directory.

    Returns:
        Path to the temp directory
    """
    return tempfile.gettempdir()


def create_temp_file(
    content: str | bytes,
    prefix: str = "claude-",
    suffix: str = ".tmp",
) -> str:
    """Create a temporary file with content.

    Args:
        content: File content
        prefix: Filename prefix
        suffix: Filename suffix

    Returns:
        Path to the created file
    """
    mode = "wb" if isinstance(content, bytes) else "w"

    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    try:
        with os.fdopen(fd, mode) as f:
            f.write(content)
    except Exception:
        os.close(fd)
        raise

    return path


def create_temp_dir(prefix: str = "claude-") -> str:
    """Create a temporary directory.

    Args:
        prefix: Directory name prefix

    Returns:
        Path to the created directory
    """
    return tempfile.mkdtemp(prefix=prefix)


def cleanup_temp_file(path: str) -> bool:
    """Remove a temporary file.

    Args:
        path: Path to the file

    Returns:
        True if removed successfully
    """
    try:
        os.unlink(path)
        return True
    except OSError:
        return False
