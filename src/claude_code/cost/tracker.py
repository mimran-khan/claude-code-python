"""
Cost Tracker Implementation.

Tracks API costs and usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelUsage:
    """Usage statistics for a model."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    web_search_requests: int = 0
    cost_usd: float = 0.0
    context_window: int = 0
    max_output_tokens: int = 0


@dataclass
class StoredCostState:
    """Stored cost state for session persistence."""

    total_cost_usd: float = 0.0
    total_api_duration: float = 0.0
    total_api_duration_without_retries: float = 0.0
    total_tool_duration: float = 0.0
    total_lines_added: int = 0
    total_lines_removed: int = 0
    last_duration: float | None = None
    model_usage: dict[str, ModelUsage] = field(default_factory=dict)


def format_cost(cost: float, max_decimal_places: int = 4) -> str:
    """Format a cost value for display.

    Args:
        cost: The cost in USD
        max_decimal_places: Maximum decimal places for small amounts

    Returns:
        The formatted cost string
    """
    if cost > 0.5:
        return f"${round(cost * 100) / 100:.2f}"
    return f"${cost:.{max_decimal_places}f}"


def format_total_cost(tracker: CostTracker) -> str:
    """Format the total cost summary for display.

    Args:
        tracker: The cost tracker

    Returns:
        The formatted cost summary string
    """
    from ..utils.format import format_duration

    cost_display = format_cost(tracker.total_cost_usd)
    if tracker.has_unknown_model_cost:
        cost_display += " (costs may be inaccurate due to unknown models)"

    model_usage_display = _format_model_usage(tracker)

    lines = [
        f"Total cost:            {cost_display}",
        f"Total duration (API):  {format_duration(tracker.total_api_duration)}",
        f"Total duration (wall): {format_duration(tracker.total_duration)}",
        f"Total code changes:    {tracker.total_lines_added} lines added, {tracker.total_lines_removed} lines removed",
        model_usage_display,
    ]

    return "\n".join(lines)


def _format_model_usage(tracker: CostTracker) -> str:
    """Format model usage for display."""
    from ..utils.format import format_number

    if not tracker.model_usage:
        return "Usage:                 0 input, 0 output, 0 cache read, 0 cache write"

    result = "Usage by model:"
    for model, usage in tracker.model_usage.items():
        usage_str = (
            f"  {format_number(usage.input_tokens)} input, "
            f"{format_number(usage.output_tokens)} output, "
            f"{format_number(usage.cache_read_input_tokens)} cache read, "
            f"{format_number(usage.cache_creation_input_tokens)} cache write"
        )
        if usage.web_search_requests > 0:
            usage_str += f", {format_number(usage.web_search_requests)} web search"
        usage_str += f" ({format_cost(usage.cost_usd)})"

        result += f"\n{model:>20}:{usage_str}"

    return result


class CostTracker:
    """Tracks API costs and usage for a session."""

    def __init__(self):
        self.total_cost_usd: float = 0.0
        self.total_api_duration: float = 0.0
        self.total_api_duration_without_retries: float = 0.0
        self.total_tool_duration: float = 0.0
        self.total_duration: float = 0.0
        self.total_lines_added: int = 0
        self.total_lines_removed: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cache_read_tokens: int = 0
        self.total_cache_creation_tokens: int = 0
        self.total_web_search_requests: int = 0
        self.model_usage: dict[str, ModelUsage] = {}
        self.has_unknown_model_cost: bool = False

    def add_cost(
        self,
        cost: float,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        web_search_requests: int = 0,
    ) -> None:
        """Add cost and usage to the tracker.

        Args:
            cost: The cost in USD
            model: The model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_read_tokens: Number of cache read tokens
            cache_creation_tokens: Number of cache creation tokens
            web_search_requests: Number of web search requests
        """
        self.total_cost_usd += cost
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cache_read_tokens += cache_read_tokens
        self.total_cache_creation_tokens += cache_creation_tokens
        self.total_web_search_requests += web_search_requests

        # Update model usage
        if model not in self.model_usage:
            self.model_usage[model] = ModelUsage()

        usage = self.model_usage[model]
        usage.input_tokens += input_tokens
        usage.output_tokens += output_tokens
        usage.cache_read_input_tokens += cache_read_tokens
        usage.cache_creation_input_tokens += cache_creation_tokens
        usage.web_search_requests += web_search_requests
        usage.cost_usd += cost

    def add_lines_changed(self, added: int, removed: int) -> None:
        """Add lines changed to the tracker.

        Args:
            added: Number of lines added
            removed: Number of lines removed
        """
        self.total_lines_added += added
        self.total_lines_removed += removed

    def add_api_duration(
        self,
        duration: float,
        *,
        include_retries: bool = True,
    ) -> None:
        """Add API duration to the tracker.

        Args:
            duration: The duration in milliseconds
            include_retries: Whether this duration includes retries
        """
        self.total_api_duration += duration
        if include_retries:
            self.total_api_duration_without_retries += duration

    def add_tool_duration(self, duration: float) -> None:
        """Add tool duration to the tracker.

        Args:
            duration: The duration in milliseconds
        """
        self.total_tool_duration += duration

    def set_total_duration(self, duration: float) -> None:
        """Set the total wall duration.

        Args:
            duration: The total duration in milliseconds
        """
        self.total_duration = duration

    def reset(self) -> None:
        """Reset all counters."""
        self.total_cost_usd = 0.0
        self.total_api_duration = 0.0
        self.total_api_duration_without_retries = 0.0
        self.total_tool_duration = 0.0
        self.total_duration = 0.0
        self.total_lines_added = 0
        self.total_lines_removed = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_read_tokens = 0
        self.total_cache_creation_tokens = 0
        self.total_web_search_requests = 0
        self.model_usage.clear()
        self.has_unknown_model_cost = False

    def to_stored_state(self) -> StoredCostState:
        """Convert to stored state for persistence."""
        return StoredCostState(
            total_cost_usd=self.total_cost_usd,
            total_api_duration=self.total_api_duration,
            total_api_duration_without_retries=self.total_api_duration_without_retries,
            total_tool_duration=self.total_tool_duration,
            total_lines_added=self.total_lines_added,
            total_lines_removed=self.total_lines_removed,
            model_usage=self.model_usage.copy(),
        )

    def restore_from_state(self, state: StoredCostState) -> None:
        """Restore from stored state."""
        self.total_cost_usd = state.total_cost_usd
        self.total_api_duration = state.total_api_duration
        self.total_api_duration_without_retries = state.total_api_duration_without_retries
        self.total_tool_duration = state.total_tool_duration
        self.total_lines_added = state.total_lines_added
        self.total_lines_removed = state.total_lines_removed
        if state.last_duration is not None:
            self.total_duration = state.last_duration
        self.model_usage = state.model_usage.copy()
