"""
SearchTool — ripgrep-based code search (TS: tools/GrepTool/).
"""

from ..grep_tool import GREP_TOOL_NAME, GrepTool, grep_execute

SEARCH_TOOL_NAME = GREP_TOOL_NAME
SearchTool = GrepTool

__all__ = [
    "SEARCH_TOOL_NAME",
    "GREP_TOOL_NAME",
    "SearchTool",
    "GrepTool",
    "grep_execute",
]
