"""
Informational warnings for potentially destructive bash commands (permission UI).

Migrated from: tools/BashTool/destructiveCommandWarning.ts
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class _Pattern:
    pattern: re.Pattern[str]
    warning: str


_DESTRUCTIVE_PATTERNS: tuple[_Pattern, ...] = (
    _Pattern(re.compile(r"\bgit\s+reset\s+--hard\b"), "Note: may discard uncommitted changes"),
    _Pattern(
        re.compile(r"\bgit\s+push\b[^;&|\n]*[ \t](--force|--force-with-lease|-f)\b"),
        "Note: may overwrite remote history",
    ),
    _Pattern(
        re.compile(r"\bgit\s+clean\b(?![^;&|\n]*(?:-[a-zA-Z]*n|--dry-run))[^;&|\n]*-[a-zA-Z]*f"),
        "Note: may permanently delete untracked files",
    ),
    _Pattern(
        re.compile(r"\bgit\s+checkout\s+(--\s+)?\.[ \t]*($|[;&|\n])"),
        "Note: may discard all working tree changes",
    ),
    _Pattern(
        re.compile(r"\bgit\s+restore\s+(--\s+)?\.[ \t]*($|[;&|\n])"),
        "Note: may discard all working tree changes",
    ),
    _Pattern(
        re.compile(r"\bgit\s+stash[ \t]+(drop|clear)\b"),
        "Note: may permanently remove stashed changes",
    ),
    _Pattern(
        re.compile(r"\bgit\s+branch\s+(-D[ \t]|--delete\s+--force|--force\s+--delete)\b"),
        "Note: may force-delete a branch",
    ),
    _Pattern(
        re.compile(r"\bgit\s+(commit|push|merge)\b[^;&|\n]*--no-verify\b"),
        "Note: may skip safety hooks",
    ),
    _Pattern(re.compile(r"\bgit\s+commit\b[^;&|\n]*--amend\b"), "Note: may rewrite the last commit"),
    _Pattern(
        re.compile(
            r"(^|[;&|\n]\s*)rm\s+-[a-zA-Z]*[rR][a-zA-Z]*f|"
            r"(^|[;&|\n]\s*)rm\s+-[a-zA-Z]*f[a-zA-Z]*[rR]"
        ),
        "Note: may recursively force-remove files",
    ),
    _Pattern(re.compile(r"(^|[;&|\n]\s*)rm\s+-[a-zA-Z]*[rR]"), "Note: may recursively remove files"),
    _Pattern(re.compile(r"(^|[;&|\n]\s*)rm\s+-[a-zA-Z]*f"), "Note: may force-remove files"),
    _Pattern(
        re.compile(r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA)\b", re.I),
        "Note: may drop or truncate database objects",
    ),
    _Pattern(
        re.compile(r"\bDELETE\s+FROM\s+\w+[ \t]*(;|\"|'|\n|$)", re.I),
        "Note: may delete all rows from a database table",
    ),
    _Pattern(re.compile(r"\bkubectl\s+delete\b"), "Note: may delete Kubernetes resources"),
    _Pattern(re.compile(r"\bterraform\s+destroy\b"), "Note: may destroy Terraform infrastructure"),
)


def get_destructive_command_warning(command: str) -> str | None:
    for entry in _DESTRUCTIVE_PATTERNS:
        if entry.pattern.search(command):
            return entry.warning
    return None


__all__ = ["get_destructive_command_warning"]
