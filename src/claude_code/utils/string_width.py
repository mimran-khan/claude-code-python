"""
Terminal display width for strings (ANSI-aware, Unicode width).

Migrated from: ink/stringWidth.ts (referenced as utils/stringWidth in TS layout).
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


def _is_zero_width(cp: int) -> bool:
    if 0x20 <= cp < 0x7F:
        return False
    if 0xA0 <= cp < 0x0300:
        return cp == 0x00AD
    if cp <= 0x1F or 0x7F <= cp <= 0x9F:
        return True
    if 0x200B <= cp <= 0x200D or cp == 0xFEFF or 0x2060 <= cp <= 0x2064:
        return True
    if 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF:
        return True
    if 0x0300 <= cp <= 0x036F:
        return True
    return bool(55296 <= cp <= 57343 or 917504 <= cp <= 917631)


@lru_cache(maxsize=4096)
def _char_width(ch: str) -> int:
    if not ch:
        return 0
    o = ord(ch)
    if _is_zero_width(o):
        return 0
    ea = unicodedata.east_asian_width(ch)
    if ea in ("F", "W"):
        return 2
    if ea == "A":
        return 1
    return 1


def string_width(text: str) -> int:
    """
    Visible width in terminal cells. Strips ANSI sequences; uses East Asian Width.
    Emoji / ZWJ sequences are approximated via per-codepoint width (good enough for layout).
    """
    if not text:
        return 0
    if "\x1b" in text:
        text = _strip_ansi(text)
        if not text:
            return 0
    total = 0
    for ch in text:
        total += _char_width(ch)
    return total
