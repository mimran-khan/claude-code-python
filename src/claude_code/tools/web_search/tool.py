"""
Web Search Tool Implementation.

Searches the web for information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import WEB_SEARCH_TOOL_NAME, get_web_search_prompt


class WebSearchInput(BaseModel):
    """Input parameters for web search tool."""

    query: str = Field(
        ...,
        description="The search query to execute.",
    )
    include_domains: list[str] = Field(
        default_factory=list,
        description="Optional list of domains to include in search.",
    )
    exclude_domains: list[str] = Field(
        default_factory=list,
        description="Optional list of domains to exclude from search.",
    )


@dataclass
class SearchResult:
    """A single search result."""

    title: str = ""
    url: str = ""
    snippet: str = ""
    published_date: str | None = None


@dataclass
class WebSearchSuccess:
    """Successful web search result."""

    type: Literal["success"] = "success"
    query: str = ""
    results: list[SearchResult] = field(default_factory=list)
    total_results: int = 0


@dataclass
class WebSearchError:
    """Failed web search result."""

    type: Literal["error"] = "error"
    query: str = ""
    error: str = ""


WebSearchOutput = WebSearchSuccess | WebSearchError


class WebSearchTool(Tool[WebSearchInput, WebSearchOutput]):
    """
    Tool for searching the web.

    Uses a search API to find relevant web pages and returns
    formatted results with titles, URLs, and snippets.
    """

    @property
    def name(self) -> str:
        return WEB_SEARCH_TOOL_NAME

    @property
    def description(self) -> str:
        return get_web_search_prompt()

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to execute.",
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of domains to include in search.",
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of domains to exclude from search.",
                },
            },
            "required": ["query"],
        }

    def is_read_only(self, input_data: WebSearchInput) -> bool:
        return True

    async def call(
        self,
        input_data: WebSearchInput,
        context: Any,
    ) -> ToolResult[WebSearchOutput]:
        """Execute the web search operation."""
        query = input_data.query

        if not query or not query.strip():
            return ToolResult(
                success=False,
                output=WebSearchError(
                    query=query,
                    error="Query cannot be empty.",
                ),
            )

        # In a full implementation, this would call a search API
        # For now, return a placeholder response
        return ToolResult(
            success=False,
            output=WebSearchError(
                query=query,
                error=(
                    "Web search requires API integration. "
                    "Please configure a search provider (e.g., Tavily, Serper, or similar)."
                ),
            ),
        )

    def user_facing_name(self, input_data: WebSearchInput | None = None) -> str:
        """Get the user-facing name for this tool."""
        return "Search"

    def get_tool_use_summary(self, input_data: WebSearchInput | None) -> str | None:
        """Get a short summary of this tool use."""
        if input_data and input_data.query:
            query = input_data.query
            if len(query) > 40:
                return query[:37] + "..."
            return query
        return None

    def get_activity_description(self, input_data: WebSearchInput | None) -> str | None:
        """Get a human-readable activity description."""
        if input_data and input_data.query:
            return (
                f"Searching for '{input_data.query[:30]}...'"
                if len(input_data.query) > 30
                else f"Searching for '{input_data.query}'"
            )
        return "Searching the web"
