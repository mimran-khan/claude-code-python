"""
Worktree mode feature flag (always enabled).

Migrated from: utils/worktreeModeEnabled.ts
"""


def is_worktree_mode_enabled() -> bool:
    """Return whether multi-worktree / worktree mode is enabled."""

    return True


__all__ = ["is_worktree_mode_enabled"]
