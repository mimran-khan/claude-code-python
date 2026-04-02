"""
Tool output / display text helpers.

Migrated from: utils/transcriptSearch.ts (tool_* helpers); TS `toolHelpers.ts` absent.
"""

from .transcript_search import tool_result_search_text, tool_use_search_text

__all__ = ["tool_result_search_text", "tool_use_search_text"]
