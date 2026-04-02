"""
/branch — fork the current conversation.

Migrated from: commands/branch/index.ts
"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec

from .branch_logic import derive_first_prompt

_fork_subagent = os.environ.get("FORK_SUBAGENT", "").lower() in ("1", "true", "yes")
_BRANCH_ALIASES: tuple[str, ...] = () if _fork_subagent else ("fork",)

BRANCH_COMMAND = CommandSpec(
    type="local-jsx",
    name="branch",
    description="Create a branch of the current conversation at this point",
    aliases=_BRANCH_ALIASES,
    argument_hint="[name]",
    load_symbol="claude_code.commands.branch.ui",
)

__all__ = ["BRANCH_COMMAND", "derive_first_prompt"]
