"""
Segmented permission checks for compound bash commands.

Migrated from: tools/BashTool/bashCommandHelpers.ts

Full ``ParsedCommand`` / AST parity lives in TypeScript. Host integrations should
call :func:`segment_bash_command` then apply permission rules per segment.
"""

from __future__ import annotations

from ...utils.bash.commands import split_command


def segment_bash_command(command: str) -> list[str]:
    """Split on ``|`` into pipeline segments (best-effort)."""
    parts: list[str] = []
    for segment in command.split("|"):
        s = segment.strip()
        if s:
            parts.append(s)
    return parts if parts else [command.strip()]


def list_compound_subcommands(command: str) -> list[str]:
    """Split on ``&&`` / ``||`` within a segment."""
    try:
        return split_command(command)
    except Exception:
        return [command]


__all__ = ["list_compound_subcommands", "segment_bash_command"]
