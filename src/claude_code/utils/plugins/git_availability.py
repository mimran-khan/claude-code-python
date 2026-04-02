"""
Git availability check (memoized per session).

Migrated from: utils/plugins/gitAvailability.ts
"""

from __future__ import annotations

import asyncio
import shutil

_git_memo: bool | None = None
_force_unavailable = False


async def check_git_available() -> bool:
    global _git_memo
    if _force_unavailable:
        return False
    if _git_memo is not None:
        return _git_memo

    def _which() -> bool:
        return shutil.which("git") is not None

    _git_memo = await asyncio.to_thread(_which)
    return _git_memo


def mark_git_unavailable() -> None:
    """Poison memoized check after a failed git exec (e.g. macOS xcrun shim)."""
    global _git_memo, _force_unavailable
    _force_unavailable = True
    _git_memo = False


def clear_git_availability_cache() -> None:
    global _git_memo, _force_unavailable
    _git_memo = None
    _force_unavailable = False


__all__ = [
    "check_git_available",
    "clear_git_availability_cache",
    "mark_git_unavailable",
]
