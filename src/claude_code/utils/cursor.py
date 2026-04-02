"""
REPL text cursor, kill ring, and wrapped layout (partial port of ``utils/Cursor.ts``).

The TypeScript implementation is Ink/grapheme-heavy (~1.5k LOC). This module provides
a width-aware subset using :func:`claude_code.utils.string_width.string_width` for TUI use.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from claude_code.utils.string_width import string_width

_KILL_RING_MAX = 10
_kill_ring: list[str] = []
_kill_ring_index = 0
_last_action_was_kill = False
_last_yank_start = 0
_last_yank_length = 0
_last_action_was_yank = False

VIM_WORD_CHAR_REGEX = re.compile(r"^[\w]$", re.UNICODE)
WHITESPACE_REGEX = re.compile(r"\s")


def push_to_kill_ring(text: str, direction: str = "append") -> None:
    global _kill_ring, _kill_ring_index, _last_action_was_kill
    if not text:
        return
    if _last_action_was_kill and _kill_ring:
        if direction == "prepend":
            _kill_ring[0] = text + _kill_ring[0]
        else:
            _kill_ring[0] = _kill_ring[0] + text
    else:
        _kill_ring.insert(0, text)
        if len(_kill_ring) > _KILL_RING_MAX:
            _kill_ring.pop()
        _kill_ring_index = 0
    _last_action_was_kill = True


def get_last_kill() -> str:
    return _kill_ring[0] if _kill_ring else ""


def get_kill_ring_item(index: int) -> str:
    if 0 <= index < len(_kill_ring):
        return _kill_ring[index]
    return ""


def get_kill_ring_size() -> int:
    return len(_kill_ring)


def clear_kill_ring() -> None:
    global _kill_ring, _kill_ring_index, _last_action_was_kill
    _kill_ring = []
    _kill_ring_index = 0
    _last_action_was_kill = False


def reset_kill_accumulation() -> None:
    global _last_action_was_kill
    _last_action_was_kill = False


def record_yank(start: int, length: int) -> None:
    global _last_yank_start, _last_yank_length, _last_action_was_yank, _last_action_was_kill
    _last_yank_start = start
    _last_yank_length = length
    _last_action_was_yank = True
    _last_action_was_kill = False


def can_yank_pop() -> bool:
    return _last_action_was_yank and len(_kill_ring) > 1


def yank_pop() -> tuple[str, int, int] | None:
    global _kill_ring_index, _last_yank_length
    if not can_yank_pop():
        return None
    _kill_ring_index = (_kill_ring_index + 1) % len(_kill_ring)
    text = get_kill_ring_item(_kill_ring_index)
    return text, _last_yank_start, _last_yank_length


def update_yank_length(length: int) -> None:
    global _last_yank_length
    _last_yank_length = length


def reset_yank_state() -> None:
    global _last_action_was_yank, _last_yank_start, _last_yank_length, _kill_ring_index
    _last_action_was_yank = False
    _last_yank_start = 0
    _last_yank_length = 0
    _kill_ring_index = 0


def is_vim_word_char(ch: str) -> bool:
    if len(ch) != 1:
        return False
    if ch == "_":
        return True
    cat = unicodedata.category(ch)
    return cat.startswith("L") or cat.startswith("N") or cat.startswith("M")


def is_vim_whitespace(ch: str) -> bool:
    return bool(WHITESPACE_REGEX.match(ch))


def is_vim_punctuation(ch: str) -> bool:
    return bool(ch) and not is_vim_whitespace(ch) and not is_vim_word_char(ch)


@dataclass(frozen=True)
class WrappedLine:
    text: str
    start_offset: int
    is_preceded_by_newline: bool
    ends_with_newline: bool = False


class MeasuredText:
    """Soft-wrapped text to a fixed column width (character-based breaks)."""

    __slots__ = ("text", "columns", "_wrapped")

    def __init__(self, text: str, columns: int) -> None:
        self.text = unicodedata.normalize("NFC", text)
        self.columns = max(1, columns)
        self._wrapped: list[WrappedLine] | None = None

    def _build_wrapped(self) -> list[WrappedLine]:
        lines: list[WrappedLine] = []
        pos = 0
        first = True
        for raw_line in self.text.split("\n"):
            offset = pos
            if not raw_line:
                lines.append(WrappedLine("", offset, not first, ends_with_newline=True))
                pos += 1
                first = False
                continue
            chunk_start = 0
            col = 0
            i = 0
            while i < len(raw_line):
                ch = raw_line[i]
                w = string_width(ch)
                if col + w > self.columns and col > 0:
                    seg = raw_line[chunk_start:i]
                    lines.append(WrappedLine(seg, offset + chunk_start, not first and chunk_start == 0))
                    first = False
                    chunk_start = i
                    col = 0
                    continue
                col += w
                i += 1
            seg = raw_line[chunk_start:]
            lines.append(WrappedLine(seg, offset + chunk_start, not first and chunk_start == 0))
            pos += len(raw_line) + 1
            first = False
        return lines

    def get_wrapped_lines(self) -> list[WrappedLine]:
        if self._wrapped is None:
            self._wrapped = self._build_wrapped()
        return self._wrapped

    def get_wrapped_text(self) -> list[str]:
        return [wl.text for wl in self.get_wrapped_lines()]

    def prev_offset(self, offset: int) -> int:
        return max(0, offset - 1)

    def next_offset(self, offset: int) -> int:
        return min(len(self.text), offset + 1)


class Cursor:
    __slots__ = ("measured_text", "offset", "selection")

    def __init__(
        self,
        measured_text: MeasuredText,
        offset: int = 0,
        selection: int = 0,
    ) -> None:
        self.measured_text = measured_text
        self.selection = selection
        tlen = len(self.text)
        self.offset = max(0, min(tlen, offset))

    @property
    def text(self) -> str:
        return self.measured_text.text

    @classmethod
    def from_text(
        cls,
        text: str,
        columns: int,
        offset: int = 0,
        selection: int = 0,
    ) -> Cursor:
        measured = MeasuredText(text, columns - 1 if columns > 1 else 1)
        return cls(measured, offset, selection)

    def left(self) -> Cursor:
        if self.offset == 0:
            return self
        prev = self.measured_text.prev_offset(self.offset)
        return Cursor(self.measured_text, prev, self.selection)

    def right(self) -> Cursor:
        if self.offset >= len(self.text):
            return self
        nxt = self.measured_text.next_offset(self.offset)
        return Cursor(self.measured_text, nxt, self.selection)

    def insert(self, s: str) -> Cursor:
        t = self.text[: self.offset] + s + self.text[self.offset :]
        measured = MeasuredText(t, self.measured_text.columns)
        return Cursor(measured, self.offset + len(s), self.selection)

    def delete_back(self) -> Cursor:
        if self.offset == 0:
            return self
        t = self.text[: self.offset - 1] + self.text[self.offset :]
        measured = MeasuredText(t, self.measured_text.columns)
        return Cursor(measured, self.offset - 1, self.selection)

    def is_at_end(self) -> bool:
        return self.offset >= len(self.text)


__all__ = [
    "Cursor",
    "MeasuredText",
    "WrappedLine",
    "VIM_WORD_CHAR_REGEX",
    "WHITESPACE_REGEX",
    "can_yank_pop",
    "clear_kill_ring",
    "get_kill_ring_item",
    "get_kill_ring_size",
    "get_last_kill",
    "is_vim_punctuation",
    "is_vim_whitespace",
    "is_vim_word_char",
    "push_to_kill_ring",
    "record_yank",
    "reset_kill_accumulation",
    "reset_yank_state",
    "update_yank_length",
    "yank_pop",
]
