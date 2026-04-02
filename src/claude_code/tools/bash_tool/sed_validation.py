"""
Validate ``sed`` commands against read-only / allowlist rules.

Migrated from: tools/BashTool/sedValidation.ts (subset — line-printing & allowlist core).
"""

from __future__ import annotations

import re


def _validate_flags_against_allowlist(flags: list[str], allowed: frozenset[str]) -> bool:
    for flag in flags:
        if flag.startswith("-") and not flag.startswith("--") and len(flag) > 2:
            for ch in flag[1:]:
                if f"-{ch}" not in allowed:
                    return False
        elif flag not in allowed:
            return False
    return True


_LINE_PRINT_ALLOWED = frozenset(
    {
        "-n",
        "--quiet",
        "--silent",
        "-E",
        "--regexp-extended",
        "-r",
        "-z",
        "--zero-terminated",
        "--posix",
    },
)


def is_line_printing_command(command: str, expressions: list[str]) -> bool:
    if not re.match(r"^\s*sed\s+", command):
        return False
    if not expressions:
        return False
    flags: list[str] = []
    for token in command.split():
        if token.startswith("-") and token != "--":
            flags.append(token)
    if not _validate_flags_against_allowlist(flags, _LINE_PRINT_ALLOWED):
        return False
    return all(re.search(r"\d+p(?:;|$)|[,;]\d+p", expr) for expr in expressions)


def sed_command_is_allowed_by_allowlist(command: str, *_args: object, **_kwargs: object) -> bool:
    """
    Conservative allowlist gate used by path validation in TS.

    Returns True when no risky ``sed`` patterns are detected.
    """
    if "sed" not in command:
        return True
    return not re.search(r"\bsed\b.*\s-w[\s]", command)


__all__ = ["is_line_printing_command", "sed_command_is_allowed_by_allowlist"]
