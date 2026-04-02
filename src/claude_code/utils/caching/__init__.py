"""
Disk-backed caches (shell completions, etc.).

Migrated from: utils/completionCache.ts
"""

from .completion_cache import (
    ShellInfo,
    detect_shell,
    regenerate_completion_cache,
    setup_shell_completion,
)

__all__ = [
    "ShellInfo",
    "detect_shell",
    "regenerate_completion_cache",
    "setup_shell_completion",
]
