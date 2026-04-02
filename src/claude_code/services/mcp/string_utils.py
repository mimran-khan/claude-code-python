"""MCP tool/server name string helpers.

Migrated from: services/mcp/mcpStringUtils.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from .normalization import normalize_name_for_mcp


@dataclass(frozen=True)
class McpInfoFromString:
    server_name: str
    tool_name: str | None = None


def mcp_info_from_string(tool_string: str) -> McpInfoFromString | None:
    parts = tool_string.split("__")
    if len(parts) < 2:
        return None
    mcp_part, server_name, *tool_name_parts = parts
    if mcp_part != "mcp" or not server_name:
        return None
    tool_name = "__".join(tool_name_parts) if tool_name_parts else None
    return McpInfoFromString(server_name=server_name, tool_name=tool_name)


def get_mcp_prefix(server_name: str) -> str:
    return f"mcp__{normalize_name_for_mcp(server_name)}__"


def build_mcp_tool_name(server_name: str, tool_name: str) -> str:
    return f"{get_mcp_prefix(server_name)}{normalize_name_for_mcp(tool_name)}"


def get_tool_name_for_permission_check(tool: object) -> str:
    name = getattr(tool, "name", "")
    mcp_info = getattr(tool, "mcp_info", None)
    if mcp_info is not None:
        sn = getattr(mcp_info, "server_name", None)
        tn = getattr(mcp_info, "tool_name", None)
        if isinstance(sn, str) and isinstance(tn, str):
            return build_mcp_tool_name(sn, tn)
    return str(name)


def get_mcp_display_name(full_name: str, server_name: str) -> str:
    prefix = get_mcp_prefix(server_name)
    return full_name.replace(prefix, "", 1)
