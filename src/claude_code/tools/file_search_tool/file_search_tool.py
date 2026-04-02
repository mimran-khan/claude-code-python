"""
File search (semantic / index) — no dedicated tools/FileSearchTool in this leak.

TODO: Integrate workspace index, embeddings, or ripgrep fallback policy from product code.
"""

from __future__ import annotations

from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import DESCRIPTION, FILE_SEARCH_TOOL_NAME
from .types import FileSearchOutput


class FileSearchTool(Tool[dict[str, Any], FileSearchOutput]):
    @property
    def name(self) -> str:
        return FILE_SEARCH_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "semantic or indexed codebase file search"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return DESCRIPTION

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language or keyword search query",
                },
                "path": {"type": "string", "description": "Optional root path to restrict search"},
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 20)",
                    "default": 20,
                },
            },
            "required": ["query"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "hits": {"type": "array"},
            },
        }

    async def check_permissions(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> dict[str, Any]:
        # TODO: read permission rules for indexed paths
        return {"behavior": "allow"}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        # TODO: call index service / embedding retrieval
        q = str(input.get("query", ""))
        out = FileSearchOutput(query=q, hits=[])
        return ToolResult(
            success=True,
            output=out,
        )
