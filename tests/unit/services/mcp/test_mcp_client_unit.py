"""Unit tests for ``claude_code.services.mcp.client``."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_code.services.mcp.client import (
    McpClient,
    McpRequest,
    McpResponse,
    _to_mcp_response,
    connect_to_server,
    create_mcp_client,
)
from claude_code.services.mcp.transports import JsonRpcResponse
from claude_code.services.mcp.types import (
    McpConnection,
    McpHTTPServerConfig,
    McpResource,
    McpSSEServerConfig,
    McpStdioServerConfig,
    McpTool,
)


def test_mcp_request_dataclass_defaults() -> None:
    r = McpRequest()
    assert r.jsonrpc == "2.0"
    assert r.method == ""


def test_mcp_response_dataclass() -> None:
    r = McpResponse(id=1, result={"a": 1}, error=None)
    assert r.result == {"a": 1}


def test_to_mcp_response_none() -> None:
    assert _to_mcp_response(None) is None


def test_to_mcp_response_maps_fields() -> None:
    raw = JsonRpcResponse(jsonrpc="2.0", id=5, result={"x": 1}, error=None)
    out = _to_mcp_response(raw)
    assert out is not None
    assert out.id == 5
    assert out.result == {"x": 1}


@pytest.mark.asyncio
async def test_create_mcp_client_builds_connection() -> None:
    cfg = McpStdioServerConfig(command="echo", args=["hi"])
    client = await create_mcp_client("srv", cfg, scope="user")
    assert client.connection.name == "srv"
    assert client.connection.scope == "user"
    assert isinstance(client.connection.config, McpStdioServerConfig)


@pytest.mark.asyncio
async def test_connect_to_server_invokes_connect() -> None:
    cfg = McpStdioServerConfig(command="x")
    with patch.object(McpClient, "connect", new_callable=AsyncMock, return_value=True) as m:
        client = await connect_to_server("n", cfg)
        m.assert_awaited_once()
    assert isinstance(client, McpClient)


@pytest.mark.asyncio
async def test_mcp_connect_unsupported_config_sets_error() -> None:
    conn = McpConnection(name="x", config=McpHTTPServerConfig(), scope="user")
    client = McpClient(conn)
    ok = await client.connect()
    assert ok is False
    assert conn.status == "error"
    assert "Unsupported" in (conn.error or "")


@pytest.mark.asyncio
async def test_mcp_connect_initialize_error_closes_transport() -> None:
    cfg = McpStdioServerConfig(command="c")
    conn = McpConnection(name="x", config=cfg, scope="user")
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.connect = AsyncMock()
    mock_transport.send_request = AsyncMock(
        return_value=JsonRpcResponse(jsonrpc="2.0", id=1, result=None, error={"message": "bad"})
    )
    mock_transport.send_notification = AsyncMock()
    mock_transport.aclose = AsyncMock()
    with patch("claude_code.services.mcp.client.StdioJsonRpcTransport", return_value=mock_transport):
        ok = await client.connect()
    assert ok is False
    assert conn.status == "error"
    mock_transport.aclose.assert_awaited()


@pytest.mark.asyncio
async def test_mcp_connect_success_sets_capabilities() -> None:
    cfg = McpStdioServerConfig(command="c")
    conn = McpConnection(name="x", config=cfg, scope="user")
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.connect = AsyncMock()
    mock_transport.send_request = AsyncMock(
        return_value=JsonRpcResponse(
            jsonrpc="2.0",
            id=1,
            result={"capabilities": {"tools": {}, "resources": {}}},
            error=None,
        )
    )
    mock_transport.send_notification = AsyncMock()
    with patch("claude_code.services.mcp.client.StdioJsonRpcTransport", return_value=mock_transport):
        ok = await client.connect()
    assert ok is True
    assert conn.status == "connected"
    assert conn.capabilities is not None
    assert conn.capabilities.tools is True
    assert conn.capabilities.resources is True


@pytest.mark.asyncio
async def test_mcp_connect_sse_transport() -> None:
    cfg = McpSSEServerConfig(url="http://localhost/sse")
    conn = McpConnection(name="s", config=cfg, scope="project")
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.connect = AsyncMock()
    mock_transport.send_request = AsyncMock(
        return_value=JsonRpcResponse(jsonrpc="2.0", id=1, result={"capabilities": {}}, error=None)
    )
    mock_transport.send_notification = AsyncMock()
    with patch("claude_code.services.mcp.client.SseJsonRpcTransport", return_value=mock_transport):
        ok = await client.connect()
    assert ok is True


def test_format_rpc_error_branches() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    client = McpClient(conn)
    assert client._format_rpc_error(None) == "No response from MCP server"
    assert "oops" in client._format_rpc_error(McpResponse(error={"message": "oops"}))
    assert client._format_rpc_error(McpResponse(error={})) == "Unknown error"


@pytest.mark.asyncio
async def test_list_tools_not_connected_returns_empty() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    client = McpClient(conn)
    assert await client.list_tools() == []


@pytest.mark.asyncio
async def test_list_tools_parses_and_caches() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    conn.status = "connected"
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.send_request = AsyncMock(
        return_value=JsonRpcResponse(
            jsonrpc="2.0",
            id=1,
            result={
                "tools": [
                    {"name": "t1", "description": "d", "inputSchema": {"type": "object"}},
                ]
            },
            error=None,
        )
    )
    client._transport = mock_transport
    tools = await client.list_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], McpTool)
    assert tools[0].name == "t1"
    assert conn.tools == tools


@pytest.mark.asyncio
async def test_list_resources_parses_and_caches() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    conn.status = "connected"
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.send_request = AsyncMock(
        return_value=JsonRpcResponse(
            jsonrpc="2.0",
            id=1,
            result={"resources": [{"uri": "u", "name": "n", "description": "d", "mimeType": "text/plain"}]},
            error=None,
        )
    )
    client._transport = mock_transport
    res = await client.list_resources()
    assert len(res) == 1
    assert isinstance(res[0], McpResource)
    assert res[0].uri == "u"


@pytest.mark.asyncio
async def test_call_tool_not_connected_raises() -> None:
    client = McpClient(McpConnection(name="n", config=McpStdioServerConfig(), scope="user"))
    with pytest.raises(RuntimeError, match="Not connected"):
        await client.call_tool("x", {})


@pytest.mark.asyncio
async def test_call_tool_error_raises() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    conn.status = "connected"
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.send_request = AsyncMock(
        return_value=JsonRpcResponse(jsonrpc="2.0", id=1, result=None, error={"message": "fail"})
    )
    client._transport = mock_transport
    with pytest.raises(RuntimeError, match="fail"):
        await client.call_tool("t", {})


@pytest.mark.asyncio
async def test_call_tool_no_response_raises() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    conn.status = "connected"
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.send_request = AsyncMock(return_value=None)
    client._transport = mock_transport
    with pytest.raises(RuntimeError, match="No response"):
        await client.call_tool("t", {})


def test_normalize_tool_result_non_dict() -> None:
    assert McpClient._normalize_tool_result(None) is None
    assert McpClient._normalize_tool_result("x") == "x"


def test_normalize_tool_result_text_blocks() -> None:
    r = {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}
    out = McpClient._normalize_tool_result(r)
    assert out == "a\nb"


def test_normalize_tool_result_single_text() -> None:
    r = {"content": [{"type": "text", "text": "only"}]}
    assert McpClient._normalize_tool_result(r) == "only"


@pytest.mark.asyncio
async def test_read_resource_not_connected() -> None:
    client = McpClient(McpConnection(name="n", config=McpStdioServerConfig(), scope="user"))
    with pytest.raises(RuntimeError, match="Not connected"):
        await client.read_resource("uri")


@pytest.mark.asyncio
async def test_read_resource_success() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    conn.status = "connected"
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.send_request = AsyncMock(
        return_value=JsonRpcResponse(jsonrpc="2.0", id=1, result={"contents": []}, error=None)
    )
    client._transport = mock_transport
    assert await client.read_resource("x") == {"contents": []}


@pytest.mark.asyncio
async def test_rpc_without_transport_returns_none() -> None:
    client = McpClient(McpConnection(name="n", config=McpStdioServerConfig(), scope="user"))
    assert await client._rpc("m", {}) is None


@pytest.mark.asyncio
async def test_send_request_alias_matches_rpc() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.send_request = AsyncMock(return_value=None)
    client._transport = mock_transport
    assert await client._send_request("x", {}) is None


@pytest.mark.asyncio
async def test_disconnect_marks_disconnected() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    conn.status = "connected"
    client = McpClient(conn)
    mock_transport = MagicMock()
    mock_transport.aclose = AsyncMock()
    client._transport = mock_transport
    await client.disconnect()
    assert conn.status == "disconnected"


@pytest.mark.asyncio
async def test_is_connected_property() -> None:
    conn = McpConnection(name="n", config=McpStdioServerConfig(), scope="user")
    client = McpClient(conn)
    assert client.is_connected is False
    conn.status = "connected"
    assert client.is_connected is True
