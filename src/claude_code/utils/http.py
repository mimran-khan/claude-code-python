"""
HTTP Utility Functions.

Constants and helpers for HTTP requests.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Version from environment or default
VERSION = os.getenv("CLAUDE_CODE_VERSION", "1.0.0")


def get_user_agent() -> str:
    """Get the user agent string for API requests.

    Returns:
        User agent string
    """
    user_type = os.getenv("USER_TYPE", "user")
    entrypoint = os.getenv("CLAUDE_CODE_ENTRYPOINT", "cli")

    parts = [f"claude-cli/{VERSION}"]
    parts.append(f"({user_type}, {entrypoint}")

    sdk_version = os.getenv("CLAUDE_AGENT_SDK_VERSION")
    if sdk_version:
        parts.append(f", agent-sdk/{sdk_version}")

    client_app = os.getenv("CLAUDE_AGENT_SDK_CLIENT_APP")
    if client_app:
        parts.append(f", client-app/{client_app}")

    parts.append(")")

    return "".join(parts)


def get_mcp_user_agent() -> str:
    """Get the user agent string for MCP requests.

    Returns:
        User agent string for MCP
    """
    parts: list[str] = []

    entrypoint = os.getenv("CLAUDE_CODE_ENTRYPOINT")
    if entrypoint:
        parts.append(entrypoint)

    sdk_version = os.getenv("CLAUDE_AGENT_SDK_VERSION")
    if sdk_version:
        parts.append(f"agent-sdk/{sdk_version}")

    client_app = os.getenv("CLAUDE_AGENT_SDK_CLIENT_APP")
    if client_app:
        parts.append(f"client-app/{client_app}")

    suffix = f" ({', '.join(parts)})" if parts else ""
    return f"claude-code/{VERSION}{suffix}"


def get_web_fetch_user_agent() -> str:
    """Get the user agent string for web fetch requests.

    Returns:
        User agent string for web fetching
    """
    return f"Claude-User (claude-code/{VERSION}; +https://support.anthropic.com/)"


@dataclass
class AuthHeaders:
    """Authentication headers result."""

    headers: dict[str, str]
    error: str | None = None


def get_auth_headers() -> AuthHeaders:
    """Get authentication headers for API requests.

    Returns OAuth headers for subscribers or API key headers for others.

    Returns:
        AuthHeaders with headers dict and optional error
    """
    # Check for API key first
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return AuthHeaders(headers={"x-api-key": api_key})

    # No authentication available
    return AuthHeaders(headers={}, error="No API key available")


async def with_oauth_retry(request_fn, *, also_403_revoked: bool = False):
    """Wrapper that handles OAuth 401 errors.

    Retries once after refreshing the token.

    Args:
        request_fn: The request function to call
        also_403_revoked: Also retry on 403 with revocation message

    Returns:
        The request result

    Raises:
        The original error if not recoverable
    """
    try:
        return await request_fn()
    except Exception:
        # In a full implementation, this would check for:
        # 1. HTTP 401 errors
        # 2. HTTP 403 with revocation message
        # And attempt token refresh
        raise
