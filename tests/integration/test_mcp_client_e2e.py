"""End-to-end :class:`McpClient` against a minimal stdio JSON-RPC server."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

from claude_code.services.mcp.client import McpClient, connect_to_server, create_mcp_client
from claude_code.services.mcp.types import (
    McpConnection,
    McpHTTPServerConfig,
    McpStdioServerConfig,
    parse_server_config,
)


def _write_fake_mcp_server(path: Path) -> None:
    path.write_text(
        textwrap.dedent(
            '''
            import json
            import sys

            def reply(req_id, result):
                print(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}), flush=True)

            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                req_id = msg.get("id")
                method = msg.get("method")
                if method == "initialize" and req_id is not None:
                    reply(
                        req_id,
                        {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "fake-mcp", "version": "0.0.1"},
                        },
                    )
                elif method == "tools/list" and req_id is not None:
                    reply(
                        req_id,
                        {
                            "tools": [
                                {
                                    "name": "ping",
                                    "description": "noop",
                                    "inputSchema": {"type": "object"},
                                }
                            ]
                        },
                    )
                elif method == "tools/call" and req_id is not None:
                    reply(
                        req_id,
                        {"content": [{"type": "text", "text": "pong"}]},
                    )
                elif method == "resources/list" and req_id is not None:
                    reply(req_id, {"resources": []})
            '''
        ).lstrip(),
        encoding="utf-8",
    )


@pytest.fixture
def fake_mcp_script(tmp_path: Path) -> Path:
    p = tmp_path / "fake_mcp.py"
    _write_fake_mcp_server(p)
    return p


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_mcp_stdio_connect_and_capabilities(fake_mcp_script: Path) -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=[str(fake_mcp_script)])
    conn = McpConnection(name="fake", config=cfg, scope="user")
    client = McpClient(conn)
    ok = await client.connect()
    assert ok is True
    assert client.is_connected
    assert client.connection.capabilities is not None
    assert client.connection.capabilities.tools is True
    await client.disconnect()
    assert client.connection.status == "disconnected"


@pytest.mark.asyncio
async def test_mcp_list_tools_after_connect(fake_mcp_script: Path) -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=[str(fake_mcp_script)])
    client = await connect_to_server("t", cfg, scope="user")
    tools = await client.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "ping"
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_call_tool_returns_text(fake_mcp_script: Path) -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=[str(fake_mcp_script)])
    client = await connect_to_server("t2", cfg, scope="user")
    out = await client.call_tool("ping", {})
    assert out == "pong"
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_list_resources_empty(fake_mcp_script: Path) -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=[str(fake_mcp_script)])
    client = await connect_to_server("t3", cfg, scope="user")
    res = await client.list_resources()
    assert res == []
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_unsupported_http_transport_returns_false() -> None:
    cfg = McpHTTPServerConfig(type="http", url="http://127.0.0.1:9/mcp")
    client = await create_mcp_client("bad", cfg)
    ok = await client.connect()
    assert ok is False
    assert client.connection.status == "error"
    assert "Unsupported" in (client.connection.error or "")


@pytest.mark.asyncio
async def test_mcp_disconnect_idempotent(fake_mcp_script: Path) -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=[str(fake_mcp_script)])
    client = await connect_to_server("t4", cfg, scope="user")
    await client.disconnect()
    await client.disconnect()
    assert client.connection.status == "disconnected"


@pytest.mark.asyncio
async def test_mcp_list_tools_when_disconnected_returns_empty() -> None:
    cfg = McpStdioServerConfig(command=sys.executable, args=["-c", "pass"])
    conn = McpConnection(name="x", config=cfg, scope="user")
    client = McpClient(conn)
    assert await client.list_tools() == []


def test_parse_server_config_stdio() -> None:
    cfg = parse_server_config({"type": "stdio", "command": "node", "args": ["x.js"]})
    assert isinstance(cfg, McpStdioServerConfig)
    assert cfg.command == "node"
    assert cfg.args == ["x.js"]


def test_parse_server_config_sse() -> None:
    cfg = parse_server_config({"type": "sse", "url": "http://localhost/sse"})
    assert cfg.type == "sse"
    assert cfg.url == "http://localhost/sse"


def test_parse_server_config_defaults_to_stdio() -> None:
    cfg = parse_server_config({})
    assert isinstance(cfg, McpStdioServerConfig)


def test_parse_server_config_ws() -> None:
    cfg = parse_server_config({"type": "ws", "url": "ws://h/ws"})
    assert cfg.type == "ws"


def test_parse_server_config_sdk() -> None:
    cfg = parse_server_config({"type": "sdk", "name": "inproc"})
    assert cfg.type == "sdk"
