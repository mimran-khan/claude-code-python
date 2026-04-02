"""Migrated from: commands/thinkback-play/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _thinkback_feature_enabled() -> bool:
    v = os.environ.get("FEATURE_TENGU_THINKBACK", os.environ.get("STATSIG_TENGU_THINKBACK", ""))
    return v.strip().lower() in ("1", "true", "yes", "on")


THINKBACK_PLAY_COMMAND = CommandSpec(
    type="local",
    name="thinkback-play",
    description="Play the thinkback animation",
    hidden=True,
    supports_non_interactive=False,
    is_enabled=_thinkback_feature_enabled,
    load_symbol="claude_code.commands.thinkback_play.thinkback_play_impl",
)

__all__ = ["THINKBACK_PLAY_COMMAND"]
