"""
File utilities.

Functions for file operations, reading, writing, and manipulation.

Migrated from: utils/file.ts (585 lines)
"""

from __future__ import annotations

import os
import shutil
from typing import Literal

from .log import log_error
from .path_utils import expand_path

MAX_OUTPUT_SIZE = 0.25 * 1024 * 1024  # 0.25MB in bytes

LineEndingType = Literal["LF", "CRLF"]

_BINARY_SNIFF_BYTES = 8192


def is_probably_binary(filepath: str, max_scan: int = _BINARY_SNIFF_BYTES) -> bool:
    """
    Heuristic binary detection: NUL bytes or a high ratio of control characters.
    """
    try:
        with open(filepath, "rb") as f:
            sample = f.read(max_scan)
    except OSError:
        return True
    if not sample:
        return False
    if b"\x00" in sample:
        return True
    n = len(sample)
    ctrl = sum(1 for b in sample if b < 8 or (b > 13 and b < 32 and b not in (9, 10, 13)))
    return (ctrl / n) > 0.3


def _sniff_text_encoding_from_bytes(data: bytes) -> str:
    """Pick a text encoding when no BOM matches (best-effort)."""
    if not data:
        return "utf-8"
    for enc in ("utf-8", "utf-8-sig", "cp1252", "iso-8859-1"):
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def path_exists(path: str) -> bool:
    """Check if a path exists."""
    return os.path.exists(path)


async def path_exists_async(path: str) -> bool:
    """Check if a path exists (async version)."""
    import aiofiles.os

    try:
        await aiofiles.os.stat(path)
        return True
    except FileNotFoundError:
        return False


def read_file_safe(filepath: str) -> str | None:
    """
    Read a text file safely: skip likely binaries, detect encoding, return None on error.
    """
    try:
        if is_probably_binary(filepath):
            return None
        encoding = detect_file_encoding(filepath)
        with open(filepath, encoding=encoding, errors="replace") as f:
            return f.read()
    except Exception as e:
        log_error(e)
        return None


async def read_file_async(filepath: str) -> str:
    """Read a file asynchronously."""
    import aiofiles

    async with aiofiles.open(filepath, encoding="utf-8") as f:
        return await f.read()


def get_file_modification_time(filepath: str) -> float:
    """
    Get the normalized modification time of a file in milliseconds.

    Uses floor to ensure consistent timestamp comparisons.
    """
    import math

    stat = os.stat(filepath)
    return math.floor(stat.st_mtime * 1000)


async def get_file_modification_time_async(filepath: str) -> float:
    """Async variant of get_file_modification_time."""
    import math

    import aiofiles.os

    stat = await aiofiles.os.stat(filepath)
    return math.floor(stat.st_mtime * 1000)


def write_text_content(
    filepath: str,
    content: str,
    encoding: str = "utf-8",
    line_endings: LineEndingType = "LF",
) -> None:
    """
    Write text content to a file with specified encoding and line endings.
    """
    to_write = content
    if line_endings == "CRLF":
        # Normalize existing CRLF to LF first
        to_write = content.replace("\r\n", "\n").replace("\n", "\r\n")

    with open(filepath, "w", encoding=encoding) as f:
        f.write(to_write)


async def write_text_content_async(
    filepath: str,
    content: str,
    encoding: str = "utf-8",
    line_endings: LineEndingType = "LF",
) -> None:
    """Write text content to a file asynchronously."""
    import aiofiles

    to_write = content
    if line_endings == "CRLF":
        to_write = content.replace("\r\n", "\n").replace("\n", "\r\n")

    async with aiofiles.open(filepath, "w", encoding=encoding) as f:
        await f.write(to_write)


