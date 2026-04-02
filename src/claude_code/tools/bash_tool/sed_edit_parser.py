"""
Parse ``sed -i`` style in-place edits for UI / fast-path hints.

Migrated from: tools/BashTool/sedEditParser.ts

Full shell-token parsing mirrors ``tryParseShellCommand`` in TS; this port handles
common ``sed -i 's/a/b/g' file`` forms only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SedEditInfo:
    file_path: str
    pattern: str
    replacement: str
    flags: str
    extended_regex: bool


_SUBST_RE = re.compile(
    r"^s([^\\\n])(.+?)\1(.+?)\1([a-zA-Z]*)$",
    re.DOTALL,
)


def parse_sed_edit_command(command: str) -> SedEditInfo | None:
    trimmed = command.strip()
    m = re.match(r"^\s*sed\s+(.+)$", trimmed, re.DOTALL)
    if not m:
        return None
    rest = m.group(1)
    extended = False
    if rest.startswith("-E ") or rest.startswith("-r "):
        extended = True
        rest = rest.split(None, 1)[1]
    if not rest.startswith("-i"):
        return None
    tokens = rest.split()
    idx = 0
    if not tokens:
        return None
    if tokens[0] != "-i":
        return None
    idx = 1
    if idx < len(tokens) and not tokens[idx].startswith(("'", '"')):
        idx += 1
    if idx >= len(tokens):
        return None
    expr = tokens[idx].strip("'\"")
    file_path = tokens[-1] if len(tokens) > idx + 1 else ""
    if not file_path or file_path == expr:
        return None
    sm = _SUBST_RE.match(expr)
    if not sm:
        return None
    return SedEditInfo(
        file_path=file_path,
        pattern=sm.group(2),
        replacement=sm.group(3),
        flags=sm.group(4) or "",
        extended_regex=extended,
    )


def is_sed_in_place_edit(command: str) -> bool:
    return parse_sed_edit_command(command) is not None


__all__ = ["SedEditInfo", "is_sed_in_place_edit", "parse_sed_edit_command"]
