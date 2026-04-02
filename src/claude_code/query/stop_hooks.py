"""
Query stop hooks.

Migrated from: query/stopHooks.ts
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class StopReason(Enum):
    """Reasons for stopping a query."""

    END_TURN = "end_turn"
    MAX_TOKENS = "max_tokens"
    TOOL_USE = "tool_use"
    USER_INTERRUPT = "user_interrupt"
    ERROR = "error"
    TOKEN_BUDGET = "token_budget"
    MAX_TURNS = "max_turns"
    STOP_SEQUENCE = "stop_sequence"


@dataclass
class StopHookResult:
    """Result from stop hook evaluation."""

    should_stop: bool
    reason: StopReason | None = None
    message: str | None = None


def should_stop_query(
    messages: list[Any],
    turn_count: int,
    max_turns: int,
    token_count: int,
    token_budget: int | None,
    has_pending_tool_use: bool,
    stop_reason: str | None = None,
) -> StopHookResult:
    """Determine if query should stop.

    Args:
        messages: Current message history
        turn_count: Current turn number
        max_turns: Maximum allowed turns
        token_count: Tokens used in current turn
        token_budget: Token budget limit
        has_pending_tool_use: Whether there's a pending tool use
        stop_reason: Model's stop reason if any

    Returns:
        StopHookResult indicating whether to stop and why
    """
    # Check max turns
    if turn_count >= max_turns:
        return StopHookResult(
            should_stop=True,
            reason=StopReason.MAX_TURNS,
            message=f"Reached maximum turns ({max_turns})",
        )

    # Check token budget
    if token_budget is not None and token_count >= token_budget:
        return StopHookResult(
            should_stop=True,
            reason=StopReason.TOKEN_BUDGET,
            message=f"Reached token budget ({token_budget})",
        )

    # Check model stop reason
    if stop_reason:
        if stop_reason == "end_turn":
            # Natural end of turn - continue if tool use pending
            if has_pending_tool_use:
                return StopHookResult(should_stop=False)
            return StopHookResult(
                should_stop=True,
                reason=StopReason.END_TURN,
            )
        elif stop_reason == "max_tokens":
            return StopHookResult(
                should_stop=True,
                reason=StopReason.MAX_TOKENS,
                message="Reached model max tokens",
            )
        elif stop_reason == "stop_sequence":
            return StopHookResult(
                should_stop=True,
                reason=StopReason.STOP_SEQUENCE,
            )

    # Continue if tool use pending
    if has_pending_tool_use:
        return StopHookResult(should_stop=False)

    # Default: don't stop
    return StopHookResult(should_stop=False)
