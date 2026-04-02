"""TS path parity for ``utils/completionCache.ts``."""

from __future__ import annotations

from claude_code.utils.caching.completion_cache import (
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
