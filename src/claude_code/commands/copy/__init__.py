"""Migrated from: commands/copy/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

COPY_COMMAND = CommandSpec(
    type="local-jsx",
    name="copy",
    description=("Copy Claude's last response to clipboard (or /copy N for the Nth-latest)"),
    load_symbol="claude_code.commands.copy.ui",
)

__all__ = ["COPY_COMMAND"]
