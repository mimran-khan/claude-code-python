"""
API utilities.

Functions for API schema generation, tool formatting, and request building.

Migrated from: utils/api.ts (719 lines)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..core.tool import Tool


@dataclass
class SystemPromptBlock:
    """A block of system prompt text with optional cache settings."""

    text: str
    cache_scope: str | None = None  # "global" or "org"


CacheScope = str  # "global" | "org"


def normalize_tool_input(
    tool_name: str,
    input_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize tool input data.

    Handles special cases like FileEdit whitespace stripping.
    """
    normalized = dict(input_data)

    # Strip trailing whitespace from FileEdit old_string/new_string
    if tool_name in ("FileEdit", "str_replace_based_edit_tool"):
        if "old_string" in normalized:
            normalized["old_string"] = _strip_trailing_whitespace(normalized["old_string"])
        if "new_string" in normalized:
            normalized["new_string"] = _strip_trailing_whitespace(normalized["new_string"])

    return normalized


def normalize_tool_input_for_api(
    tool_name: str,
    input_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize tool input for API transmission.

    Same as normalize_tool_input but for API payloads.
    """
    return normalize_tool_input(tool_name, input_data)


def _strip_trailing_whitespace(s: str) -> str:
    """Strip trailing whitespace from each line."""
    if not isinstance(s, str):
        return s
    return "\n".join(line.rstrip() for line in s.split("\n"))


async def tool_to_api_schema(
    tool: Tool,
    *,
    model: str | None = None,
    defer_loading: bool = False,
    cache_control: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Convert a Tool to API schema format.

    Args:
        tool: The tool to convert
        model: The model being used (for feature detection)
        defer_loading: Mark tool for deferred loading
        cache_control: Cache control settings

    Returns:
        API-compatible tool schema dict
    """
    schema: dict[str, Any] = {
        "name": tool.name,
        "description": tool.description or await tool.get_prompt(),
        "input_schema": tool.get_input_schema(),
    }

    if defer_loading:
        schema["defer_loading"] = True

    if cache_control:
        schema["cache_control"] = cache_control

    return schema


async def tools_to_api_schemas(
    tools: list[Tool],
    *,
    model: str | None = None,
) -> list[dict[str, Any]]:
    """
    Convert multiple tools to API schema format.
    """
    schemas = []
    for tool in tools:
        schema = await tool_to_api_schema(tool, model=model)
        schemas.append(schema)
    return schemas


def build_system_prompt_blocks(
    system_prompt: str,
    *,
    cache_scope: CacheScope | None = None,
) -> list[SystemPromptBlock]:
    """
    Build system prompt blocks for the API.

    Args:
        system_prompt: The system prompt text
        cache_scope: Optional cache scope

    Returns:
        List of system prompt blocks
    """
    if not system_prompt:
        return []

    return [SystemPromptBlock(text=system_prompt, cache_scope=cache_scope)]


def hash_system_prompt(prompt: str) -> str:
    """
    Create a hash of the system prompt for caching.
    """
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def estimate_token_count(text: str) -> int:
    """
    Rough estimation of token count.

    Uses a simple heuristic: ~4 characters per token.
    """
    return len(text) // 4


def format_tool_result(
    tool_use_id: str,
    result: Any,
    *,
    is_error: bool = False,
) -> dict[str, Any]:
    """
    Format a tool result for the API.

    Args:
        tool_use_id: The tool use ID
        result: The tool result
        is_error: Whether this is an error result

    Returns:
        API-formatted tool result
    """
    content: str
    if isinstance(result, str):
        content = result
    elif isinstance(result, dict):
        import json

        content = json.dumps(result)
    else:
        content = str(result)

    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "is_error": is_error,
    }


def create_user_message(content: str | list[dict[str, Any]]) -> dict[str, Any]:
    """Create a user message for the API."""
    return {
        "role": "user",
        "content": content,
    }


def create_assistant_message(content: str | list[dict[str, Any]]) -> dict[str, Any]:
    """Create an assistant message for the API."""
    return {
        "role": "assistant",
        "content": content,
    }


def merge_system_prompts(*prompts: str) -> str:
    """
    Merge multiple system prompts into one.

    Joins non-empty prompts with double newlines.
    """
    return "\n\n".join(p for p in prompts if p)


def count_files_in_directory(path: str, pattern: str = "*") -> int:
    """
    Count files in a directory matching a pattern.

    Uses glob for pattern matching.
    """
    from pathlib import Path

    return len(list(Path(path).glob(pattern)))


def windows_path_to_posix(path: str) -> str:
    """Convert a Windows path to POSIX format."""
    return path.replace("\\", "/")


def posix_path_to_windows(path: str) -> str:
    """Convert a POSIX path to Windows format."""
    return path.replace("/", "\\")
