"""Read a single MCP resource by URI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .prompt import DESCRIPTION, READ_MCP_RESOURCE_TOOL_NAME


@dataclass
class ReadMcpResourceInput:
    server: str
    uri: str


@dataclass
class ReadMcpResourceContentBlock:
    uri: str
    mime_type: str | None = None
    text: str | None = None
    blob_saved_to: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"uri": self.uri}
        if self.mime_type is not None:
            d["mimeType"] = self.mime_type
        if self.text is not None:
            d["text"] = self.text
        if self.blob_saved_to is not None:
            d["blobSavedTo"] = self.blob_saved_to
        return d


@dataclass
class ReadMcpResourceOutput:
    contents: list[ReadMcpResourceContentBlock]


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "server": {"type": "string", "description": "The MCP server name"},
        "uri": {"type": "string", "description": "The resource URI to read"},
    },
    "required": ["server", "uri"],
}


class ReadMcpResourceTool(Tool):
    name = READ_MCP_RESOURCE_TOOL_NAME
    description = DESCRIPTION.strip()
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True
    user_facing_name = "readMcpResource"

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[dict[str, Any]]:
        server_name = str(input_data.get("server", ""))
        uri = str(input_data.get("uri", ""))
        opts = context.options or {}
        clients: list[Any] = list(opts.get("mcp_clients", []))
        client = next((c for c in clients if getattr(c, "name", None) == server_name), None)
        if not client:
            names = ", ".join(getattr(c, "name", "?") for c in clients) or "(none)"
            raise RuntimeError(f'Server "{server_name}" not found. Available servers: {names}')
        if getattr(client, "type", "") != "connected":
            raise RuntimeError(f'Server "{server_name}" is not connected')
        caps = getattr(client, "capabilities", None) or {}
        if isinstance(caps, dict) and caps.get("resources") is False:
            raise RuntimeError(f'Server "{server_name}" does not support resources')

        read_fn = getattr(client, "read_resource", None)
        if not callable(read_fn):
            raise RuntimeError(f'Server "{server_name}" has no read_resource implementation')

        raw = await read_fn(uri)
        blocks: list[ReadMcpResourceContentBlock] = []
        if isinstance(raw, ReadMcpResourceOutput):
            blocks = raw.contents
        elif isinstance(raw, dict) and "contents" in raw:
            for c in raw["contents"]:
                if isinstance(c, dict):
                    blocks.append(
                        ReadMcpResourceContentBlock(
                            uri=str(c.get("uri", uri)),
                            mime_type=c.get("mimeType"),
                            text=c.get("text"),
                            blob_saved_to=c.get("blobSavedTo"),
                        ),
                    )
        else:
            blocks.append(
                ReadMcpResourceContentBlock(
                    uri=uri,
                    text=json.dumps(raw) if raw is not None else "",
                ),
            )

        return ToolResult(data={"contents": [b.to_dict() for b in blocks]})

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        return f"read MCP resource {input_data.get('uri')}@{input_data.get('server')}"


def format_tool_result_content(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2)
