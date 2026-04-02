"""
Resolve executable on PATH (spawn-rx ``findActualExecutable`` shape).

Migrated from: utils/findExecutable.ts
"""

from __future__ import annotations

from .which_cli import which_sync


def find_executable(exe: str, args: list[str]) -> dict[str, object]:
    """Return ``{"cmd": resolved_or_original, "args": args}``."""

    resolved = which_sync(exe)
    return {"cmd": resolved if resolved is not None else exe, "args": args}


__all__ = ["find_executable"]
