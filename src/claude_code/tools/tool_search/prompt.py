"""Tool search documentation.

Migrated from: tools/ToolSearchTool/prompt.ts (trimmed; feature flags omitted).
"""

from __future__ import annotations

from typing import Any

TOOL_SEARCH_TOOL_NAME = "ToolSearch"


def get_tool_search_prompt() -> str:
    return """Fetches full schema definitions for deferred tools so they can be called.

Deferred tools appear by name in system reminders or available-deferred-tools blocks.
Until fetched, only the name is known — use this tool to load JSON Schema.

Query forms:
- "select:Read,Edit,Grep" — fetch these exact tools by name
- "notebook jupyter" — keyword search, up to max_results best matches
- "+slack send" — require "slack" in the name, rank by remaining terms
"""


def is_deferred_tool_record(tool: dict[str, Any]) -> bool:
    """Return True if this tool record behaves like a deferred tool in TS."""
    if tool.get("always_load") is True:
        return False
    if tool.get("is_mcp") is True:
        return True
    return tool.get("should_defer") is True
