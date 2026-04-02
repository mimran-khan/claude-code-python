"""
Web Search Tool.

Searches the web for information.
"""

from .prompt import (
    WEB_SEARCH_TOOL_NAME,
    get_web_search_prompt,
)


def __getattr__(name: str):
    """Lazy import for WebSearchTool."""
    if name == "WebSearchTool":
        from .tool import WebSearchTool

        return WebSearchTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "WEB_SEARCH_TOOL_NAME",
    "get_web_search_prompt",
    "WebSearchTool",
]
