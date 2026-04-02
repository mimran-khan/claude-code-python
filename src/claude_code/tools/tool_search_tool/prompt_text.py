"""
Instructions for deferred tool discovery (ToolSearch).

Migrated from: tools/ToolSearchTool/prompt.ts (core prompt tail; feature flags omitted)
"""

from __future__ import annotations

from .constants import TOOL_SEARCH_TOOL_NAME

PROMPT_HEAD = """Fetches full schema definitions for deferred tools so they can be called.

"""

PROMPT_TAIL = """ Until fetched, only the name is known — there is no parameter schema, so the tool cannot be invoked. This tool takes a query, matches it against the deferred tool list, and returns the matched tools' complete JSONSchema definitions inside a <functions> block. Once a tool's schema appears in that result, it is callable exactly like any tool defined at the top of the prompt.

Result format: each matched tool appears as one <function>{"description": "...", "name": "...", "parameters": {...}}</function> line inside the <functions> block — the same encoding as the tool list at the top of this prompt.

Query forms:
- "select:Read,Edit,Grep" — fetch these exact tools by name
- "notebook jupyter" — keyword search, up to max_results best matches
- "+slack send" — require "slack" in the name, rank by remaining terms"""


def get_tool_location_hint(delta_enabled: bool = False) -> str:
    """Where deferred tools appear in the prompt (TS growthbook / env gated)."""
    if delta_enabled:
        return "Deferred tools appear by name in <system-reminder> messages."
    return "Deferred tools appear by name in <available-deferred-tools> messages."


def build_prompt(delta_enabled: bool = False) -> str:
    return PROMPT_HEAD + get_tool_location_hint(delta_enabled) + PROMPT_TAIL


__all__ = [
    "TOOL_SEARCH_TOOL_NAME",
    "PROMPT_HEAD",
    "PROMPT_TAIL",
    "build_prompt",
    "get_tool_location_hint",
]
