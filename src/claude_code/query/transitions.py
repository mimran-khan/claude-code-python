"""
Query loop transitions.

Types for the query loop state machine.

Migrated from: query/transitions.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class TerminalCompleted:
    """Normal completion."""

    reason: Literal["completed"] = "completed"


@dataclass
class TerminalAbortedStreaming:
    """Aborted during streaming."""

    reason: Literal["aborted_streaming"] = "aborted_streaming"


@dataclass
class TerminalAbortedTools:
    """Aborted during tool execution."""

    reason: Literal["aborted_tools"] = "aborted_tools"


@dataclass
class TerminalMaxTurns:
    """Max turns limit reached."""

    reason: Literal["max_turns"] = "max_turns"
    turn_count: int = 0


@dataclass
class TerminalBlockingLimit:
    """Context blocking limit reached."""

    reason: Literal["blocking_limit"] = "blocking_limit"


@dataclass
class TerminalPromptTooLong:
    """Prompt too long error."""

    reason: Literal["prompt_too_long"] = "prompt_too_long"


@dataclass
class TerminalImageError:
    """Image processing error."""

    reason: Literal["image_error"] = "image_error"


@dataclass
class TerminalModelError:
    """Model/API error."""

    reason: Literal["model_error"] = "model_error"
    error: Exception | None = None


@dataclass
class TerminalHookStopped:
    """Hook prevented continuation."""

    reason: Literal["hook_stopped"] = "hook_stopped"


@dataclass
class TerminalStopHookPrevented:
    """Stop hook prevented continuation."""

    reason: Literal["stop_hook_prevented"] = "stop_hook_prevented"


Terminal = (
    TerminalCompleted
    | TerminalAbortedStreaming
    | TerminalAbortedTools
    | TerminalMaxTurns
    | TerminalBlockingLimit
    | TerminalPromptTooLong
    | TerminalImageError
    | TerminalModelError
    | TerminalHookStopped
    | TerminalStopHookPrevented
)

"""Terminal states for query loop exit."""


@dataclass
class ContinueNextTurn:
    """Continue to next turn."""

    reason: Literal["next_turn"] = "next_turn"


@dataclass
class ContinueReactiveCompactRetry:
    """Retry after reactive compact."""

    reason: Literal["reactive_compact_retry"] = "reactive_compact_retry"


@dataclass
class ContinueCollapseDrainRetry:
    """Retry after collapse drain."""

    reason: Literal["collapse_drain_retry"] = "collapse_drain_retry"
    committed: int = 0


@dataclass
class ContinueMaxOutputTokensRecovery:
    """Retry after max output tokens."""

    reason: Literal["max_output_tokens_recovery"] = "max_output_tokens_recovery"
    attempt: int = 0


@dataclass
class ContinueMaxOutputTokensEscalate:
    """Escalate max output tokens."""

    reason: Literal["max_output_tokens_escalate"] = "max_output_tokens_escalate"


@dataclass
class ContinueStopHookBlocking:
    """Continue after stop hook blocking."""

    reason: Literal["stop_hook_blocking"] = "stop_hook_blocking"


@dataclass
class ContinueTokenBudgetContinuation:
    """Continue for token budget."""

    reason: Literal["token_budget_continuation"] = "token_budget_continuation"


Continue = (
    ContinueNextTurn
    | ContinueReactiveCompactRetry
    | ContinueCollapseDrainRetry
    | ContinueMaxOutputTokensRecovery
    | ContinueMaxOutputTokensEscalate
    | ContinueStopHookBlocking
    | ContinueTokenBudgetContinuation
)

"""Continue states for query loop iteration."""
