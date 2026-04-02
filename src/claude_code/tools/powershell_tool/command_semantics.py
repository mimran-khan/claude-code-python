"""Lightweight PowerShell command classification (destructive hints)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CommandSemantics:
    is_destructive_hint: bool = False


def analyze_powershell_command(command: str) -> CommandSemantics:
    lower = command.lower()
    hints = (
        "remove-item",
        "ri ",
        "rm ",
        "del ",
        "erase ",
        "clear-recyclebin",
        "format-volume",
        "stop-process",
        "spps ",
    )
    if any(h in lower for h in hints):
        return CommandSemantics(is_destructive_hint=True)
    return CommandSemantics(is_destructive_hint=False)
