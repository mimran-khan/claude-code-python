"""
Resolve default shell for input-box ``!`` commands.

Migrated from: utils/shell/resolveDefaultShell.ts

Resolution order:
    merged settings ``defaultShell`` → ``bash``

Platform default is ``bash`` everywhere — we do **not** auto-flip Windows to
PowerShell (would break existing Windows users with bash hooks).
"""

from __future__ import annotations

from claude_code.utils.settings import get_merged_settings

from .shell_provider import SHELL_TYPES, ShellType


def resolve_default_shell() -> ShellType:
    merged = get_merged_settings()
    raw = merged.get("defaultShell")
    if isinstance(raw, str) and raw in SHELL_TYPES:
        return raw  # type: ignore[return-value]
    return "bash"


__all__ = ["resolve_default_shell"]
