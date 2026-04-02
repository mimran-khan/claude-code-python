"""
Read a single MCP resource by URI.

Migrated from: tools/ReadMcpResourceTool/ReadMcpResourceTool.ts
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .prompt_text import DESCRIPTION, PROMPT, READ_MCP_RESOURCE_TOOL_NAME


@dataclass
class ReadMcpResourceContent:
    uri: str
    mime_type: str | None = None
    text: str | None = None
    blob_saved_to: str | None = None


@dataclass
class ReadMcpResourceOutput:
    contents: list[ReadMcpResourceContent]


class ReadMcpResourceTool(Tool[dict[str, Any], ReadMcpResourceOutput]):
    @property
    def name(self) -> str:
        return READ_MCP_RESOURCE_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "read a specific MCP resource by URI"

    async def description(self) -> str:
        return DESCRIPTION.strip()

    async def prompt(self) -> str:
        return PROMPT.strip()

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server": {"type": "string"},
                "uri": {"type": "string"},
            },
            "required": ["server", "uri"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "contents": {
                    "type": "array",
                    "items": {"type": "object"},
                },
            },
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        server_name = str(input.get("server", "")).strip()
        uri = str(input.get("uri", "")).strip()
        if not server_name or not uri:
            return ToolResult(success=False, error="server and uri are required", error_code=1)

        clients: list[Any] = []
        app = context.get_app_state() if context.get_app_state else None
        if app is not None and hasattr(app, "mcp_clients"):
            raw = getattr(app, "mcp_clients", [])
            if isinstance(raw, (list, tuple)):
                clients = list(raw)

        client = next((c for c in clients if getattr(c, "name", None) == server_name), None)
        if client is None:
            return ToolResult(
                success=False,
                error=f'MCP server "{server_name}" is not connected',
                error_code=1,
            )

        read_fn = getattr(client, "read_resource", None)
        if not callable(read_fn):
            return ToolResult(
                success=False,
                error="Client does not support read_resource",
                error_code=1,
            )

        try:
            if inspect.iscoroutinefunction(read_fn):
                result = await read_fn(uri)
            else:
                result = read_fn(uri)
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=str(e), error_code=1)

        contents: list[ReadMcpResourceContent] = []
        if isinstance(result, dict) and "contents" in result:
            for block in result.get("contents") or []:
                if isinstance(block, dict):
                    contents.append(
                        ReadMcpResourceContent(
                            uri=str(block.get("uri", uri)),
                            mime_type=block.get("mimeType"),
                            text=block.get("text"),
                            blob_saved_to=block.get("blobSavedTo"),
                        ),
                    )
        elif isinstance(result, str):
            contents.append(ReadMcpResourceContent(uri=uri, text=result))

        return ToolResult(success=True, output=ReadMcpResourceOutput(contents=contents))
