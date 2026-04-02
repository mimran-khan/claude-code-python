"""Manage MCP servers."""

from .add_command import register_mcp_add_command
from .command import McpCommand
from .xaa_idp_command import register_mcp_xaa_idp_command

__all__ = [
    "McpCommand",
    "register_mcp_add_command",
    "register_mcp_xaa_idp_command",
]
