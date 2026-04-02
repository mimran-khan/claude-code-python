"""Migrated from: commands/tag/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _tag_enabled() -> bool:
    return os.environ.get("USER_TYPE", "") == "ant"


TAG_COMMAND = CommandSpec(
    type="local-jsx",
    name="tag",
    description="Toggle a searchable tag on the current session",
    argument_hint="<tag-name>",
    is_enabled=_tag_enabled,
    load_symbol="claude_code.commands.tag.ui",
)

__all__ = ["TAG_COMMAND"]
