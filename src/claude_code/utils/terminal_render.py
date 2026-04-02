"""
Terminal text wrapping and truncation for tool output previews.

Migrated from: utils/terminal.ts
"""

from __future__ import annotations

import re

from .truncate import string_width

_MAX_LINES_TO_SHOW = 3
_PADDING = 10

# CSI sequences (SGR); good enough for common colored CLI output.
_CSI_RE = re.compile(r"\x1b\[[\d;]*[A-Za-z]")


def _slice_ansi_visible(line: str, start: int, end: int) -> str:
    """Take a slice on visible width while preserving leading CSI runs."""
    if "\x1b" not in line:
        return _slice_plain(line, start, end)
    out: list[str] = []
    pos = 0
    i = 0
    while i < len(line):
        if line[i] == "\x1b":
            m = _CSI_RE.match(line, i)
            if m:
                if start <= pos < end:
                    out.append(m.group(0))
                i = m.end()
                continue
        ch = line[i]
        w = string_width(ch)
        if pos + w > start and pos < end:
            out.append(ch)
        pos += w
        i += 1
    return "".join(out)


def _slice_plain(text: str, start: int, end: int) -> str:
    if start <= 0 and end >= string_width(text):
        return text
    out: list[str] = []
    pos = 0
    for ch in text:
        w = string_width(ch)
        if pos + w > start and pos < end:
            out.append(ch)
        pos += w
    return "".join(out)


def _wrap_text(text: str, wrap_width: int) -> tuple[str, int]:
    lines = text.split("\n")
    wrapped: list[str] = []
    for line in lines:
        vis = string_width(line)
        if vis <= wrap_width:
            wrapped.append(line.rstrip())
        else:
            position = 0
            while position < vis:
                chunk = _slice_ansi_visible(line, position, position + wrap_width)
                wrapped.append(chunk.rstrip())
                position += wrap_width

    remaining = len(wrapped) - _MAX_LINES_TO_SHOW
    if remaining == 1:
        return (
            "\n".join(wrapped[: _MAX_LINES_TO_SHOW + 1]).rstrip(),
            0,
        )
    return (
        "\n".join(wrapped[:_MAX_LINES_TO_SHOW]).rstrip(),
        max(0, remaining),
    )


def ctrl_o_to_expand() -> str:
    return "(ctrl+o to expand)"


def render_truncated_content(
    content: str,
    terminal_width: int,
    suppress_expand_hint: bool = False,
) -> str:
    trimmed = content.rstrip()
    if not trimmed:
        return ""
    wrap_w = max(terminal_width - _PADDING, 10)
    max_chars = _MAX_LINES_TO_SHOW * wrap_w * 4
    pre_truncated = len(trimmed) > max_chars
    content_for_wrapping = trimmed[:max_chars] if pre_truncated else trimmed
    above, remaining = _wrap_text(content_for_wrapping, wrap_w)
    est_rem = max(remaining, (len(trimmed) + wrap_w - 1) // wrap_w - _MAX_LINES_TO_SHOW) if pre_truncated else remaining
    hint = ""
    if est_rem > 0:
        suffix = "" if suppress_expand_hint else f" {ctrl_o_to_expand()}"
        hint = f"\n… +{est_rem} lines{suffix}"
    parts = [p for p in (above, hint) if p]
    return "\n".join(parts)


def is_output_line_truncated(content: str) -> bool:
    pos = 0
    for _ in range(_MAX_LINES_TO_SHOW + 1):
        idx = content.find("\n", pos)
        if idx == -1:
            return False
        pos = idx + 1
    return pos < len(content)
