"""
MCP types.

Type definitions for MCP servers and connections.

Migrated from: services/mcp/types.ts (259 lines)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# Configuration scope
ConfigScope = Literal["local", "user", "project", "dynamic", "enterprise", "claudeai", "managed"]

# Transport types
Transport = Literal["stdio", "sse", "sse-ide", "http", "ws", "sdk"]


@dataclass
class McpStdioServerConfig:
    """Stdio server configuration."""

    type: Literal["stdio"] = "stdio"
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class McpSSEServerConfig:
    """SSE server configuration."""

    type: Literal["sse"] = "sse"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    headers_helper: str | None = None
    oauth_client_id: str | None = None


@dataclass
class McpHTTPServerConfig:
    """HTTP server configuration."""

    type: Literal["http"] = "http"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    headers_helper: str | None = None
    oauth_client_id: str | None = None


@dataclass
class McpWebSocketServerConfig:
    """WebSocket server configuration."""

    type: Literal["ws"] = "ws"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    oauth_client_id: str | None = None


@dataclass
class McpSdkServerConfig:
    """SDK server configuration (in-process)."""

    type: Literal["sdk"] = "sdk"
    name: str = ""


# Union of all server config types

McpServerConfig = (
    McpStdioServerConfig | McpSSEServerConfig | McpHTTPServerConfig | McpWebSocketServerConfig | McpSdkServerConfig
)


@dataclass
class McpTool:
    """An MCP tool definition."""

    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class McpResource:
    """An MCP resource definition."""

    uri: str
    name: str
    description: str = ""
    mime_type: str | None = None


@dataclass
class McpServerCapabilities:
    """Server capabilities."""

    tools: bool = False
    resources: bool = False
    prompts: bool = False
    sampling: bool = False


@dataclass
class McpConnection:
    """An active MCP connection."""

    name: str
    config: McpServerConfig
    scope: ConfigScope
    status: Literal["connecting", "connected", "disconnected", "error"] = "disconnected"
    error: str | None = None
    tools: list[McpTool] = field(default_factory=list)
    resources: list[McpResource] = field(default_factory=list)
    capabilities: McpServerCapabilities | None = None


def parse_server_config(data: dict[str, Any]) -> McpServerConfig:
    """
    Parse a server config from a dict.

    Args:
        data: Configuration dictionary

    Returns:
        Typed server config
    """
    server_type = data.get("type", "stdio")

    if server_type == "stdio":
        return McpStdioServerConfig(
            type="stdio",
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
        )

    oauth_cid = data.get("oauthClientId") or data.get("clientId")

    if server_type == "sse":
        return McpSSEServerConfig(
            type="sse",
            url=data.get("url", ""),
            headers=data.get("headers", {}),
            headers_helper=data.get("headersHelper"),
            oauth_client_id=oauth_cid,
        )

    if server_type == "http":
        return McpHTTPServerConfig(
            type="http",
            url=data.get("url", ""),
            headers=data.get("headers", {}),
            headers_helper=data.get("headersHelper"),
            oauth_client_id=oauth_cid,
        )

    if server_type == "ws":
        return McpWebSocketServerConfig(
            type="ws",
            url=data.get("url", ""),
            headers=data.get("headers", {}),
            oauth_client_id=oauth_cid,
        )

    if server_type == "sdk":
        return McpSdkServerConfig(
            type="sdk",
            name=data.get("name", ""),
        )

    # Default to stdio
    return McpStdioServerConfig()
