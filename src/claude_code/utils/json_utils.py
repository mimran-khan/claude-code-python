"""
JSON utilities.

Functions for parsing and manipulating JSON data.

Migrated from: utils/json.ts (278 lines)
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, TypeVar

from .log import log_error

T = TypeVar("T")


# Cache size for parsed JSON
PARSE_CACHE_MAX_KEY_BYTES = 8 * 1024


@lru_cache(maxsize=50)
def _parse_json_cached(json_str: str) -> tuple[bool, Any]:
    """
    Cached JSON parsing.

    Returns (ok, value) tuple where ok indicates success.
    """
    try:
        return (True, json.loads(_strip_bom(json_str)))
    except json.JSONDecodeError:
        return (False, None)


def _strip_bom(s: str) -> str:
    """Strip UTF-8 BOM from string."""
    if s.startswith("\ufeff"):
        return s[1:]
    return s


def safe_parse_json(
    json_str: str | None,
    should_log_error: bool = True,
) -> Any:
    """
    Safely parse JSON, returning None on error.

    Memoized for performance (LRU-bounded, small inputs only).
    """
    if not json_str:
        return None

    # For large inputs, don't use cache
    if len(json_str) > PARSE_CACHE_MAX_KEY_BYTES:
        try:
            return json.loads(_strip_bom(json_str))
        except json.JSONDecodeError as e:
            if should_log_error:
                log_error(e)
            return None

    ok, value = _parse_json_cached(json_str)
    if not ok and should_log_error:
        # Re-parse to get the error for logging
        try:
            json.loads(_strip_bom(json_str))
        except json.JSONDecodeError as e:
            log_error(e)

    return value if ok else None


def safe_parse_jsonc(json_str: str | None) -> Any:
    """
    Safely parse JSON with comments (JSONC).

    Removes C-style comments before parsing.
    """
    if not json_str:
        return None

    try:
        # Remove single-line comments
        cleaned = re.sub(r"//.*$", "", json_str, flags=re.MULTILINE)
        # Remove multi-line comments
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        return json.loads(_strip_bom(cleaned))
    except json.JSONDecodeError as e:
        log_error(e)
        return None


def parse_jsonl(data: str) -> list[Any]:
    """
    Parse JSONL (JSON Lines) data.

    Each line is a separate JSON object.
    """
    results = []

    for line in data.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            # Skip malformed lines
            pass

    return results


def parse_jsonl_file(path: str | Path) -> list[Any]:
    """
    Parse a JSONL file.

    Reads the file and parses each line as JSON.
    """
    try:
        with open(path, encoding="utf-8") as f:
            return parse_jsonl(f.read())
    except Exception as e:
        log_error(e)
        return []


def safe_json_stringify(
    obj: Any,
    indent: int | None = None,
    default: Any = None,
) -> str:
    """
    Safely stringify an object to JSON.

    Handles circular references and non-serializable types.
    """

    def _default_handler(o: Any) -> Any:
        if default is not None:
            return default(o)
        # Convert non-serializable types to string
        return str(o)

    try:
        return json.dumps(obj, indent=indent, default=_default_handler)
    except Exception:
        return "{}"


def extract_json_from_text(text: str) -> Any | None:
    """
    Extract JSON from text that may contain other content.

    Looks for JSON objects or arrays in the text.
    """
    # Try to find JSON object
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        try:
            return json.loads(obj_match.group())
        except json.JSONDecodeError:
            pass

    # Try to find JSON array
    arr_match = re.search(r"\[[\s\S]*\]", text)
    if arr_match:
        try:
            return json.loads(arr_match.group())
        except json.JSONDecodeError:
            pass

    return None


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries.

    Values from override take precedence.
    """
    result = dict(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def safe_get_nested(
    obj: dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    """
    Safely get a nested value from a dictionary.

    Returns default if any key in the path is missing.
    """
    current = obj
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
