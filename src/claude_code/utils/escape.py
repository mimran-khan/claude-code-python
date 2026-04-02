"""
String escaping helpers (no ``utils/escape.ts`` in snapshot — common utilities).
"""

from __future__ import annotations

import html
import re


def escape_html(text: str) -> str:
    return html.escape(text, quote=True)


def escape_regex_literal(text: str) -> str:
    return re.escape(text)


def escape_for_diff_specials(s: str) -> tuple[str, str]:
    """Replace ``&`` and ``$`` for diff engines that mishandle them (see utils/diff.ts)."""
    amp = "<<:AMPERSAND_TOKEN:>>"
    dollar = "<<:DOLLAR_TOKEN:>>"
    return s.replace("&", amp).replace("$", dollar), amp


def unescape_from_diff_specials(s: str, amp: str, dollar: str) -> str:
    return s.replace(amp, "&").replace(dollar, "$")
