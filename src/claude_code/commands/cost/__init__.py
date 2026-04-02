"""Migrated from: commands/cost/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec

from .cost_impl import cost_call, is_claude_ai_subscriber


def _cost_hidden() -> bool:
    if os.environ.get("USER_TYPE") == "ant":
        return False
    return is_claude_ai_subscriber()


COST_COMMAND = CommandSpec(
    type="local",
    name="cost",
    description="Show the total cost and duration of the current session",
    is_hidden_fn=_cost_hidden,
    supports_non_interactive=True,
    load_symbol="claude_code.commands.cost.cost_impl",
)

__all__ = ["COST_COMMAND", "cost_call"]
