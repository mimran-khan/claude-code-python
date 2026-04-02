"""
JSON utilities.

Provides functions for parsing and handling JSON/JSONL data.

Migrated from: utils/json.ts (278 lines)
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, TypeVar

import json5

from .log import log_error

T = TypeVar("T")


def strip_bom(content: str) -> str:
    """Strip UTF-8 BOM from content if present."""
    if content.startswith("\ufeff"):
        return content[1:]
    return content


@lru_cache(maxsize=50)
def _parse_json_cached(json_str: str, should_log_error: bool) -> tuple[bool, Any]:
    """
    Internal cached JSON parser.

    Returns a tuple of (success, value).
    """
    try:
        return (True, json.loads(strip_bom(json_str)))
    except json.JSONDecodeError as e:
        if should_log_error:
            log_error(e)
        return (False, None)


def safe_parse_json(
    json_str: str | None,
    should_log_error: bool = True,
) -> Any:
    """
    Safely parse JSON string, returning None on failure.

    Uses an LRU cache for performance (bounded to 50 entries).

    Args:
        json_str: The JSON string to parse.
        should_log_error: Whether to log parsing errors.

    Returns:
        The parsed JSON value, or None if parsing fails.
    """
    if not json_str:
        return None

    # Skip cache for large strings
    if len(json_str) > 8 * 1024:
        try:
            return json.loads(strip_bom(json_str))
        except json.JSONDecodeError as e:
            if should_log_error:
                log_error(e)
            return None

    success, value = _parse_json_cached(json_str, should_log_error)
    return value if success else None


def parse_jsonl(data: str | bytes) -> list[Any]:
    """
    Parse JSONL data from a string or bytes, skipping malformed lines.

    Args:
        data: JSONL data as string or bytes.

    Returns:
        List of parsed JSON values.
    """
    if isinstance(data, bytes):
        # Handle BOM
        if data.startswith(b"\xef\xbb\xbf"):
            data = data[3:]
        content = data.decode("utf-8")
    else:
        content = strip_bom(data)

    results: list[Any] = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            # Skip malformed lines
            pass

    return results


async def read_jsonl_file(file_path: str) -> list[Any]:
    """
    Read and parse a JSONL file.

    For files larger than 100 MB, reads the tail and skips the first
    partial line.

    Args:
        file_path: Path to the JSONL file.

    Returns:
        List of parsed JSON values.
    """
    import os

    import aiofiles

    MAX_JSONL_READ_BYTES = 100 * 1024 * 1024  # 100 MB

    file_size = os.path.getsize(file_path)

    if file_size <= MAX_JSONL_READ_BYTES:
        async with aiofiles.open(file_path, "rb") as f:
            data = await f.read()
        return parse_jsonl(data)

    # Read tail of large file
    async with aiofiles.open(file_path, "rb") as f:
        await f.seek(file_size - MAX_JSONL_READ_BYTES)
        data = await f.read(MAX_JSONL_READ_BYTES)

    # Skip the first partial line
    newline_idx = data.find(b"\n")
    if newline_idx != -1 and newline_idx < len(data) - 1:
        data = data[newline_idx + 1 :]

    return parse_jsonl(data)


def json_stringify(obj: Any, default: Any = None, indent: int | None = None) -> str:
    """
    Stringify an object to JSON.

    Args:
        obj: The object to stringify.
        default: Default function for non-serializable objects.
        indent: Number of spaces for indentation.

    Returns:
        JSON string.
    """
    return json.dumps(obj, default=default, indent=indent, ensure_ascii=False)


def safe_parse_jsonc(json_str: str | None) -> Any:
    """
    Parse JSON with comments (jsonc), e.g. VS Code keybindings.json.

    Uses JSON5 for comment/trailing-comma tolerance.
    """
    if not json_str:
        return None
    try:
        return json5.loads(strip_bom(json_str))
    except Exception as e:
        log_error(e)
        return None


def add_item_to_jsonc_array(content: str, new_item: Any) -> str:
    """
    Add an item to a JSONC array when possible; falls back to a fresh JSON array.

    Comments in the original string are not preserved on rewrite (JSON5 round-trip).
    """
    if not content or not content.strip():
        return json5.dumps([new_item], indent=4, quote_keys=True)  # type: ignore[call-arg]

    clean_content = strip_bom(content)
    try:
        parsed = json5.loads(clean_content)
        if isinstance(parsed, list):
            parsed.append(new_item)
            return json5.dumps(parsed, indent=4, quote_keys=True)  # type: ignore[call-arg]
        return json5.dumps([new_item], indent=4, quote_keys=True)  # type: ignore[call-arg]
    except Exception as e:
        log_error(e)
        return json5.dumps([new_item], indent=4, quote_keys=True)  # type: ignore[call-arg]


def add_item_to_json_array(content: str, new_item: Any) -> str:
    """
    Add an item to a JSON array, preserving formatting.

    Args:
        content: The JSON string containing an array.
        new_item: The item to add.

    Returns:
        The modified JSON string.
    """
    if not content or not content.strip():
        return json_stringify([new_item], indent=4)

    clean_content = strip_bom(content)

    try:
        parsed = json.loads(clean_content)

        if isinstance(parsed, list):
            parsed.append(new_item)
            return json_stringify(parsed, indent=4)
        else:
            # Not an array, create new array
            return json_stringify([new_item], indent=4)
    except json.JSONDecodeError as e:
        log_error(e)
        return json_stringify([new_item], indent=4)
