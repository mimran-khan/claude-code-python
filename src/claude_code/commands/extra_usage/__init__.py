"""Migrated from: commands/extra-usage/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _non_interactive() -> bool:
    return os.environ.get("CLAUDE_CODE_NON_INTERACTIVE", "").lower() in ("1", "true", "yes")


def is_extra_usage_allowed() -> bool:
    if os.environ.get("DISABLE_EXTRA_USAGE_COMMAND", "").lower() in ("1", "true", "yes"):
        return False
    return os.environ.get("OVERAGE_PROVISIONING_ALLOWED", "1") != "0"


EXTRA_USAGE_COMMAND = CommandSpec(
    type="local-jsx",
    name="extra-usage",
    description="Configure extra usage to keep working when limits are hit",
    is_enabled=lambda: is_extra_usage_allowed() and not _non_interactive(),
    load_symbol="claude_code.commands.extra_usage.ui",
)

EXTRA_USAGE_NON_INTERACTIVE_COMMAND = CommandSpec(
    type="local",
    name="extra-usage",
    supports_non_interactive=True,
    description="Configure extra usage to keep working when limits are hit",
    is_enabled=lambda: is_extra_usage_allowed() and _non_interactive(),
    is_hidden_fn=lambda: not _non_interactive(),
    load_symbol="claude_code.commands.extra_usage.extra_usage_noninteractive",
)

__all__ = [
    "EXTRA_USAGE_COMMAND",
    "EXTRA_USAGE_NON_INTERACTIVE_COMMAND",
    "is_extra_usage_allowed",
]
