"""Migrated from: commands/files/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec

from .files_impl import call

FILES_COMMAND = CommandSpec(
    type="local",
    name="files",
    description="List all files currently in context",
    is_enabled=lambda: os.environ.get("USER_TYPE") == "ant",
    supports_non_interactive=True,
    load_symbol="claude_code.commands.files.files_impl",
)

__all__ = ["FILES_COMMAND", "call"]
