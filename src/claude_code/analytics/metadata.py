"""
Analytics Metadata.

Utilities for handling analytics metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventMetadata:
    """Structured event metadata."""

    # Common fields
    session_id: str = ""
    model: str = ""
    tool_name: str = ""

    # Numeric fields
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    cost_usd: float = 0.0

    # Boolean fields
    success: bool = True
    is_interactive: bool = True

    # Custom fields
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        result: dict[str, Any] = {}

        if self.session_id:
            result["session_id"] = self.session_id
        if self.model:
            result["model"] = self.model
        if self.tool_name:
            result["tool_name"] = self.tool_name

        if self.input_tokens > 0:
            result["input_tokens"] = self.input_tokens
        if self.output_tokens > 0:
            result["output_tokens"] = self.output_tokens
        if self.duration_ms > 0:
            result["duration_ms"] = self.duration_ms
        if self.cost_usd > 0:
            result["cost_usd"] = self.cost_usd

        result["success"] = self.success
        result["is_interactive"] = self.is_interactive

        result.update(self.custom)

        return result


def strip_proto_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    """Strip _PROTO_ prefixed keys from metadata.

    These keys are reserved for PII-tagged proto columns and should
    not be sent to general-access storage backends.

    Returns:
        The input unchanged if no _PROTO_ keys present, otherwise a new dict.
    """
    result: dict[str, Any] | None = None

    for key in list(metadata.keys()):
        if key.startswith("_PROTO_"):
            if result is None:
                result = dict(metadata)
            del result[key]

    return result if result is not None else metadata


# Patterns for detecting sensitive data
FILE_PATH_PATTERN = re.compile(r"[/\\](?:[\w.-]+[/\\])+[\w.-]+")
CODE_PATTERN = re.compile(r"(?:function|class|def|import|const|let|var)\s+\w+")


def sanitize_metadata(
    metadata: dict[str, Any],
    *,
    allow_paths: bool = False,
    allow_code: bool = False,
) -> dict[str, Any]:
    """Sanitize metadata to remove potentially sensitive data.

    Args:
        metadata: The metadata to sanitize
        allow_paths: If True, don't redact file paths
        allow_code: If True, don't redact code snippets

    Returns:
        Sanitized metadata dictionary
    """
    result: dict[str, Any] = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, (bool, int, float)):
            result[key] = value
            continue

        if isinstance(value, str):
            sanitized = value

            # Redact file paths
            if not allow_paths and FILE_PATH_PATTERN.search(value):
                sanitized = "[REDACTED_PATH]"

            # Redact code
            if not allow_code and CODE_PATTERN.search(value):
                sanitized = "[REDACTED_CODE]"

            result[key] = sanitized
            continue

        if isinstance(value, dict):
            result[key] = sanitize_metadata(
                value,
                allow_paths=allow_paths,
                allow_code=allow_code,
            )
            continue

        if isinstance(value, list):
            result[key] = [
                sanitize_metadata({"v": v}, allow_paths=allow_paths, allow_code=allow_code).get("v", v)
                if isinstance(v, (dict, str))
                else v
                for v in value
            ]
            continue

        # Unknown type - convert to string and redact
        result[key] = "[REDACTED]"

    return result


def sanitize_tool_name(tool_name: str) -> str:
    """Sanitize a tool name for analytics.

    Extracts the base tool name, removing any MCP server prefixes.
    """
    # Handle MCP tool names like "mcp__server__tool"
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        if len(parts) >= 3:
            return f"mcp_{parts[-1]}"

    return tool_name
