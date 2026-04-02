"""Integration tests for MCP-style JSON messaging (serialization parity with client)."""

from __future__ import annotations

import importlib
import json

import pytest

pytestmark = pytest.mark.integration


def test_stdio_server_module_importable() -> None:
    """StdIO transport implementation must be importable from the MCP SDK."""
    stdio_mod = importlib.import_module("mcp.server.stdio")
    assert hasattr(stdio_mod, "stdio_server")
    assert callable(stdio_mod.stdio_server)


def test_stdio_server_is_async_context_manager() -> None:
    from mcp.server.stdio import stdio_server

    assert callable(stdio_server)
    assert getattr(stdio_server, "__wrapped__", None) is not None


@pytest.mark.parametrize(
    "payload",
    [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        },
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "ping", "params": None},
    ],
)
def test_jsonrpc_line_encoding_decoding_roundtrip(payload: dict) -> None:
    """Mirrors claude_code.services.mcp.client.McpClient line protocol."""
    line = json.dumps(payload, separators=(",", ":")) + "\n"
    restored = json.loads(line.strip())
    assert restored["jsonrpc"] == "2.0"
    assert restored["id"] == payload["id"]
    assert restored["method"] == payload["method"]


def test_jsonrpc_message_validate_with_mcp_types() -> None:
    from mcp.types import JSONRPCMessage

    raw = '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"x","arguments":{}}}'
    msg = JSONRPCMessage.model_validate_json(raw)
    dumped = msg.model_dump_json(by_alias=True, exclude_none=True)
    again = JSONRPCMessage.model_validate_json(dumped)
    assert again.root.method == msg.root.method  # type: ignore[attr-defined]


def test_mcp_client_request_shape_matches_encoder() -> None:
    """Ensure the hand-written request dict in the client stays JSON-serializable."""
    from claude_code.services.mcp.client import McpRequest

    req = McpRequest(id=42, method="initialize", params={"capabilities": {}})
    body = {
        "jsonrpc": req.jsonrpc,
        "id": req.id,
        "method": req.method,
        "params": req.params,
    }
    encoded = json.dumps(body) + "\n"
    decoded = json.loads(encoded.strip())
    assert decoded["id"] == 42
    assert decoded["method"] == "initialize"
