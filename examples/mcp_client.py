#!/usr/bin/env python3
"""
MCP client lifecycle: connect, list tools, call a tool, disconnect.

Uses a tiny generated stub server (stdio) so the example runs without installing
extra MCP servers.

Run:
  python examples/mcp_client.py
"""

from __future__ import annotations

import asyncio
import contextlib
import sys
import tempfile
from pathlib import Path

from _path_setup import ensure_src_on_path

ensure_src_on_path()

from claude_code.services.mcp.client import connect_to_server
from claude_code.services.mcp.types import McpStdioServerConfig


def _write_stub_server(path: Path) -> None:
    """Minimal MCP-over-stdio server (newline-delimited JSON-RPC)."""
    script = """
import json
import sys


def _send(obj):
    sys.stdout.write(json.dumps(obj) + "\\n")
    sys.stdout.flush()


for _line in sys.stdin:
    line = _line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        continue
    if msg.get("method") == "notifications/initialized":
        continue
    if "id" not in msg:
        continue
    mid = msg["id"]
    method = msg.get("method")
    if method == "initialize":
        _send({
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "example-stub", "version": "0.0.1"},
            },
        })
    elif method == "tools/list":
        _send({
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "tools": [
                    {
                        "name": "stub_hello",
                        "description": "Returns a short greeting (example tool).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            "required": [],
                        },
                    }
                ]
            },
        })
    elif method == "tools/call":
        _send({
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "content": [{"type": "text", "text": "Hello from stub MCP — connection OK."}],
            },
        })
    else:
        _send({
            "jsonrpc": "2.0",
            "id": mid,
            "error": {"code": -32601, "message": "unknown method: " + repr(method)},
        })
"""
    path.write_text(script.lstrip("\n"), encoding="utf-8")


async def main() -> int:
    stub_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix="_mcp_stub.py", delete=False) as tmp:
            stub_path = Path(tmp.name)
        _write_stub_server(stub_path)

        config = McpStdioServerConfig(
            type="stdio",
            command=sys.executable,
            args=[str(stub_path)],
        )

        client = await connect_to_server(name="example-stub", config=config, scope="dynamic")

        if not client.is_connected:
            err = client.connection.error or "unknown error"
            print(f"Failed to connect to stub MCP server: {err}", file=sys.stderr)
            return 1

        try:
            tools = await client.list_tools()
            print(f"Listed {len(tools)} tool(s) from server:")
            for t in tools:
                desc = t.description[:80] if t.description else ""
                print(f"  - {t.name}: {desc!r}")

            if not tools:
                print("No tools returned (unexpected for stub).", file=sys.stderr)
                return 1

            first = tools[0].name
            out = await client.call_tool(first, {"name": "developer"})
            print(f"\nTool {first!r} result:\n{out}")
        finally:
            await client.disconnect()

    except (OSError, RuntimeError, TimeoutError) as exc:
        print(f"MCP example failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if stub_path is not None:
            with contextlib.suppress(OSError):
                stub_path.unlink(missing_ok=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
