"""
Portable git worktree listing (stdlib only, no heavy CLI deps).

Migrated from: utils/getWorktreePathsPortable.ts
"""

from __future__ import annotations

import subprocess
import unicodedata

from .subprocess import run_async


def _parse_worktree_porcelain(stdout: str) -> list[str]:
    if not stdout:
        return []
    prefix = "worktree "
    out: list[str] = []
    for line in stdout.split("\n"):
        if line.startswith(prefix):
            path = line[len(prefix) :]
            out.append(unicodedata.normalize("NFC", path))
    return out


async def get_worktree_paths_portable(cwd: str) -> list[str]:
    """Run ``git worktree list --porcelain`` and return worktree paths."""
    try:
        result = await run_async(
            ["git", "worktree", "list", "--porcelain"],
            cwd=cwd,
            timeout=5.0,
        )
    except (FileNotFoundError, OSError):
        return []
    if result.returncode != 0:
        return []
    return _parse_worktree_porcelain(result.stdout)


def get_worktree_paths_portable_sync(cwd: str) -> list[str]:
    """Synchronous ``git worktree list`` (avoids nested asyncio loops)."""
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    if proc.returncode != 0:
        return []
    return _parse_worktree_porcelain(proc.stdout or "")
