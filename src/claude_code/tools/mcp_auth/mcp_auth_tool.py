"""
Shim module: ``mcp_auth`` package exposes the same API as ``tools.mcp_auth_tool``.

The real implementation lives in ``claude_code.tools.mcp_auth_tool``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..mcp_auth_tool.mcp_auth_tool import (
    McpAuthOutput,
    build_mcp_auth_tool_name,
    create_mcp_auth_tool_stub,
)


@dataclass
class McpAuthInput:
    """Placeholder input for MCP authenticate pseudo-tool."""

    pass


def build_mcp_tool_name(server_name: str) -> str:
    return build_mcp_auth_tool_name(server_name)


def create_mcp_auth_tool(server_name: str, location: str):
    return create_mcp_auth_tool_stub(server_name, location)


__all__ = [
    "McpAuthInput",
    "McpAuthOutput",
    "build_mcp_tool_name",
    "create_mcp_auth_tool",
]
