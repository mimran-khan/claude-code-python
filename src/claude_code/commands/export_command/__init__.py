"""Migrated from: commands/export/index.ts (handler: export/export.tsx → ui.py)."""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

EXPORT_COMMAND = CommandSpec(
    type="local-jsx",
    name="export",
    description="Export the current conversation to a file or clipboard",
    argument_hint="[filename]",
    load_symbol="claude_code.commands.export_command.ui",
)

__all__ = ["EXPORT_COMMAND"]