def detect_file_encoding(filepath: str) -> str:
    """
    Detect the encoding of a file (BOM first, then short-sample sniff).

    Returns 'utf-8' by default or on error.
    """
    try:
        with open(filepath, "rb") as f:
            header = f.read(4)
            rest = f.read(65536)

        sample = header + rest

        if sample.startswith(b"\xff\xfe\x00\x00"):
            return "utf-32-le"
        if sample.startswith(b"\x00\x00\xfe\xff"):
            return "utf-32-be"
        if sample.startswith(b"\xff\xfe"):
            return "utf-16-le"
        if sample.startswith(b"\xfe\xff"):
            return "utf-16-be"
        if sample.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"

        return _sniff_text_encoding_from_bytes(sample)
    except Exception as e:
        log_error(e)
        return "utf-8"


def detect_line_endings(filepath: str, encoding: str = "utf-8") -> LineEndingType:
    """
    Detect the line ending type of a file.
    """
    try:
        with open(filepath, encoding=encoding, newline="") as f:
            # Read first 4KB
            content = f.read(4096)

        return detect_line_endings_for_string(content)
    except Exception as e:
        log_error(e)
        return "LF"


def detect_line_endings_for_string(content: str) -> LineEndingType:
    """Detect line endings for a string."""
    if "\r\n" in content:
        return "CRLF"
    return "LF"


def convert_leading_tabs_to_spaces(content: str) -> str:
    """Convert leading tabs to spaces (2 spaces per tab)."""
    if "\t" not in content:
        return content

    import re

    return re.sub(r"^\t+", lambda m: "  " * len(m.group()), content, flags=re.MULTILINE)


def get_absolute_and_relative_paths(path: str | None) -> dict[str, str | None]:
    """
    Get both absolute and relative paths for a given path.
    """
    from .cwd import get_cwd

    if not path:
        return {"absolute_path": None, "relative_path": None}

    absolute_path = expand_path(path)
    cwd = get_cwd()
    relative_path = os.path.relpath(absolute_path, cwd)

    return {
        "absolute_path": absolute_path,
        "relative_path": relative_path,
    }


def ensure_directory(path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)


async def ensure_directory_async(path: str) -> None:
    """Ensure a directory exists (async version)."""
    import aiofiles.os

    await aiofiles.os.makedirs(path, exist_ok=True)


def remove_file(path: str) -> bool:
    """Remove a file, returning True if successful."""
    try:
        os.remove(path)
        return True
    except Exception as e:
        log_error(e)
        return False


def remove_directory(path: str, recursive: bool = False) -> bool:
    """Remove a directory, returning True if successful."""
    try:
        if recursive:
            shutil.rmtree(path)
        else:
            os.rmdir(path)
        return True
    except Exception as e:
        log_error(e)
        return False


def copy_file(src: str, dst: str) -> bool:
    """Copy a file, returning True if successful."""
    try:
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        log_error(e)
        return False


def move_file(src: str, dst: str) -> bool:
    """Move a file, returning True if successful."""
    try:
        shutil.move(src, dst)
        return True
    except Exception as e:
        log_error(e)
        return False


def get_file_size(path: str) -> int:
    """Get the size of a file in bytes."""
    return os.path.getsize(path)


def is_file(path: str) -> bool:
    """Check if a path is a file."""
    return os.path.isfile(path)


def is_directory(path: str) -> bool:
    """Check if a path is a directory."""
    return os.path.isdir(path)


def list_directory(path: str) -> list[str]:
    """List contents of a directory."""
    try:
        return os.listdir(path)
    except Exception as e:
        log_error(e)
        return []


def get_real_path(path: str) -> str:
    """Get the real (canonicalized) path, resolving symlinks."""
    return os.path.realpath(path)


def is_symlink(path: str) -> bool:
    """Check if a path is a symbolic link."""
    return os.path.islink(path)


def create_symlink(target: str, link: str) -> bool:
    """Create a symbolic link."""
    try:
        os.symlink(target, link)
        return True
    except Exception as e:
        log_error(e)
        return False


def read_symlink(path: str) -> str | None:
    """Read the target of a symbolic link."""
    try:
        return os.readlink(path)
    except Exception as e:
        log_error(e)
        return None
