"""Warnings for destructive PowerShell operations.

Migrated from: tools/PowerShellTool/destructiveCommandWarning.ts (subset).
"""

from __future__ import annotations

from dataclasses import dataclass

from .command_semantics import analyze_powershell_command


@dataclass
class DestructiveWarning:
    should_warn: bool
    message: str | None = None


def destructive_warning_for_command(command: str) -> DestructiveWarning:
    sem = analyze_powershell_command(command)
    if sem.is_destructive_hint:
        return DestructiveWarning(
            should_warn=True,
            message="Command may delete or stop processes; confirm intent.",
        )
    return DestructiveWarning(should_warn=False)
