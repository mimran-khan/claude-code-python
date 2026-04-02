"""
MCP (Model Context Protocol) type definitions.

Provides configuration schemas and types for MCP servers.

Migrated from: services/mcp/types.ts (259 lines)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

# Configuration scope types
ConfigScope = Literal[
    "local",
    "user",
    "project",
    "dynamic",
    "enterprise",
    "claudeai",
    "managed",
]

# Transport types
Transport = Literal["stdio", "sse", "sse-ide", "http", "ws", "sdk"]


class McpOAuthConfig(BaseModel):
    """OAuth configuration for MCP servers."""

    client_id: str | None = None
    callback_port: int | None = None
    auth_server_metadata_url: str | None = None
    xaa: bool | None = None


class McpStdioServerConfig(BaseModel):
    """Configuration for stdio-based MCP server."""

    type: Literal["stdio"] | None = None
    command: str = Field(..., min_length=1)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None


class McpSSEServerConfig(BaseModel):
    """Configuration for SSE-based MCP server."""

    type: Literal["sse"]
    url: str
    headers: dict[str, str] | None = None
    headers_helper: str | None = None
    oauth: McpOAuthConfig | None = None


class McpSSEIDEServerConfig(BaseModel):
    """Configuration for IDE SSE-based MCP server."""

    type: Literal["sse-ide"]
    url: str
    ide_name: str
    ide_running_in_windows: bool | None = None


class McpWebSocketIDEServerConfig(BaseModel):
    """Configuration for IDE WebSocket-based MCP server."""

    type: Literal["ws-ide"]
    url: str
    ide_name: str
    auth_token: str | None = None
    ide_running_in_windows: bool | None = None


class McpHTTPServerConfig(BaseModel):
    """Configuration for HTTP-based MCP server."""

    type: Literal["http"]
    url: str
    headers: dict[str, str] | None = None
    headers_helper: str | None = None
    oauth: McpOAuthConfig | None = None


class McpWebSocketServerConfig(BaseModel):
    """Configuration for WebSocket-based MCP server."""

    type: Literal["ws"]
    url: str
    headers: dict[str, str] | None = None
    headers_helper: str | None = None


class McpSdkServerConfig(BaseModel):
    """Configuration for SDK-based MCP server."""

    type: Literal["sdk"]
    name: str


class McpClaudeAIProxyServerConfig(BaseModel):
    """Configuration for Claude.ai proxy MCP server."""

    type: Literal["claudeai-proxy"]
    url: str
    id: str


# Union type for all MCP server configs
McpServerConfig = (
    McpStdioServerConfig
    | McpSSEServerConfig
    | McpSSEIDEServerConfig
    | McpWebSocketIDEServerConfig
    | McpHTTPServerConfig
    | McpWebSocketServerConfig
    | McpSdkServerConfig
    | McpClaudeAIProxyServerConfig
)


@dataclass
class ScopedMcpServerConfig:
    """MCP server config with scope information."""

    config: McpServerConfig
    scope: ConfigScope
    plugin_source: str | None = None


@dataclass
class ServerCapabilities:
    """Server capabilities from MCP."""

    tools: bool = False
    resources: bool = False
    prompts: bool = False
    experimental: dict[str, Any] | None = None


@dataclass
class ServerInfo:
    """Server info from MCP."""

    name: str
    version: str


@dataclass
class ConnectedMCPServer:
    """A connected MCP server."""

    name: str
    type: Literal["connected"] = "connected"
    capabilities: ServerCapabilities = field(default_factory=ServerCapabilities)
    server_info: ServerInfo | None = None
    instructions: str | None = None
    config: ScopedMcpServerConfig | None = None
    client: Any = None  # MCP Client


@dataclass
class FailedMCPServer:
    """A failed MCP server."""

    name: str
    type: Literal["failed"] = "failed"
    config: ScopedMcpServerConfig | None = None
    error: str | None = None


@dataclass
class NeedsAuthMCPServer:
    """An MCP server that needs authentication."""

    name: str
    type: Literal["needs-auth"] = "needs-auth"
    config: ScopedMcpServerConfig | None = None


@dataclass
class PendingMCPServer:
    """A pending MCP server."""

    name: str
    type: Literal["pending"] = "pending"
    config: ScopedMcpServerConfig | None = None
    reconnect_attempt: int | None = None
    max_reconnect_attempts: int | None = None


@dataclass
class DisabledMCPServer:
    """A disabled MCP server."""

    name: str
    type: Literal["disabled"] = "disabled"
    config: ScopedMcpServerConfig | None = None


# Union type for all MCP server connection states
MCPServerConnection = ConnectedMCPServer | FailedMCPServer | NeedsAuthMCPServer | PendingMCPServer | DisabledMCPServer


@dataclass
class Resource:
    """An MCP resource."""

    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None


@dataclass
class ServerResource:
    """An MCP resource with server info."""

    uri: str
    name: str
    server: str
    description: str | None = None
    mime_type: str | None = None


@dataclass
class SerializedTool:
    """A serialized MCP tool."""

    name: str
    description: str
    input_json_schema: dict[str, Any] | None = None
    is_mcp: bool = False
    original_tool_name: str | None = None


@dataclass
class SerializedClient:
    """A serialized MCP client."""

    name: str
    type: Literal["connected", "failed", "needs-auth", "pending", "disabled"]
    capabilities: ServerCapabilities | None = None


@dataclass
class MCPCliState:
    """CLI state for MCP."""

    clients: list[SerializedClient] = field(default_factory=list)
    configs: dict[str, ScopedMcpServerConfig] = field(default_factory=dict)
    tools: list[SerializedTool] = field(default_factory=list)
    resources: dict[str, list[ServerResource]] = field(default_factory=dict)
    normalized_names: dict[str, str] | None = None
