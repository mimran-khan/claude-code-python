"""
Query error recovery budget (ported from query.ts max-output-tokens / overflow paths).

Tracks recovery attempts alongside :class:`claude_code.query.query.QueryState`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from claude_code.query.query import MAX_OUTPUT_TOKENS_RECOVERY_LIMIT


@dataclass
class ErrorRecoveryHandler:
    """Session-local counter for automated recovery (e.g. max_output_tokens)."""

    max_output_tokens_recovery_count: int = 0
    has_attempted_reactive_compact: bool = False

    _withheld_recoverable: bool = field(default=False, repr=False)

    def can_retry_max_output_tokens(self) -> bool:
        return self.max_output_tokens_recovery_count < MAX_OUTPUT_TOKENS_RECOVERY_LIMIT

    def record_max_output_tokens_recovery(self) -> bool:
        """
        Increment recovery counter. Returns False if the budget is exhausted.
        """
        if not self.can_retry_max_output_tokens():
            return False
        self.max_output_tokens_recovery_count += 1
        return True

    def reset_recovery_counters(self) -> None:
        self.max_output_tokens_recovery_count = 0
        self.has_attempted_reactive_compact = False
        self._withheld_recoverable = False

    def set_withheld_recoverable(self, value: bool) -> None:
        self._withheld_recoverable = value

    @property
    def withheld_recoverable(self) -> bool:
        return self._withheld_recoverable
