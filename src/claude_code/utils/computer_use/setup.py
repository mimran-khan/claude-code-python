"""
MCP config + allowed tool names for computer-use (dynamic stdio placeholder).

Migrated from: utils/computerUse/setup.ts
"""

from __future__ import annotations

import sys
from typing import Any, TypedDict

from ...services.mcp.string_utils import build_mcp_tool_name
from .common import COMPUTER_USE_MCP_SERVER_NAME, get_cli_cu_capabilities
from .gates import get_chicago_coordinate_mode
from .mcp_server import build_computer_use_tools


class ComputerUseMcpEntry(TypedDict):
    type: str
    command: str
    args: list[str]
    scope: str


def setup_computer_use_mcp() -> dict[str, Any]:
    caps = get_cli_cu_capabilities()
    mode = get_chicago_coordinate_mode()
    tools = build_computer_use_tools(caps, mode, None)
    allowed_tools = [build_mcp_tool_name(COMPUTER_USE_MCP_SERVER_NAME, t.name) for t in tools]

    args = ["-m", "claude_code.utils.computer_use"]

    mcp_entry: ComputerUseMcpEntry = {
        "type": "stdio",
        "command": sys.executable,
        "args": args,
        "scope": "dynamic",
    }
    return {
        "mcpConfig": {COMPUTER_USE_MCP_SERVER_NAME: mcp_entry},
        "allowedTools": allowed_tools,
    }
