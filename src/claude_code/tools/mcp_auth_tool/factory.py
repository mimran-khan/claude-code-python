"""Factory entry points for MCP OAuth pseudo-tools."""

from __future__ import annotations

from ...mcp.types import ScopedMcpServerConfig
from .mcp_auth_tool import build_mcp_auth_tool_name, create_mcp_auth_tool_stub


def build_mcp_authenticate_tool_name(server_name: str) -> str:
    return build_mcp_auth_tool_name(server_name)


def create_mcp_auth_tool(
    server_name: str,
    location: str,
    _config: ScopedMcpServerConfig | None = None,
):
    _ = _config
    return create_mcp_auth_tool_stub(server_name, location)
