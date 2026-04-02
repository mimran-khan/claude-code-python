"""
Pre/post tool hooks (permissions, MCP output rewrite).

Migrated from: services/tools/toolHooks.ts (generator skeleton).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, TypeVar

T = TypeVar("T")


async def run_post_tool_use_hooks(
    tool_use_context: Any,
    tool: Any,
    tool_use_id: str,
    message_id: str,
    tool_input: dict[str, Any],
    tool_response: T,
    request_id: str | None,
    mcp_server_type: str,
    mcp_server_base_url: str | None,
) -> AsyncIterator[dict[str, Any]]:
    """Yield hook outcomes; integrate with utils.hooks when ported."""
    _ = (
        tool_use_context,
        tool,
        tool_use_id,
        message_id,
        tool_input,
        tool_response,
        request_id,
        mcp_server_type,
        mcp_server_base_url,
    )
    for _ in []:
        yield {}


async def run_pre_tool_hooks(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_use_context: Any,
) -> AsyncIterator[dict[str, Any]]:
    _ = tool_name, tool_input, tool_use_context
    for _ in []:
        yield {}
