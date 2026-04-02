"""
MCP client.

Client for communicating with MCP servers.

Migrated from: services/mcp/client.ts
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any

from .transports import (
    JsonRpcResponse,
    SseJsonRpcTransport,
    StdioJsonRpcTransport,
)
from .types import (
    ConfigScope,
    McpConnection,
    McpResource,
    McpServerCapabilities,
    McpServerConfig,
    McpSSEServerConfig,
    McpStdioServerConfig,
    McpTool,
)


@dataclass
class McpRequest:
    """An MCP JSON-RPC request."""

    jsonrpc: str = "2.0"
    id: int = 0
    method: str = ""
    params: dict[str, Any] | None = None


@dataclass
class McpResponse:
    """JSON-RPC 2.0 response wrapper used after transport decode.

    Attributes:
        jsonrpc: Protocol version, always ``2.0``.
        id: Matches the request id when present.
        result: Success payload, or None if ``error`` is set.
        error: Error object ``{message, ...}`` when the call failed.
    """

    jsonrpc: str = "2.0"
    id: int | str | None = 0
    result: Any = None
    error: dict[str, Any] | None = None


class McpClient:
    """Stateful MCP session over stdio or SSE.

    Holds a :class:`~claude_code.services.mcp.types.McpConnection`, lazily
    creates a transport on :meth:`connect`, and routes JSON-RPC through
    :meth:`_rpc`. Use :func:`connect_to_server` for a one-shot connect helper.

    Attributes:
        connection: Live connection state, capabilities, and cached tool/resource
            lists updated by list/call methods.
    """

    def __init__(self, connection: McpConnection) -> None:
        """Attach a connection descriptor; transport is created in :meth:`connect`.

        Args:
            connection: Server name, config (stdio or SSE), and scope.
        """
        self.connection = connection
        self._transport: StdioJsonRpcTransport | SseJsonRpcTransport | None = None

    @property
    def is_connected(self) -> bool:
        """Whether :attr:`connection.status` is ``connected``."""

        return self.connection.status == "connected"

    async def connect(self) -> bool:
        """Open transport, send ``initialize``, send ``initialized``, probe capabilities.

        On failure sets :attr:`connection.status` to ``error`` and stores a
        message in :attr:`connection.error`.

        Returns:
            True if the handshake completed and capabilities were parsed; False
            if the transport is unsupported, RPC fails, or any exception occurs
            (see :attr:`connection.error`).
        """
        config = self.connection.config

        try:
            if isinstance(config, McpStdioServerConfig):
                transport: StdioJsonRpcTransport | SseJsonRpcTransport = StdioJsonRpcTransport(config)
            elif isinstance(config, McpSSEServerConfig):
                transport = SseJsonRpcTransport(config)
            else:
                self.connection.status = "error"
                self.connection.error = "Unsupported transport type (use stdio or sse)"
                return False

            self.connection.status = "connecting"
            self._transport = transport
            await transport.connect()

            response = await self._rpc(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {
                        "name": "claude-code-python",
                        "version": "0.1.0",
                    },
                    "capabilities": {},
                },
            )

            if response is None or response.error:
                self.connection.status = "error"
                self.connection.error = self._format_rpc_error(response)
                await self._safe_close_transport()
                return False

            await self._transport.send_notification("notifications/initialized", {})

            self.connection.status = "connected"
            if response.result:
                caps = response.result.get("capabilities", {})
                self.connection.capabilities = McpServerCapabilities(
                    tools="tools" in caps,
                    resources="resources" in caps,
                    prompts="prompts" in caps,
                    sampling="sampling" in caps,
                )
            return True

        except Exception as e:
            self.connection.status = "error"
            self.connection.error = str(e)
            await self._safe_close_transport()
            return False

    async def _safe_close_transport(self) -> None:
        """Close and clear the active transport, swallowing errors."""
        if self._transport:
            with contextlib.suppress(Exception):
                await self._transport.aclose()
            self._transport = None

    def _format_rpc_error(self, response: McpResponse | None) -> str:
        """Human-readable error string for logging or :attr:`connection.error`."""
        if response is None:
            return "No response from MCP server"
        if response.error:
            return str(response.error.get("message", response.error))
        return "Unknown error"

    async def disconnect(self) -> None:
        """Close the transport and mark the connection ``disconnected``."""
        await self._safe_close_transport()
        self.connection.status = "disconnected"

    async def list_tools(self) -> list[McpTool]:
        """Call ``tools/list`` and cache results on :attr:`connection.tools`.

        Returns:
            Parsed tools, or an empty list if not connected or the RPC fails.
        """
        if not self.is_connected:
            return []

        response = await self._rpc("tools/list", {})

        if response and not response.error and response.result:
            tools = []
            for tool_data in response.result.get("tools", []):
                tools.append(
                    McpTool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        input_schema=tool_data.get("inputSchema", {}),
                    )
                )
            self.connection.tools = tools
            return tools

        return []

    async def list_resources(self) -> list[McpResource]:
        """Call ``resources/list`` and cache on :attr:`connection.resources`.

        Returns:
            Parsed resources, or an empty list if not connected or the RPC fails.
        """
        if not self.is_connected:
            return []

        response = await self._rpc("resources/list", {})

        if response and not response.error and response.result:
            resources = []
            for res_data in response.result.get("resources", []):
                resources.append(
                    McpResource(
                        uri=res_data.get("uri", ""),
                        name=res_data.get("name", ""),
                        description=res_data.get("description", ""),
                        mime_type=res_data.get("mimeType"),
                    )
                )
            self.connection.resources = resources
            return resources

        return []

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Invoke ``tools/call`` and normalize text content when present.

        Args:
            tool_name: Registered tool name from ``tools/list``.
            arguments: JSON-serializable tool arguments.

        Returns:
            For typical MCP tool results, concatenated text blocks; otherwise
            the raw ``result`` dict or value from :meth:`_normalize_tool_result`.

        Raises:
            RuntimeError: If not connected, the request returns no response, or
                the server returns a JSON-RPC error.
        """
        if not self.is_connected or not self._transport:
            raise RuntimeError("Not connected")

        response = await self._rpc(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )

        if response is None:
            raise RuntimeError("No response from tools/call")

        if response.error:
            raise RuntimeError(str(response.error.get("message", response.error)))

        return self._normalize_tool_result(response.result)

    @staticmethod
    def _normalize_tool_result(result: Any) -> Any:
        """Extract text from CallToolResult-style ``content`` arrays when helpful.

        Args:
            result: Raw ``tools/call`` result (dict or other).

        Returns:
            Joined text if ``content`` holds ``type: text`` blocks; else
            ``result`` unchanged.
        """
        if not isinstance(result, dict):
            return result
        content = result.get("content")
        if isinstance(content, list) and content:
            texts: list[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(str(block.get("text", "")))
            if texts:
                return "\n".join(texts) if len(texts) > 1 else texts[0]
        return result

    async def read_resource(self, uri: str) -> Any:
        """
        Fetch a resource via ``resources/read``.

        Args:
            uri: Resource URI from ``resources/list``.

        Returns:
            The ``result`` field on success, or None if the response is missing.

        Raises:
            RuntimeError: If not connected or the server returns an error.
        """
        if not self.is_connected:
            raise RuntimeError("Not connected")

        response = await self._rpc(
            "resources/read",
            {
                "uri": uri,
            },
        )

        if response and response.error:
            raise RuntimeError(str(response.error.get("message", response.error)))

        return response.result if response else None

    async def _rpc(self, method: str, params: dict[str, Any]) -> McpResponse | None:
        """Send a JSON-RPC request through the active transport.

        Args:
            method: MCP method name.
            params: Request parameters object.

        Returns:
            Parsed :class:`McpResponse`, or None if no transport is available.
        """
        if not self._transport:
            return None
        raw = await self._transport.send_request(method, params)
        return _to_mcp_response(raw)

    async def _send_request(
        self,
        method: str,
        params: dict[str, Any],
    ) -> McpResponse | None:
        """Legacy alias for :meth:`_rpc` (tests and older callers).

        Args:
            method: JSON-RPC method.
            params: Request body.

        Returns:
            Same as :meth:`_rpc`.
        """
        return await self._rpc(method, params)


def _to_mcp_response(raw: JsonRpcResponse | None) -> McpResponse | None:
    """Map transport-layer :class:`~claude_code.services.mcp.transports.JsonRpcResponse` to :class:`McpResponse`."""
    if raw is None:
        return None
    return McpResponse(
        jsonrpc=raw.jsonrpc,
        id=raw.id,
        result=raw.result,
        error=raw.error,
    )


async def create_mcp_client(
    name: str,
    config: McpServerConfig,
    scope: ConfigScope = "user",
) -> McpClient:
    """
    Build a client without connecting.

    Args:
        name: Display name for the connection.
        config: Stdio or SSE server configuration.
        scope: Config scope label (e.g. ``user``).

    Returns:
        Unconnected :class:`McpClient` wrapping a new :class:`~claude_code.services.mcp.types.McpConnection`.
    """
    connection = McpConnection(
        name=name,
        config=config,
        scope=scope,
    )
    return McpClient(connection)


async def connect_to_server(
    name: str,
    config: McpServerConfig,
    scope: ConfigScope = "user",
) -> McpClient:
    """
    Create a client and await :meth:`McpClient.connect`.

    Args:
        name: Display name for the connection.
        config: Stdio or SSE server configuration.
        scope: Config scope label.

    Returns:
        The same client instance after connect; check :attr:`McpClient.is_connected`
        if the handshake may have failed.
    """
    client = await create_mcp_client(name, config, scope)
    await client.connect()
    return client


# Alias for callers expecting PascalCase ``MCPClient`` (TypeScript parity).
MCPClient = McpClient
