"""
Web Search Tool implementation.

Search the web for information.

Migrated from: tools/WebSearchTool/WebSearchTool.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext

WEB_SEARCH_TOOL_NAME = "WebSearch"


WEB_SEARCH_DESCRIPTION = """Search the web for real-time information.

Returns summarized information from search results and relevant URLs.

Use for:
- Up-to-date information
- Current events
- Library documentation
- Technology news
"""


WEB_SEARCH_PROMPT = """Search the web for information.

Include relevant keywords for better results.
For technical queries, include version numbers or dates if relevant.
"""


@dataclass
class WebSearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str


@dataclass
class WebSearchOutput:
    """Output from the Web Search tool."""

    results: list[WebSearchResult]
    query: str


class WebSearchTool(Tool[dict[str, Any], WebSearchOutput]):
    """Tool for searching the web."""

    @property
    def name(self) -> str:
        return WEB_SEARCH_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "search the web, find information online"

    async def description(self) -> str:
        return WEB_SEARCH_DESCRIPTION

    async def prompt(self) -> str:
        return WEB_SEARCH_PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to use (TypeScript WebSearchTool name)",
                    "minLength": 2,
                },
                "search_term": {
                    "type": "string",
                    "description": "Alias for query (Python legacy)",
                },
                "allowed_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only include search results from these domains",
                },
                "blocked_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Never include search results from these domains",
                },
                "explanation": {
                    "type": "string",
                    "description": "Why this search is being performed",
                },
            },
            "required": [],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "results": {"type": "array"},
                "query": {"type": "string"},
            },
        }

    def user_facing_name(self, input: dict[str, Any] | None = None) -> str:
        return WEB_SEARCH_TOOL_NAME

    def get_tool_use_summary(self, input: dict[str, Any] | None = None) -> str | None:
        if not input:
            return None
        q = str(input.get("query") or input.get("search_term") or "").strip()
        return q or None

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        """Execute the web search."""
        return await web_search(input, context)


async def web_search(
    input: dict[str, Any],
    context: ToolUseContext,
) -> ToolResult:
    """Search the web for information."""
    import os

    search_term = str(input.get("query") or input.get("search_term") or "").strip()

    if len(search_term) < 2:
        return ToolResult(
            success=False,
            error='A "query" of at least 2 characters is required (or legacy "search_term").',
            error_code=1,
        )

    # Check for API key
    tavily_key = os.getenv("TAVILY_API_KEY")

    if tavily_key:
        allowed = input.get("allowed_domains") or []
        blocked = input.get("blocked_domains") or []
        if not isinstance(allowed, list):
            allowed = []
        if not isinstance(blocked, list):
            blocked = []
        return await _tavily_search(
            search_term,
            tavily_key,
            allowed_domains=[str(x) for x in allowed],
            blocked_domains=[str(x) for x in blocked],
        )

    # Fallback: return stub result
    return ToolResult(
        success=False,
        error="No search API configured. Set TAVILY_API_KEY for web search.",
        error_code=1,
    )


def _hostname(url: str) -> str:
    from urllib.parse import urlparse

    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


async def _tavily_search(
    query: str,
    api_key: str,
    *,
    allowed_domains: list[str],
    blocked_domains: list[str],
) -> ToolResult:
    """Search using Tavily API."""
    import httpx

    allowed_l = {d.lower().lstrip("*.") for d in allowed_domains}
    blocked_l = {d.lower().lstrip("*.") for d in blocked_domains}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": True,
                    "include_images": False,
                    "max_results": 8,
                },
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("results", []):
            url = item.get("url", "")
            host = _hostname(str(url))
            if blocked_l and any(host == b or host.endswith("." + b) for b in blocked_l):
                continue
            if allowed_l and not any(host == a or host.endswith("." + a) for a in allowed_l):
                continue
            results.append(
                WebSearchResult(
                    title=item.get("title", ""),
                    url=str(url),
                    snippet=item.get("content", ""),
                )
            )

        output = WebSearchOutput(
            results=results,
            query=query,
        )

        return ToolResult(success=True, output=output)

    except Exception as e:
        return ToolResult(
            success=False,
            error=str(e),
            error_code=1,
        )
