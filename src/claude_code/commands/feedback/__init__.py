"""Migrated from: commands/feedback/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _feedback_enabled() -> bool:
    if os.environ.get("CLAUDE_CODE_USE_BEDROCK", "").lower() in ("1", "true"):
        return False
    if os.environ.get("CLAUDE_CODE_USE_VERTEX", "").lower() in ("1", "true"):
        return False
    if os.environ.get("CLAUDE_CODE_USE_FOUNDRY", "").lower() in ("1", "true"):
        return False
    if os.environ.get("DISABLE_FEEDBACK_COMMAND", "").lower() in ("1", "true"):
        return False
    if os.environ.get("DISABLE_BUG_COMMAND", "").lower() in ("1", "true"):
        return False
    if os.environ.get("ESSENTIAL_TRAFFIC_ONLY", "").lower() in ("1", "true"):
        return False
    return os.environ.get("USER_TYPE") != "ant"


FEEDBACK_COMMAND = CommandSpec(
    type="local-jsx",
    name="feedback",
    aliases=("bug",),
    description="Submit feedback about Claude Code",
    argument_hint="[report]",
    is_enabled=_feedback_enabled,
    load_symbol="claude_code.commands.feedback.ui",
)

__all__ = ["FEEDBACK_COMMAND"]
