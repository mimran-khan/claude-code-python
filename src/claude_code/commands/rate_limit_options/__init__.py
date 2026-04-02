"""Migrated from: commands/rate-limit-options/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _claude_ai_subscriber() -> bool:
    return os.environ.get("CLAUDE_CODE_CLAUDE_AI_SUBSCRIBER", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


RATE_LIMIT_OPTIONS_COMMAND = CommandSpec(
    type="local-jsx",
    name="rate-limit-options",
    description="Show options when rate limit is reached",
    hidden=True,
    is_enabled=_claude_ai_subscriber,
    load_symbol="claude_code.commands.rate_limit_options.ui",
)

__all__ = ["RATE_LIMIT_OPTIONS_COMMAND"]
