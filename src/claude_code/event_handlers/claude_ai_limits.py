"""
Claude AI quota limits subscription (ported from services/claudeAiLimitsHook.ts).

useState + useEffect listener registration becomes a handler with explicit
subscribe / async cleanup.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from claude_code.services.limits.tracker import (
    add_limits_listener,
    get_current_limits,
    remove_limits_listener,
)
from claude_code.services.limits.types import ClaudeAILimits


@dataclass
class ClaudeAiLimitsHandler:
    """Mirrors useClaudeAiLimits: snapshot updates when global limits change."""

    _limits: ClaudeAILimits = field(init=False)

    def __post_init__(self) -> None:
        self._limits = get_current_limits()

    @property
    def limits(self) -> ClaudeAILimits:
        return self._limits

    def _on_limits(self, new_limits: ClaudeAILimits) -> None:
        self._limits = new_limits

    async def initialize(self) -> None:
        add_limits_listener(self._on_limits)

    async def cleanup(self) -> None:
        remove_limits_listener(self._on_limits)
