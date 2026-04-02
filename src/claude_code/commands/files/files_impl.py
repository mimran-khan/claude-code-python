"""Migrated from: commands/files/files.ts"""

from __future__ import annotations

import os
from typing import Any


async def call(_args: str, context: Any) -> dict[str, str]:
    read_state = getattr(context, "read_file_state", None)
    files: list[str] = []
    if read_state is not None and hasattr(read_state, "cache"):
        files = list(read_state.cache.keys())

    if not files:
        return {"type": "text", "value": "No files in context"}

    cwd = os.getcwd()
    lines = []
    for f in files:
        try:
            rel = os.path.relpath(f, cwd)
        except ValueError:
            rel = f
        lines.append(rel)
    return {"type": "text", "value": "Files in context:\n" + "\n".join(lines)}
