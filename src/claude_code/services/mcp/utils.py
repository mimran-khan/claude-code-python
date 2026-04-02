"""
MCP utility functions.

Common utilities for MCP operations.

Migrated from: services/mcp/utils.ts + mcpStringUtils.ts
"""

from __future__ import annotations

import re
from urllib.parse import urlparse


def get_logging_safe_mcp_base_url(url: str) -> str:
    """
    Get a URL safe for logging (without credentials).

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL
    """
    try:
        parsed = urlparse(url)
        # Remove username/password
        if parsed.username or parsed.password:
            return f"{parsed.scheme}://{parsed.hostname}{':' + str(parsed.port) if parsed.port else ''}{parsed.path}"
        return url
    except Exception:
        return "[invalid-url]"


def extract_server_name_from_url(url: str) -> str:
    """
    Extract a server name from a URL.

    Args:
        url: Server URL

    Returns:
        Extracted name or fallback
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        # Remove common prefixes
        name = hostname.replace("www.", "")

        # Use first segment
        name = name.split(".")[0]

        # Sanitize
        name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)

        return name or "mcp-server"
    except Exception:
        return "mcp-server"


def format_mcp_error(error: Exception) -> str:
    """
    Format an MCP error for display.

    Args:
        error: The exception

    Returns:
        Formatted error message
    """
    message = str(error)

    # Truncate long messages
    if len(message) > 200:
        message = message[:200] + "..."

    return f"MCP Error: {message}"


def is_mcp_server_url(url: str) -> bool:
    """
    Check if a URL looks like an MCP server URL.

    Args:
        url: URL to check

    Returns:
        True if likely an MCP server
    """
    try:
        parsed = urlparse(url)

        # Must have scheme and host
        if not parsed.scheme or not parsed.hostname:
            return False

        # Check for common MCP patterns
        path = parsed.path.lower()
        return "mcp" in path or "sse" in path or path.endswith("/messages")
    except Exception:
        return False


def truncate_mcp_output(output: str, max_length: int = 10000) -> str:
    """
    Truncate MCP tool output if too long.

    Args:
        output: Output to truncate
        max_length: Maximum length

    Returns:
        Truncated output
    """
    if len(output) <= max_length:
        return output

    # Keep first and last parts
    keep_each = (max_length - 50) // 2
    truncated = output[:keep_each] + "\n\n... [truncated] ...\n\n" + output[-keep_each:]
    return truncated
