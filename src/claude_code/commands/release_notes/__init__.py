"""Migrated from: commands/release-notes/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

RELEASE_NOTES_COMMAND = CommandSpec(
    type="local",
    name="release-notes",
    description="View release notes",
    supports_non_interactive=True,
    load_symbol="claude_code.commands.release_notes.release_notes_impl",
)

__all__ = ["RELEASE_NOTES_COMMAND"]
