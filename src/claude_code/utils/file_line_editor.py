"""
Line-oriented file edits (``utils/fileLineEditor.ts`` not in snapshot).

Provides a small async API for replacing ranges by line number.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LineEdit:
    start_line: int  # 1-based inclusive
    end_line: int  # 1-based inclusive
    new_text: str


async def apply_line_edits(content: str, edits: list[LineEdit]) -> str:
    lines = content.splitlines(keepends=True)
    for ed in sorted(edits, key=lambda e: e.start_line, reverse=True):
        i0 = max(0, ed.start_line - 1)
        i1 = min(len(lines), ed.end_line)
        replacement = ed.new_text if ed.new_text.endswith("\n") else ed.new_text + "\n"
        lines[i0:i1] = [replacement]
    return "".join(lines)
