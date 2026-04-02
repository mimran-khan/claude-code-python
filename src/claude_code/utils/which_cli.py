"""
Resolve executable paths (`which` / `where.exe`).

Migrated from: utils/which.ts
"""

from __future__ import annotations

import asyncio
import os
import shutil


async def which(command: str) -> str | None:
    """Return absolute path to `command`, or None if not found."""

    def _sync() -> str | None:
        if os.name == "nt":
            # Windows: prefer shutil.which (PATH + PATHEXT)
            return shutil.which(command)
        return shutil.which(command)

    return await asyncio.to_thread(_sync)


def which_sync(command: str) -> str | None:
    return shutil.which(command)
