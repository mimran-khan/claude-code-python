"""
Computer-use MCP server (stdio) for tool listing and subprocess entrypoint.

Migrated from: utils/computerUse/mcpServer.ts
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import mcp.types as mcp_types
from mcp.server import InitializationOptions, Server
from mcp.server.models import ServerCapabilities
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, ToolsCapability

from ..debug import log_for_debugging
from .app_names import filter_apps_for_description
from .common import COMPUTER_USE_MCP_SERVER_NAME, get_cli_cu_capabilities
from .gates import get_chicago_coordinate_mode
from .host_adapter import get_computer_use_host_adapter

APP_ENUM_TIMEOUT_S = 1.0

_JSON_OBJECT = {"type": "object", "properties": {}, "additionalProperties": True}


def build_computer_use_tools(
    capabilities: dict[str, str],
    coordinate_mode: str,
    installed_app_names: list[str] | None = None,
) -> list[Tool]:
    cap_blob = ", ".join(f"{k}={v}" for k, v in sorted(capabilities.items()))
    apps_line = ""
    if installed_app_names:
        apps_line = "\n\nAvailable applications (sample): " + ", ".join(installed_app_names)

    def tool(name: str, description: str) -> Tool:
        return Tool(name=name, description=description + apps_line, inputSchema=dict(_JSON_OBJECT))

    req = f"Request desktop automation access. Mode: {coordinate_mode}. {cap_blob}."
    return [
        tool("request_access", req),
        tool("list_granted_applications", "List applications the user has granted for this session."),
        tool("revoke_application_access", "Revoke a previously granted application."),
        tool("screenshot", "Capture the display (respecting allowlisted applications)."),
        tool("mouse_move", "Move the mouse pointer."),
        tool("left_click", "Left click at coordinates."),
        tool("right_click", "Right click at coordinates."),
        tool("middle_click", "Middle click at coordinates."),
        tool("double_click", "Double left click."),
        tool("triple_click", "Triple left click."),
        tool("left_click_drag", "Drag with the left mouse button."),
        tool("scroll", "Scroll at coordinates."),
        tool("key", "Press a key combination (xdotool-style, e.g. ctrl+c)."),
        tool("hold_key", "Hold keys for a duration in milliseconds."),
        tool("type", "Type Unicode text (optionally via clipboard)."),
        tool("cursor_position", "Return current cursor coordinates."),
        tool("open_application", "Open an application by bundle id / app id."),
        tool("wait", "Wait for a duration."),
    ]


async def try_get_installed_app_names() -> list[str] | None:
    adapter = get_computer_use_host_adapter()
    try:
        installed = await asyncio.wait_for(
            adapter.executor.listInstalledApps(),
            timeout=APP_ENUM_TIMEOUT_S,
        )
    except TimeoutError:
        log_for_debugging(
            f"[Computer Use MCP] app enumeration exceeded {APP_ENUM_TIMEOUT_S}s; tool description omits list",
        )
        return None
    except Exception:
        return None
    home = os.path.expanduser("~")
    return filter_apps_for_description(
        [
            {
                "bundleId": str(x.get("bundleId", "")),
                "displayName": str(x.get("displayName", "")),
                "path": str(x.get("path", "")),
            }
            for x in installed
        ],
        home,
    )


def create_computer_use_mcp_server_for_cli() -> Server:
    adapter = get_computer_use_host_adapter()
    server = Server(COMPUTER_USE_MCP_SERVER_NAME)

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        if adapter.isDisabled():
            return []
        installed = await try_get_installed_app_names()
        return build_computer_use_tools(
            get_cli_cu_capabilities(),
            get_chicago_coordinate_mode(),
            installed,
        )

    @server.call_tool()
    async def _call_tool(
        name: str,
        arguments: dict[str, Any] | None,
    ) -> list[mcp_types.ContentBlock]:
        _ = arguments
        msg = (
            f"Computer-use tool {name!r} is handled in-process by claude-code-python; "
            "this stdio server only advertises tools for discovery."
        )
        return [TextContent(type="text", text=msg)]

    return server


def enable_configs() -> None:
    """Placeholder for TS enableConfigs(); Python loads config via entrypoints."""


async def run_computer_use_mcp_server() -> None:
    from ...services.analytics.datadog import shutdown_datadog
    from ...services.analytics.sink import initialize_analytics_sink

    enable_configs()
    initialize_analytics_sink()
    server = create_computer_use_mcp_server_for_cli()
    log_for_debugging("[Computer Use MCP] Starting MCP server")
    init = InitializationOptions(
        server_name=COMPUTER_USE_MCP_SERVER_NAME,
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
    await shutdown_datadog()
    log_for_debugging("[Computer Use MCP] MCP server stopped")
