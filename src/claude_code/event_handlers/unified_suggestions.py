"""
Fuse-backed suggestion merging (files, MCP, agents).

Migrated from: hooks/unifiedSuggestions.ts

The TypeScript module orchestrates Fuse.js ranking and theme truncation.
Python CLI hosts should call suggestion providers directly; this module
anchors the port with shared typing hooks only.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class SuggestionItemDict(TypedDict, total=False):
    displayText: str
    description: str
    path: str
    score: float


SuggestionKind = Literal["file", "mcp_resource", "agent"]


def coerce_suggestion_score(item: dict[str, Any]) -> float:
    """Normalize optional Fuse score for stable sorting."""
    raw = item.get("score")
    return float(raw) if isinstance(raw, (int, float)) else 0.0
