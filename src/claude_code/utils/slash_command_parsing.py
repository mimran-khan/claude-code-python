"""Slash command parsing. Migrated from: utils/slashCommandParsing.ts"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedSlashCommand:
    command_name: str
    args: str
    is_mcp: bool


def parse_slash_command(input_text: str) -> ParsedSlashCommand | None:
    trimmed = input_text.strip()
    if not trimmed.startswith("/"):
        return None
    without_slash = trimmed[1:]
    words = without_slash.split(" ")
    if not words or not words[0]:
        return None
    command_name = words[0]
    is_mcp = False
    args_start = 1
    if len(words) > 1 and words[1] == "(MCP)":
        command_name = f"{command_name} (MCP)"
        is_mcp = True
        args_start = 2
    args = " ".join(words[args_start:])
    return ParsedSlashCommand(command_name=command_name, args=args, is_mcp=is_mcp)
