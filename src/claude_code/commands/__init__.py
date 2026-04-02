"""
Commands module.

CLI and interactive commands for Claude Code.

Migrated from: commands/*.ts

Batch 2 Python packages (mirroring `commands/` subfolders) live as submodules,
for example `claude_code.commands.hooks`, `claude_code.commands.init_verifiers`,
`claude_code.commands.plugins`, `claude_code.commands.remote`, etc.
"""

# Import builtin commands
from . import builtin, commands_manifest, protocols, spec
from .base import (
    Command,
    CommandContext,
    CommandResult,
    CommandType,
)
from .registry import (
    CommandRegistry,
    get_all_commands,
    get_command,
    register_command,
)

__all__ = [
    "Command",
    "CommandResult",
    "CommandContext",
    "CommandType",
    "CommandRegistry",
    "register_command",
    "get_command",
    "get_all_commands",
    "builtin",
    "commands_manifest",
    "protocols",
    "spec",
]
