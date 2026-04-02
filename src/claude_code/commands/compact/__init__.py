"""Migrated from: commands/compact/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _compact_enabled() -> bool:
    return os.environ.get("DISABLE_COMPACT", "").lower() not in ("1", "true", "yes")


COMPACT_COMMAND = CommandSpec(
    type="local",
    name="compact",
    description=(
        "Clear conversation history but keep a summary in context. Optional: /compact [instructions for summarization]"
    ),
    is_enabled=_compact_enabled,
    supports_non_interactive=True,
    argument_hint="<optional custom summarization instructions>",
    load_symbol="claude_code.commands.compact.compact_impl",
)

__all__ = ["COMPACT_COMMAND"]
