"""
Search and load deferred tool schemas by query.

Migrated from: tools/ToolSearchTool/ToolSearchTool.ts (simplified execution)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import TOOL_SEARCH_TOOL_NAME
from .prompt_text import build_prompt


@dataclass
class ToolSearchInput:
    """Input for ToolSearch."""

    query: str
    max_results: int = 5


@dataclass
class ToolSearchOutput:
    """Output describing matched deferred tools."""

    matches: list[str]
    query: str
    total_deferred_tools: int
    pending_mcp_servers: list[str] | None = None


class ToolSearchTool(Tool[dict[str, Any], ToolSearchOutput]):
    """Find deferred tools by keyword or select: name list."""

    @property
    def name(self) -> str:
        return TOOL_SEARCH_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "find deferred tools, load tool schemas"

    async def description(self) -> str:
        return "Search deferred tools and return schema placeholders for matched names."

    async def prompt(self) -> str:
        return build_prompt(delta_enabled=False)

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": ('Query: "select:ToolA,ToolB" for direct names, or keywords to search.'),
                },
                "max_results": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum matches to return",
                },
            },
            "required": ["query"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "matches": {"type": "array", "items": {"type": "string"}},
                "query": {"type": "string"},
                "total_deferred_tools": {"type": "integer"},
                "pending_mcp_servers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        query = str(input.get("query", "")).strip()
        max_results = int(input.get("max_results", 5) or 5)
        max_results = max(1, min(max_results, 50))

        deferred: list[str] = []
        pending: list[str] = []
        app = context.get_app_state() if context.get_app_state else None
        if app is not None and hasattr(app, "deferred_tool_names"):
            raw = getattr(app, "deferred_tool_names", [])
            if isinstance(raw, (list, tuple)):
                deferred = [str(x) for x in raw]
        if app is not None and hasattr(app, "pending_mcp_servers"):
            raw_p = getattr(app, "pending_mcp_servers", [])
            if isinstance(raw_p, (list, tuple)):
                pending = [str(x) for x in raw_p]

        matches: list[str] = []
        if query.lower().startswith("select:"):
            names = [n.strip() for n in query.split(":", 1)[1].split(",") if n.strip()]
            matches = [n for n in names if n in deferred][:max_results]
            if not matches:
                matches = names[:max_results]
        else:
            q = query.lower()
            require = ""
            rest = q
            if q.startswith("+"):
                space = q.find(" ")
                if space > 1:
                    require = q[1:space]
                    rest = q[space + 1 :]
            for name in deferred:
                nl = name.lower()
                if require and require not in nl:
                    continue
                if rest and rest not in nl:
                    continue
                matches.append(name)
                if len(matches) >= max_results:
                    break

        out = ToolSearchOutput(
            matches=matches,
            query=query,
            total_deferred_tools=len(deferred),
            pending_mcp_servers=pending or None,
        )
        return ToolResult(success=True, output=out)
