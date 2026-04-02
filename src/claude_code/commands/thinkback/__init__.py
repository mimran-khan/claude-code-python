"""Migrated from: commands/thinkback/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _thinkback_feature_enabled() -> bool:
    """Parity: checkStatsigFeatureGate_CACHED_MAY_BE_STALE('tengu_thinkback')."""

    v = os.environ.get("FEATURE_TENGU_THINKBACK", os.environ.get("STATSIG_TENGU_THINKBACK", ""))
    return v.strip().lower() in ("1", "true", "yes", "on")


THINKBACK_COMMAND = CommandSpec(
    type="local-jsx",
    name="think-back",
    description="Your 2025 Claude Code Year in Review",
    is_enabled=_thinkback_feature_enabled,
    load_symbol="claude_code.commands.thinkback.ui",
)

__all__ = ["THINKBACK_COMMAND"]
