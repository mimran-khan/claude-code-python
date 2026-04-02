"""Migrated from: commands/desktop/index.ts"""

from __future__ import annotations

import platform

from claude_code.commands.spec import CommandSpec


def is_supported_platform() -> bool:
    if platform.system() == "Darwin":
        return True
    return bool(platform.system() == "Windows" and platform.machine().endswith("64"))


DESKTOP_COMMAND = CommandSpec(
    type="local-jsx",
    name="desktop",
    aliases=("app",),
    description="Continue the current session in Claude Desktop",
    availability=("claude-ai",),
    is_enabled=is_supported_platform,
    is_hidden_fn=lambda: not is_supported_platform(),
    load_symbol="claude_code.commands.desktop.ui",
)

__all__ = ["DESKTOP_COMMAND", "is_supported_platform"]
