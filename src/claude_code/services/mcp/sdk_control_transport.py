"""
SDK MCP control transport bridge (CLI ↔ SDK process).

Migrated from: services/mcp/SdkControlTransport.ts

JSON-RPC messages are represented as dicts (parsed JSON objects).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

JSONRPCMessage = dict[str, Any]

SendMcpMessageCallback = Callable[[str, JSONRPCMessage], Awaitable[JSONRPCMessage]]


class SdkControlClientTransport:
    """
    CLI-side transport: sends MCP messages to the SDK process and delivers
    responses back to the client via ``onmessage``.
    """

    def __init__(self, server_name: str, send_mcp_message: SendMcpMessageCallback) -> None:
        self._server_name = server_name
        self._send_mcp_message = send_mcp_message
        self._closed = False
        self.onclose: Callable[[], None] | None = None
        self.onerror: Callable[[Exception], None] | None = None
        self.onmessage: Callable[[JSONRPCMessage], None] | None = None

    async def start(self) -> None:
        """No-op start (parity with TS SDK Transport)."""

    async def send(self, message: JSONRPCMessage) -> None:
        if self._closed:
            raise RuntimeError("Transport is closed")
        response = await self._send_mcp_message(self._server_name, message)
        if self.onmessage:
            self.onmessage(response)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.onclose:
            self.onclose()


class SdkControlServerTransport:
    """
    SDK-side transport: forwards inbound MCP messages to the server and
    passes outbound responses through ``send_mcp_message``.
    """

    def __init__(self, send_mcp_message: Callable[[JSONRPCMessage], None]) -> None:
        self._send_mcp_message = send_mcp_message
        self._closed = False
        self.onclose: Callable[[], None] | None = None
        self.onerror: Callable[[Exception], None] | None = None
        self.onmessage: Callable[[JSONRPCMessage], None] | None = None

    async def start(self) -> None:
        """No-op start."""

    async def send(self, message: JSONRPCMessage) -> None:
        if self._closed:
            raise RuntimeError("Transport is closed")
        self._send_mcp_message(message)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.onclose:
            self.onclose()
