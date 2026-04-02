"""Migrated from: commands/cost/cost.ts"""

from __future__ import annotations

import os

from claude_code.core.cost_tracker import format_total_cost


def is_claude_ai_subscriber() -> bool:
    return os.environ.get("CLAUDE_AI_SUBSCRIBER", "").lower() in ("1", "true", "yes")


async def cost_call() -> dict[str, str]:
    if is_claude_ai_subscriber():
        value: str
        if os.environ.get("CLAUDE_CODE_USING_OVERAGE", "").lower() in ("1", "true"):
            value = (
                "You are currently using your overages to power your Claude Code usage. "
                "We will automatically switch you back to your subscription rate limits when they reset"
            )
        else:
            value = "You are currently using your subscription to power your Claude Code usage"
        if os.environ.get("USER_TYPE") == "ant":
            value += f"\n\n[ANT-ONLY] Showing cost anyway:\n {format_total_cost()}"
        return {"type": "text", "value": value}
    return {"type": "text", "value": format_total_cost()}
