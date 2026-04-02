"""MCP OAuth pseudo-tool factory. Migrated from tools/McpAuthTool/McpAuthTool.ts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlparse

from ..base import Tool, ToolResult, ToolUseContext

McpAuthStatus = Literal["auth_url", "unsupported", "error"]


@dataclass
class McpAuthOutput:
    """Result of MCP authenticate pseudo-tool."""

    status: McpAuthStatus
    message: str
    auth_url: str | None = None


def build_mcp_auth_tool_name(server_name: str) -> str:
    """Build wire name mcp__<server>__authenticate (TS buildMcpToolName parity)."""
    safe = server_name.replace(" ", "_")
    return f"mcp__{safe}__authenticate"


def _mcp_server_base_url(config: Any) -> str | None:
    url = getattr(config, "url", None)
    if not url or not isinstance(url, str):
        return None
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _mcp_oauth_client_id(server_name: str, config: Any) -> str | None:
    cid = getattr(config, "oauth_client_id", None)
    if isinstance(cid, str) and cid.strip():
        return cid.strip()
    safe = "".join(c if c.isalnum() else "_" for c in server_name.upper())
    return os.environ.get(f"MCP_OAUTH_CLIENT_ID_{safe}") or os.environ.get("MCP_OAUTH_CLIENT_ID")


class McpAuthToolStub(Tool[dict[str, Any], dict[str, Any]]):
    """Per-server MCP OAuth helper: discovers AS metadata and returns an authorization URL."""

    def __init__(self, server_name: str, description_text: str) -> None:
        self._server_name = server_name
        self._description_text = description_text

    @property
    def name(self) -> str:
        return build_mcp_auth_tool_name(self._server_name)

    async def description(self) -> str:
        return self._description_text

    async def prompt(self) -> str:
        return self._description_text

    def get_input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"},
                "auth_url": {"type": "string"},
            },
            "required": ["status", "message"],
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = input, context
        from ...services.mcp.auth import (
            build_authorization_url,
            discover_oauth_metadata,
            generate_code_challenge,
            get_oauth_flow_manager,
        )
        from ...services.mcp.config import get_mcp_servers

        servers = get_mcp_servers()
        cfg = servers.get(self._server_name)
        if cfg is None:
            return ToolResult(
                success=True,
                output={
                    "status": "error",
                    "message": f"Unknown MCP server {self._server_name!r}. Use /mcp list to see configured servers.",
                },
            )

        base = _mcp_server_base_url(cfg)
        if not base:
            return ToolResult(
                success=True,
                output={
                    "status": "unsupported",
                    "message": "OAuth applies to URL-based MCP servers (sse, http, ws). Stdio servers use env/credentials instead.",
                },
            )

        client_id = _mcp_oauth_client_id(self._server_name, cfg)
        if not client_id:
            return ToolResult(
                success=True,
                output={
                    "status": "error",
                    "message": "Set oauthClientId (or clientId) in mcpServers config, or set MCP_OAUTH_CLIENT_ID.",
                },
            )

        meta = await discover_oauth_metadata(base)
        if meta is None or not meta.authorization_endpoint:
            return ToolResult(
                success=True,
                output={
                    "status": "error",
                    "message": f"No OAuth metadata found at {base} (/.well-known/oauth-authorization-server or openid-configuration).",
                },
            )

        redirect_uri = os.environ.get("MCP_OAUTH_REDIRECT_URI", "http://127.0.0.1:19199/mcp/oauth/callback")
        mgr = get_oauth_flow_manager()
        flow = mgr.start_flow(self._server_name, redirect_uri)
        challenge = generate_code_challenge(flow.code_verifier)
        scope = " ".join(meta.scopes_supported) if meta.scopes_supported else ""
        auth_url = build_authorization_url(
            meta.authorization_endpoint,
            client_id,
            redirect_uri,
            flow.state,
            challenge,
            scope,
        )
        return ToolResult(
            success=True,
            output={
                "status": "auth_url",
                "message": "Open this URL in a browser to authorize the MCP server, then complete the code exchange if your host supports it.",
                "auth_url": auth_url,
            },
        )


def create_mcp_auth_tool_stub(server_name: str, location: str) -> McpAuthToolStub:
    """Factory mirroring createMcpAuthTool (simplified)."""
    description = (
        f"The `{server_name}` MCP server ({location}) is installed but requires authentication. "
        "Call this tool to start the OAuth flow — you'll receive an authorization URL to share with the user."
    )
    return McpAuthToolStub(server_name, description)
