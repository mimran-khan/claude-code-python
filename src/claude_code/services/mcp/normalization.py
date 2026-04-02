"""
MCP name normalization utilities.

Normalize server names for API compatibility.

Migrated from: services/mcp/normalization.ts
"""

from __future__ import annotations

import re

# Claude.ai server name prefix
CLAUDEAI_SERVER_PREFIX = "claude.ai "


def normalize_name_for_mcp(name: str) -> str:
    """
    Normalize server names to be compatible with API pattern.

    Pattern: ^[a-zA-Z0-9_-]{1,64}$

    Replaces invalid characters (including dots and spaces) with underscores.
    For claude.ai servers, also collapses consecutive underscores and
    strips leading/trailing underscores.

    Args:
        name: Server name to normalize

    Returns:
        Normalized name
    """
    # Replace invalid characters with underscore
    normalized = re.sub(r"[^a-zA-Z0-9_-]", "_", name)

    # For claude.ai servers, clean up underscores
    if name.startswith(CLAUDEAI_SERVER_PREFIX):
        normalized = re.sub(r"_+", "_", normalized)
        normalized = normalized.strip("_")

    return normalized


def is_valid_mcp_name(name: str) -> bool:
    """
    Check if a name is a valid MCP server name.

    Args:
        name: Name to check

    Returns:
        True if valid
    """
    return bool(re.match(r"^[a-zA-Z0-9_-]{1,64}$", name))


def sanitize_tool_name(server_name: str, tool_name: str) -> str:
    """
    Create a full tool name from server and tool names.

    Format: {server}__{tool}

    Args:
        server_name: MCP server name
        tool_name: Tool name

    Returns:
        Full tool name
    """
    normalized_server = normalize_name_for_mcp(server_name)
    normalized_tool = normalize_name_for_mcp(tool_name)
    return f"{normalized_server}__{normalized_tool}"


def parse_tool_name(full_name: str) -> tuple[str, str]:
    """
    Parse a full tool name into server and tool components.

    Args:
        full_name: Full tool name (server__tool)

    Returns:
        Tuple of (server_name, tool_name)
    """
    if "__" in full_name:
        parts = full_name.split("__", 1)
        return parts[0], parts[1]
    return "", full_name
