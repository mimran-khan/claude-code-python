"""
/add-dir — add a new working directory (lazy UI load in TypeScript).

Migrated from: commands/add-dir/index.ts
"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

from .validation import (
    add_dir_help_message,
    all_working_directories,
    validate_directory_for_workspace,
)

ADD_DIR_COMMAND = CommandSpec(
    type="local-jsx",
    name="add-dir",
    description="Add a new working directory",
    argument_hint="<path>",
    load_symbol="claude_code.commands.add_dir.ui",
)

__all__ = [
    "ADD_DIR_COMMAND",
    "add_dir_help_message",
    "all_working_directories",
    "validate_directory_for_workspace",
]
