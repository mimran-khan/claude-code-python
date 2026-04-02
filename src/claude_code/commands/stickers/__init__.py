"""Migrated from: commands/stickers/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

STICKERS_COMMAND = CommandSpec(
    type="local",
    name="stickers",
    description="Order Claude Code stickers",
    supports_non_interactive=False,
    load_symbol="claude_code.commands.stickers.stickers_impl",
)

__all__ = ["STICKERS_COMMAND"]
