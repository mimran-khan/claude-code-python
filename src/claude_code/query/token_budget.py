"""
Token budget tracking and decisions.

Migrated from: query/tokenBudget.ts
"""

import time
from dataclasses import dataclass
from typing import Any, Literal

COMPLETION_THRESHOLD = 0.9
DIMINISHING_THRESHOLD = 500


@dataclass
class BudgetTracker:
    """Tracks token budget consumption."""

    continuation_count: int = 0
    last_delta_tokens: int = 0
    last_global_turn_tokens: int = 0
    started_at: float = 0.0


def create_budget_tracker() -> BudgetTracker:
    """Create a new budget tracker."""
    return BudgetTracker(started_at=time.time() * 1000)


@dataclass
class ContinueDecision:
    """Decision to continue query."""

    action: Literal["continue"] = "continue"
    nudge_message: str = ""
    continuation_count: int = 0
    pct: int = 0
    turn_tokens: int = 0
    budget: int = 0


@dataclass
class StopDecision:
    """Decision to stop query."""

    action: Literal["stop"] = "stop"
    completion_event: dict[str, Any] | None = None


TokenBudgetDecision = ContinueDecision | StopDecision


def get_budget_continuation_message(pct: int, turn_tokens: int, budget: int) -> str:
    """Generate budget continuation nudge message."""
    return f"[Token budget: {pct}% used ({turn_tokens}/{budget} tokens). Continue working on the task.]"


def check_token_budget(
    tracker: BudgetTracker,
    agent_id: str | None,
    budget: int | None,
    global_turn_tokens: int,
) -> TokenBudgetDecision:
    """Check token budget and decide whether to continue or stop.

    Args:
        tracker: Budget tracking state
        agent_id: Current agent ID (sub-agents don't use budgets)
        budget: Token budget limit (None = no limit)
        global_turn_tokens: Total tokens used in turn

    Returns:
        Decision to continue or stop
    """
    # Sub-agents or no budget = immediate stop (no budget nudging)
    if agent_id or budget is None or budget <= 0:
        return StopDecision(completion_event=None)

    turn_tokens = global_turn_tokens
    pct = round((turn_tokens / budget) * 100)
    delta_since_last_check = global_turn_tokens - tracker.last_global_turn_tokens

    # Check for diminishing returns
    is_diminishing = (
        tracker.continuation_count >= 3
        and delta_since_last_check < DIMINISHING_THRESHOLD
        and tracker.last_delta_tokens < DIMINISHING_THRESHOLD
    )

    # Continue if not diminishing and under threshold
    if not is_diminishing and turn_tokens < budget * COMPLETION_THRESHOLD:
        tracker.continuation_count += 1
        tracker.last_delta_tokens = delta_since_last_check
        tracker.last_global_turn_tokens = global_turn_tokens
        return ContinueDecision(
            nudge_message=get_budget_continuation_message(pct, turn_tokens, budget),
            continuation_count=tracker.continuation_count,
            pct=pct,
            turn_tokens=turn_tokens,
            budget=budget,
        )

    # Stop with completion event
    if is_diminishing or tracker.continuation_count > 0:
        duration_ms = (time.time() * 1000) - tracker.started_at
        return StopDecision(
            completion_event={
                "continuation_count": tracker.continuation_count,
                "pct": pct,
                "turn_tokens": turn_tokens,
                "budget": budget,
                "diminishing_returns": is_diminishing,
                "duration_ms": duration_ms,
            }
        )

    return StopDecision(completion_event=None)
