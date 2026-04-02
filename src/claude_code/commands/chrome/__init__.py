"""
/chrome — Claude in Chrome (Beta) settings.

Migrated from: commands/chrome/index.ts
"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _non_interactive() -> bool:
    return os.environ.get("CLAUDE_CODE_NON_INTERACTIVE", "").lower() in ("1", "true", "yes")


CHROME_COMMAND = CommandSpec(
    type="local-jsx",
    name="chrome",
    description="Claude in Chrome (Beta) settings",
    availability=("claude-ai",),
    is_enabled=lambda: not _non_interactive(),
    load_symbol="claude_code.commands.chrome.ui",
)

__all__ = ["CHROME_COMMAND"]
