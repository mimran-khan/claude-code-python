"""
MCP stdio server entry (tools surface).

Migrated from: entrypoints/mcp.ts

Exposes built-in Claude Code tools over the Model Context Protocol (stdio).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Callable
from typing import Any, cast

import mcp.types as mcp_types
from mcp.server import InitializationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import ServerCapabilities, TextContent, Tool, ToolsCapability

from ..core.tool import Tool as ClaudeTool
from ..core.tool import (
    ToolUseContext,
    ValidationResult,
    get_empty_tool_permission_context,
)
from ..core.tools_registry import get_tools

logger = logging.getLogger(__name__)

CLAUDE_CODE_MCP_SERVER_NAME = "claude-code-python"


def _tool_input_schema(tool: ClaudeTool) -> dict[str, Any]:
    schema = getattr(tool, "input_schema", None)
    if isinstance(schema, dict) and schema:
        return schema
    return {"type": "object", "properties": {}, "additionalProperties": True}


def _claude_tools_to_mcp(tools: list[ClaudeTool]) -> list[Tool]:
    return [
        Tool(
            name=t.name,
            description=(getattr(t, "description", None) or "").strip() or f"Tool {t.name}",
            inputSchema=_tool_input_schema(t),
        )
        for t in tools
    ]


async def _run_validation(
    tool: ClaudeTool,
    args: dict[str, Any],
    ctx: ToolUseContext,
) -> str | None:
    """Return error message if validation fails, else None."""
    validate_fn = cast(Callable[..., Any], tool.validate_input)
    try:
        try:
            raw = validate_fn(args, ctx)
        except TypeError:
            raw = validate_fn(args)
    except Exception as exc:  # noqa: BLE001
        return str(exc)

    if asyncio.iscoroutine(raw):
        raw = await raw

    if raw is None:
        return None

    if isinstance(raw, ValidationResult):
        return None if raw.result else (raw.message or "Validation failed")

    valid = getattr(raw, "valid", None)
    if valid is False:
        return getattr(raw, "message", None) or "Validation failed"

    return None


def _tool_result_to_text(result: Any) -> str:
    data = getattr(result, "data", result)
    if isinstance(data, (dict, list)):
        try:
            return json.dumps(data, indent=2, default=str)
        except TypeError:
            return str(data)
    return str(data)


def _tools_with_call_interface(tools: list[ClaudeTool]) -> list[ClaudeTool]:
    """Keep only tools that implement the ``core.tool.Tool.call`` API (MCP dispatch)."""
    return [t for t in tools if callable(getattr(t, "call", None))]


def create_claude_code_mcp_server(*, cwd: str) -> Server:
    """Build MCP server listing and dispatching built-in tools for ``cwd``."""
    permission_ctx = get_empty_tool_permission_context()
    tools = _tools_with_call_interface(get_tools(permission_ctx))
    if not tools:
        logger.warning(
            "mcp_no_callable_tools",
            extra={"hint": "Registry tools must expose async call() on core.tool.Tool"},
        )
    by_name: dict[str, ClaudeTool] = {t.name: t for t in tools}

    server = Server(CLAUDE_CODE_MCP_SERVER_NAME)

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return _claude_tools_to_mcp(tools)

    @server.call_tool()
    async def _call_tool(
        name: str,
        arguments: dict[str, Any] | None,
    ) -> list[mcp_types.ContentBlock]:
        tool = by_name.get(name)
        if tool is None:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown tool {name!r}. Use list_tools for available tools.",
                )
            ]

        args = dict(arguments or {})
        ctx = ToolUseContext(options={"cwd": cwd, "mcp_stdio": True})
        err = await _run_validation(tool, args, ctx)
        if err:
            return [TextContent(type="text", text=err)]
        try:
            out = await tool.call(args, ctx, None)
        except TypeError:
            # Some tools use a two-arg call without progress callback
            try:
                out = await tool.call(args, ctx)
            except Exception as exc:  # noqa: BLE001
                return [TextContent(type="text", text=f"Tool error: {exc}")]
        except Exception as exc:  # noqa: BLE001
            return [TextContent(type="text", text=f"Tool error: {exc}")]

        return [TextContent(type="text", text=_tool_result_to_text(out))]

    return server


async def start_mcp_server(cwd: str, debug: bool = False, verbose: bool = False) -> None:
    """
    Start MCP server on stdio, advertising and executing built-in Claude Code tools.

    The host working directory is passed to tools via ``ToolUseContext.options['cwd']``.
    """
    os.chdir(cwd)
    if debug or verbose:
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    logger.info("mcp_server_starting", extra={"cwd": cwd})

    server = create_claude_code_mcp_server(cwd=cwd)
    init = InitializationOptions(
        server_name=CLAUDE_CODE_MCP_SERVER_NAME,
        server_version="0.1.0",
        capabilities=ServerCapabilities(tools=ToolsCapability()),
    )
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            init,
            raise_exceptions=False,
        )


def main() -> None:
    """Console entrypoint for ``claude-code-mcp`` (stdio MCP server)."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Code MCP server (stdio) — built-in tools over Model Context Protocol",
    )
    parser.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="Working directory passed to tools (default: current directory)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable INFO logging",
    )
    args = parser.parse_args()
    asyncio.run(start_mcp_server(cwd=args.cwd, debug=args.debug, verbose=args.verbose))
