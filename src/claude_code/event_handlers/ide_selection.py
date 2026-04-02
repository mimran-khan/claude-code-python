"""
IDE ``selection_changed`` notification → line span summary.

Migrated from: hooks/useIdeSelection.ts
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IdeSelection:
    line_count: int
    line_start: int | None = None
    text: str | None = None
    file_path: str | None = None


def ide_selection_from_notification_params(params: Mapping[str, Any]) -> IdeSelection | None:
    sel = params.get("selection")
    text = params.get("text")
    fp = params.get("filePath")
    text_s = str(text) if text is not None else None
    fp_s = str(fp) if fp is not None else None

    if isinstance(sel, Mapping):
        start = sel.get("start")
        end = sel.get("end")
        if isinstance(start, Mapping) and isinstance(end, Mapping):
            s_line = start.get("line")
            e_line = end.get("line")
            e_char = end.get("character")
            if isinstance(s_line, (int, float)) and isinstance(e_line, (int, float)):
                sl = int(s_line)
                el = int(e_line)
                line_count = el - sl + 1
                if isinstance(e_char, (int, float)) and int(e_char) == 0:
                    line_count -= 1
                return IdeSelection(
                    line_count=max(0, line_count),
                    line_start=sl,
                    text=text_s,
                    file_path=fp_s,
                )

    if text_s is not None:
        return IdeSelection(line_count=0, text=text_s, file_path=fp_s)
    return None
