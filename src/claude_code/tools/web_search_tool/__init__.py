"""
Web Search Tool.

Search the web for information.

Migrated from: tools/WebSearchTool/*.ts
"""

from .web_search_tool import (
    WEB_SEARCH_TOOL_NAME,
    WebSearchTool,
    web_search,
)

__all__ = [
    "WebSearchTool",
    "WEB_SEARCH_TOOL_NAME",
    "web_search",
]
