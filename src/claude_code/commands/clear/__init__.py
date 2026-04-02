"""
/clear — reset conversation and context.

Migrated from: commands/clear/index.ts
"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

from .caches import clear_session_caches
from .clear_impl import clear_command_call
from .conversation import clear_conversation

CLEAR_COMMAND = CommandSpec(
    type="local",
    name="clear",
    description="Clear conversation history and free up context",
    aliases=("reset", "new"),
    supports_non_interactive=False,
    load_symbol="claude_code.commands.clear.clear_impl",
)

__all__ = [
    "CLEAR_COMMAND",
    "clear_command_call",
    "clear_conversation",
    "clear_session_caches",
]
