"""List MCP resources tool."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .prompt import DESCRIPTION, LIST_MCP_RESOURCES_TOOL_NAME


@dataclass
class ListMcpResourcesInput:
    server: str | None = None


@dataclass
class McpResourceItem:
    uri: str
    name: str
    server: str
    mime_type: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "uri": self.uri,
            "name": self.name,
            "server": self.server,
        }
        if self.mime_type is not None:
            d["mimeType"] = self.mime_type
        if self.description is not None:
            d["description"] = self.description
        return d


@runtime_checkable
class McpClientLike(Protocol):
    name: str
    type: str

    async def list_resources(self) -> list[McpResourceItem]: ...


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "server": {
            "type": "string",
            "description": "Optional server name to filter resources by",
        },
    },
}


class ListMcpResourcesTool(Tool):
    """Lists resources exposed by connected MCP servers."""

    name = LIST_MCP_RESOURCES_TOOL_NAME
    description = DESCRIPTION.strip()
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True
    user_facing_name = "listMcpResources"

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[list[dict[str, Any]]]:
        opts = context.options or {}
        raw_clients: list[Any] = list(opts.get("mcp_clients", []))
        target = input_data.get("server")

        clients = raw_clients
        if target:
            clients = [c for c in raw_clients if getattr(c, "name", None) == target]
            if not clients:
                names = ", ".join(getattr(c, "name", "?") for c in raw_clients) or "(none)"
                raise RuntimeError(f'Server "{target}" not found. Available servers: {names}')

        out: list[McpResourceItem] = []
        for client in clients:
            if getattr(client, "type", "") != "connected":
                continue
            fetch = getattr(client, "list_resources", None)
            if callable(fetch):
                items = await fetch()
                out.extend(items)
            else:
                resources = getattr(client, "resources", None)
                if isinstance(resources, list):
                    for r in resources:
                        if isinstance(r, McpResourceItem):
                            out.append(r)
                        elif isinstance(r, dict):
                            out.append(
                                McpResourceItem(
                                    uri=str(r.get("uri", "")),
                                    name=str(r.get("name", "")),
                                    server=getattr(client, "name", ""),
                                    mime_type=r.get("mimeType"),
                                    description=r.get("description"),
                                ),
                            )

        return ToolResult(data=[x.to_dict() for x in out])

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        s = input_data.get("server")
        return f"list MCP resources{f' ({s})' if s else ''}"


def format_tool_result_content(items: list[dict[str, Any]]) -> str:
    if not items:
        return "No resources found. MCP servers may still provide tools even if they have no resources."
    return json.dumps(items, indent=2)
