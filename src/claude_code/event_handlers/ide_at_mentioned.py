"""
IDE ``at_mentioned`` MCP notification → normalized file + line range.

Migrated from: hooks/useIdeAtMentioned.ts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdeAtMentioned:
    file_path: str
    line_start: int | None = None
    line_end: int | None = None


def parse_at_mentioned_params(params: dict[str, object]) -> IdeAtMentioned:
    """Convert 0-based IDE lines to 1-based for REPL display."""
    fp = str(params.get("filePath", ""))
    raw_start = params.get("lineStart")
    raw_end = params.get("lineEnd")
    ls = int(raw_start) + 1 if isinstance(raw_start, (int, float)) else None
    le = int(raw_end) + 1 if isinstance(raw_end, (int, float)) else None
    return IdeAtMentioned(file_path=fp, line_start=ls, line_end=le)
