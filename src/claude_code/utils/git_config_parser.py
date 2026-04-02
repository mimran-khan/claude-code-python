"""
Lightweight parser for .git/config files.

Migrated from: utils/git/gitConfigParser.ts
"""

from __future__ import annotations

import os


async def parse_git_config_value(
    git_dir: str,
    section: str,
    subsection: str | None,
    key: str,
) -> str | None:
    """Parse a single value from .git/config."""
    path = os.path.join(git_dir, "config")
    try:
        with open(path, encoding="utf-8") as f:
            return parse_config_string(f.read(), section, subsection, key)
    except OSError:
        return None


def parse_config_string(
    config: str,
    section: str,
    subsection: str | None,
    key: str,
) -> str | None:
    """Parse a config value from an in-memory config string."""
    lines = config.split("\n")
    section_lower = section.lower()
    key_lower = key.lower()
    in_section = False
    for line in lines:
        trimmed = line.strip()
        if not trimmed or trimmed[0] in "#;":
            continue
        if trimmed[0] == "[":
            in_section = _matches_section_header(trimmed, section_lower, subsection)
            continue
        if not in_section:
            continue
        parsed = _parse_key_value(trimmed)
        if parsed and parsed[0].lower() == key_lower:
            return parsed[1]
    return None


def _parse_key_value(line: str) -> tuple[str, str] | None:
    i = 0
    while i < len(line) and _is_key_char(line[i]):
        i += 1
    if i == 0:
        return None
    key = line[:i]
    while i < len(line) and line[i] in " \t":
        i += 1
    if i >= len(line) or line[i] != "=":
        return None
    i += 1
    while i < len(line) and line[i] in " \t":
        i += 1
    value = _parse_value(line, i)
    return key, value


def _parse_value(line: str, start: int) -> str:
    result: list[str] = []
    in_quote = False
    i = start
    while i < len(line):
        ch = line[i]
        if not in_quote and ch in "#;":
            break
        if ch == '"':
            in_quote = not in_quote
            i += 1
            continue
        if ch == "\\" and i + 1 < len(line):
            nxt = line[i + 1]
            if in_quote:
                esc = {"n": "\n", "t": "\t", "b": "\b", '"': '"', "\\": "\\"}.get(nxt, nxt)
                result.append(esc)
                i += 2
                continue
            if nxt == "\\":
                result.append("\\")
                i += 2
                continue
        result.append(ch)
        i += 1
    s = "".join(result)
    if not in_quote:
        s = s.rstrip(" \t")
    return s


def _matches_section_header(line: str, section_lower: str, subsection: str | None) -> bool:
    i = 1
    while i < len(line) and line[i] not in '] \t"':
        i += 1
    found_section = line[1:i].lower()
    if found_section != section_lower:
        return False
    if subsection is None:
        return i < len(line) and line[i] == "]"
    while i < len(line) and line[i] in " \t":
        i += 1
    if i >= len(line) or line[i] != '"':
        return False
    i += 1
    found_sub = []
    while i < len(line) and line[i] != '"':
        if line[i] == "\\" and i + 1 < len(line):
            nxt = line[i + 1]
            if nxt in '\\"':
                found_sub.append(nxt)
                i += 2
                continue
            found_sub.append(nxt)
            i += 2
            continue
        found_sub.append(line[i])
        i += 1
    if i >= len(line) or line[i] != '"':
        return False
    i += 1
    return i < len(line) and line[i] == "]" and "".join(found_sub) == subsection


def _is_key_char(ch: str) -> bool:
    return ch.isalnum() or ch == "-"
