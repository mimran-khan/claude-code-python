"""Migrated from: commands/context/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _non_interactive() -> bool:
    return os.environ.get("CLAUDE_CODE_NON_INTERACTIVE", "").lower() in ("1", "true", "yes")


CONTEXT_COMMAND = CommandSpec(
    type="local-jsx",
    name="context",
    description="Visualize current context usage as a colored grid",
    is_enabled=lambda: not _non_interactive(),
    load_symbol="claude_code.commands.context.ui",
)

CONTEXT_NON_INTERACTIVE_COMMAND = CommandSpec(
    type="local",
    name="context",
    supports_non_interactive=True,
    description="Show current context usage",
    is_hidden_fn=lambda: not _non_interactive(),
    is_enabled=_non_interactive,
    load_symbol="claude_code.commands.context.context_noninteractive",
)

__all__ = ["CONTEXT_COMMAND", "CONTEXT_NON_INTERACTIVE_COMMAND"]
