"""
Web Fetch Tool.

Fetches and processes content from URLs.
"""

from .prompt import (
    DESCRIPTION,
    WEB_FETCH_TOOL_NAME,
    make_secondary_model_prompt,
)


def __getattr__(name: str):
    """Lazy import for WebFetchTool."""
    if name == "WebFetchTool":
        from .tool import WebFetchTool

        return WebFetchTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "WEB_FETCH_TOOL_NAME",
    "DESCRIPTION",
    "make_secondary_model_prompt",
    "WebFetchTool",
]
