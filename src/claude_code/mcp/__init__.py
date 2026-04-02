"""
Model Context Protocol (MCP) support for Claude Code.

This package provides types and utilities for working with MCP servers.
"""

from .types import (
    ConfigScope,
    ConnectedMCPServer,
    DisabledMCPServer,
    FailedMCPServer,
    MCPCliState,
    McpHTTPServerConfig,
    McpServerConfig,
    MCPServerConnection,
    McpSSEServerConfig,
    McpStdioServerConfig,
    NeedsAuthMCPServer,
    PendingMCPServer,
    ScopedMcpServerConfig,
    SerializedClient,
    SerializedTool,
    ServerResource,
    Transport,
)

__all__ = [
    "ConfigScope",
    "Transport",
    "McpServerConfig",
    "McpStdioServerConfig",
    "McpSSEServerConfig",
    "McpHTTPServerConfig",
    "ScopedMcpServerConfig",
    "ConnectedMCPServer",
    "FailedMCPServer",
    "NeedsAuthMCPServer",
    "PendingMCPServer",
    "DisabledMCPServer",
    "MCPServerConnection",
    "ServerResource",
    "SerializedTool",
    "SerializedClient",
    "MCPCliState",
]
