"""
Session / workspace bootstrap.

Migrated from: setup.ts (entry surface; full wiring lives in entrypoints/init).
"""

from __future__ import annotations


async def setup(
    cwd: str,
    permission_mode: str,
    allow_dangerously_skip_permissions: bool,
    worktree_enabled: bool,
    worktree_name: str | None,
    tmux_enabled: bool,
    custom_session_id: str | None = None,
    worktree_pr_number: int | None = None,
    messaging_socket_path: str | None = None,
) -> None:
    _ = (
        permission_mode,
        allow_dangerously_skip_permissions,
        worktree_enabled,
        worktree_name,
        tmux_enabled,
        custom_session_id,
        worktree_pr_number,
        messaging_socket_path,
    )
    import os

    os.chdir(cwd)
    from .entrypoints.init import initialize

    await initialize()


__all__ = ["setup"]
