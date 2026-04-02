"""
PowerShell static command-prefix extraction.

Migrated from: utils/tokens.ts (~300 lines, depends on PowerShell AST + fig specs).
Port incrementally alongside `utils/shell` / permission validators.
"""

from __future__ import annotations


async def get_command_prefix_static(_command: str) -> dict[str, str | None] | None:
    """Placeholder: return None until parser + specPrefix port exists."""
    return None


async def get_compound_command_prefixes_static(
    _command: str,
    _exclude_subcommand=None,
) -> list[str]:
    return []
