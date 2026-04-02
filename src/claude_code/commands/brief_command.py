"""
/brief — Kairos brief-only mode (feature gated).

Migrated from: commands/brief.ts (metadata + config gate; UI in lazy module)
"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _kairos_brief_feature() -> bool:
    return os.environ.get("KAIROS_BRIEF", "").lower() in ("1", "true", "yes") or os.environ.get(
        "KAIROS", ""
    ).lower() in ("1", "true", "yes")


def _brief_enabled() -> bool:
    # GrowthBook + tool entitlement wired in services in full port
    return _kairos_brief_feature()


BRIEF_COMMAND = CommandSpec(
    type="local-jsx",
    name="brief",
    description="Toggle brief-only output mode",
    is_enabled=_brief_enabled,
    is_hidden_fn=lambda: not _brief_enabled(),
    load_symbol="claude_code.commands.brief_ui",
)

__all__ = ["BRIEF_COMMAND"]
