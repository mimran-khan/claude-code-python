"""
Hash Utilities.

Non-cryptographic and cryptographic hash functions.
"""

from __future__ import annotations

import hashlib


def djb2_hash(s: str) -> int:
    """djb2 string hash.

    Fast non-cryptographic hash returning a signed 32-bit int.
    Deterministic across runtimes.

    Args:
        s: The string to hash

    Returns:
        A signed 32-bit integer hash
    """
    h = 0
    for c in s:
        h = ((h << 5) - h + ord(c)) & 0xFFFFFFFF

    # Convert to signed 32-bit
    if h >= 0x80000000:
        h -= 0x100000000

    return h


def hash_content(content: str | bytes) -> str:
    """Hash content for change detection.

    Uses SHA-256 for a collision-resistant hash.

    Args:
        content: The content to hash

    Returns:
        A hex-encoded hash string
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def hash_pair(a: str, b: str) -> str:
    """Hash two strings without allocating a concatenated string.

    Uses SHA-256 with incremental updates.

    Args:
        a: First string
        b: Second string

    Returns:
        A hex-encoded hash string
    """
    h = hashlib.sha256()
    h.update(a.encode("utf-8"))
    h.update(b"\0")
    h.update(b.encode("utf-8"))
    return h.hexdigest()


def hash_file(path: str) -> str:
    """Hash a file's contents.

    Args:
        path: Path to the file

    Returns:
        A hex-encoded hash string
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_hash(content: str | bytes) -> str:
    """MD5 hash for non-security purposes.

    Args:
        content: The content to hash

    Returns:
        A hex-encoded MD5 hash
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.md5(content).hexdigest()


def short_hash(content: str, length: int = 8) -> str:
    """Generate a short hash of content.

    Args:
        content: The content to hash
        length: Length of the short hash

    Returns:
        A truncated hex-encoded hash
    """
    return hash_content(content)[:length]
