"""Generic MCP call tool definition. Migrated from tools/MCPTool/MCPTool.ts."""

from __future__ import annotations

from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .mcp_prompt_constants import DESCRIPTION, PROMPT


class McpToolDef(Tool[dict[str, Any], str]):
    """Passthrough MCP invocation surface (name/description overridden by client)."""

    @property
    def name(self) -> str:
        return "mcp"

    async def description(self) -> str:
        return DESCRIPTION or "Call an MCP tool"

    async def prompt(self) -> str:
        return PROMPT or ""

    def get_input_schema(self) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": True}

    def get_output_schema(self) -> dict[str, Any]:
        return {"type": "string", "description": "MCP tool execution result"}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = input, context
        return ToolResult(success=True, output="")
