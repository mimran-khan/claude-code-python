"""
Cost tracking for API usage.

This module tracks token usage, costs, and session statistics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..utils.format import format_duration, format_number


@dataclass
class ModelUsage:
    """Usage statistics for a specific model."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    web_search_requests: int = 0
    cost_usd: float = 0.0
    context_window: int = 0
    max_output_tokens: int = 0


@dataclass
class CostState:
    """Global cost tracking state."""

    total_cost_usd: float = 0.0
    total_api_duration: float = 0.0  # milliseconds
    total_api_duration_without_retries: float = 0.0
    total_tool_duration: float = 0.0
    total_duration: float = 0.0  # wall clock time
    total_lines_added: int = 0
    total_lines_removed: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_input_tokens: int = 0
    total_cache_creation_input_tokens: int = 0
    total_web_search_requests: int = 0
    has_unknown_model_cost: bool = False
    model_usage: dict[str, ModelUsage] = field(default_factory=dict)
    last_duration: float | None = None


# Global state
_cost_state = CostState()


def get_total_cost() -> float:
    """Get total cost in USD."""
    return _cost_state.total_cost_usd


def get_total_cost_usd() -> float:
    """Get total cost in USD (alias)."""
    return _cost_state.total_cost_usd


def get_total_duration() -> float:
    """Get total wall clock duration in milliseconds."""
    return _cost_state.total_duration


def get_total_api_duration() -> float:
    """Get total API duration in milliseconds."""
    return _cost_state.total_api_duration


def get_total_api_duration_without_retries() -> float:
    """Get total API duration without retries in milliseconds."""
    return _cost_state.total_api_duration_without_retries


def get_total_tool_duration() -> float:
    """Get total tool execution duration in milliseconds."""
    return _cost_state.total_tool_duration


def get_total_lines_added() -> int:
    """Get total lines of code added."""
    return _cost_state.total_lines_added


def get_total_lines_removed() -> int:
    """Get total lines of code removed."""
    return _cost_state.total_lines_removed


def get_total_input_tokens() -> int:
    """Get total input tokens used."""
    return _cost_state.total_input_tokens


def get_total_output_tokens() -> int:
    """Get total output tokens used."""
    return _cost_state.total_output_tokens


def get_total_cache_read_input_tokens() -> int:
    """Get total cache read input tokens."""
    return _cost_state.total_cache_read_input_tokens


def get_total_cache_creation_input_tokens() -> int:
    """Get total cache creation input tokens."""
    return _cost_state.total_cache_creation_input_tokens


def get_total_web_search_requests() -> int:
    """Get total web search requests."""
    return _cost_state.total_web_search_requests


def has_unknown_model_cost() -> bool:
    """Check if there are costs from unknown models."""
    return _cost_state.has_unknown_model_cost


def set_has_unknown_model_cost(value: bool) -> None:
    """Set whether there are unknown model costs."""
    _cost_state.has_unknown_model_cost = value


def get_model_usage() -> dict[str, ModelUsage]:
    """Get usage by model."""
    return _cost_state.model_usage.copy()


def get_usage_for_model(model: str) -> ModelUsage | None:
    """Get usage for a specific model."""
    return _cost_state.model_usage.get(model)


def add_to_total_lines_changed(lines_added: int, lines_removed: int) -> None:
    """Add to total lines changed."""
    _cost_state.total_lines_added += lines_added
    _cost_state.total_lines_removed += lines_removed


def add_to_total_cost_state(
    cost: float,
    model_usage: ModelUsage,
    model: str,
) -> None:
    """Add to the total cost state."""
    _cost_state.total_cost_usd += cost
    _cost_state.total_input_tokens += model_usage.input_tokens
    _cost_state.total_output_tokens += model_usage.output_tokens
    _cost_state.total_cache_read_input_tokens += model_usage.cache_read_input_tokens
    _cost_state.total_cache_creation_input_tokens += model_usage.cache_creation_input_tokens
    _cost_state.total_web_search_requests += model_usage.web_search_requests
    _cost_state.model_usage[model] = model_usage


def add_to_total_api_duration(duration: float, include_retries: bool = True) -> None:
    """Add to total API duration."""
    _cost_state.total_api_duration += duration
    if include_retries:
        _cost_state.total_api_duration_without_retries += duration


def add_to_total_tool_duration(duration: float) -> None:
    """Add to total tool duration."""
    _cost_state.total_tool_duration += duration


def set_total_duration(duration: float) -> None:
    """Set total wall clock duration."""
    _cost_state.total_duration = duration


def reset_cost_state() -> None:
    """Reset all cost state."""
    global _cost_state
    _cost_state = CostState()


def reset_state_for_tests() -> None:
    """Reset state for testing."""
    reset_cost_state()


def set_cost_state_for_restore(data: dict[str, Any]) -> None:
    """Restore cost state from saved data."""
    _cost_state.total_cost_usd = data.get("totalCostUSD", 0.0)
    _cost_state.total_api_duration = data.get("totalAPIDuration", 0.0)
    _cost_state.total_api_duration_without_retries = data.get("totalAPIDurationWithoutRetries", 0.0)
    _cost_state.total_tool_duration = data.get("totalToolDuration", 0.0)
    _cost_state.total_lines_added = data.get("totalLinesAdded", 0)
    _cost_state.total_lines_removed = data.get("totalLinesRemoved", 0)
    _cost_state.last_duration = data.get("lastDuration")
    if data.get("modelUsage"):
        for model, usage in data["modelUsage"].items():
            _cost_state.model_usage[model] = ModelUsage(
                input_tokens=usage.get("inputTokens", 0),
                output_tokens=usage.get("outputTokens", 0),
                cache_read_input_tokens=usage.get("cacheReadInputTokens", 0),
                cache_creation_input_tokens=usage.get("cacheCreationInputTokens", 0),
                web_search_requests=usage.get("webSearchRequests", 0),
                cost_usd=usage.get("costUSD", 0.0),
                context_window=usage.get("contextWindow", 0),
                max_output_tokens=usage.get("maxOutputTokens", 0),
            )


def format_cost(cost: float, max_decimal_places: int = 4) -> str:
    """Format a cost value as a string."""
    if cost > 0.5:
        return f"${cost:.2f}"
    return f"${cost:.{max_decimal_places}f}"


def _format_model_usage() -> str:
    """Format model usage for display."""
    model_usage_map = get_model_usage()
    if not model_usage_map:
        return "Usage:                 0 input, 0 output, 0 cache read, 0 cache write"

    result = "Usage by model:"
    for model, usage in model_usage_map.items():
        usage_string = (
            f"  {format_number(usage.input_tokens)} input, "
            f"{format_number(usage.output_tokens)} output, "
            f"{format_number(usage.cache_read_input_tokens)} cache read, "
            f"{format_number(usage.cache_creation_input_tokens)} cache write"
        )
        if usage.web_search_requests > 0:
            usage_string += f", {format_number(usage.web_search_requests)} web search"
        usage_string += f" ({format_cost(usage.cost_usd)})"
        result += f"\n{model}:".rjust(21) + usage_string
    return result


def format_total_cost() -> str:
    """Format the total cost summary for display."""
    cost_display = format_cost(get_total_cost_usd())
    if has_unknown_model_cost():
        cost_display += " (costs may be inaccurate due to usage of unknown models)"

    model_usage_display = _format_model_usage()
    lines_added = get_total_lines_added()
    lines_removed = get_total_lines_removed()
    lines_added_word = "line" if lines_added == 1 else "lines"
    lines_removed_word = "line" if lines_removed == 1 else "lines"

    return (
        f"Total cost:            {cost_display}\n"
        f"Total duration (API):  {format_duration(int(get_total_api_duration()))}\n"
        f"Total duration (wall): {format_duration(int(get_total_duration()))}\n"
        f"Total code changes:    {lines_added} {lines_added_word} added, "
        f"{lines_removed} {lines_removed_word} removed\n"
        f"{model_usage_display}"
    )


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
    model_usage: dict[str, ModelUsage] | None = None


def get_stored_session_costs(session_id: str) -> StoredCostState | None:
    """
    Get stored cost state from project config for a specific session.

    Returns the cost data if the session ID matches, or None otherwise.
    """
    from ..config import get_current_project_config

    project_config = get_current_project_config()

    if project_config.get("last_session_id") != session_id:
        return None

    return StoredCostState(
        total_cost_usd=project_config.get("last_cost", 0.0),
        total_api_duration=project_config.get("last_api_duration", 0.0),
        total_api_duration_without_retries=project_config.get("last_api_duration_without_retries", 0.0),
        total_tool_duration=project_config.get("last_tool_duration", 0.0),
        total_lines_added=project_config.get("last_lines_added", 0),
        total_lines_removed=project_config.get("last_lines_removed", 0),
        last_duration=project_config.get("last_duration"),
        model_usage=project_config.get("last_model_usage"),
    )


def restore_cost_state_for_session(session_id: str) -> bool:
    """
    Restore cost state from project config when resuming a session.

    Returns True if cost state was restored, False otherwise.
    """
    data = get_stored_session_costs(session_id)
    if data is None:
        return False

    _cost_state.total_cost_usd = data.total_cost_usd
    _cost_state.total_api_duration = data.total_api_duration
    _cost_state.total_api_duration_without_retries = data.total_api_duration_without_retries
    _cost_state.total_tool_duration = data.total_tool_duration
    _cost_state.total_lines_added = data.total_lines_added
    _cost_state.total_lines_removed = data.total_lines_removed
    _cost_state.last_duration = data.last_duration
    return True


def save_current_session_costs(fps_metrics: dict[str, float] | None = None) -> None:
    """
    Save the current session's costs to project config.

    Call this before switching sessions to avoid losing accumulated costs.
    """
    from ..bootstrap.state import get_session_id
    from ..config import save_current_project_config

    def update_config(current: dict[str, Any]) -> dict[str, Any]:
        return {
            **current,
            "last_cost": get_total_cost_usd(),
            "last_api_duration": get_total_api_duration(),
            "last_api_duration_without_retries": get_total_api_duration_without_retries(),
            "last_tool_duration": get_total_tool_duration(),
            "last_duration": get_total_duration(),
            "last_lines_added": get_total_lines_added(),
            "last_lines_removed": get_total_lines_removed(),
            "last_total_input_tokens": get_total_input_tokens(),
            "last_total_output_tokens": get_total_output_tokens(),
            "last_total_cache_creation_input_tokens": get_total_cache_creation_input_tokens(),
            "last_total_cache_read_input_tokens": get_total_cache_read_input_tokens(),
            "last_total_web_search_requests": get_total_web_search_requests(),
            "last_fps_average": fps_metrics.get("average_fps") if fps_metrics else None,
            "last_fps_low_1pct": fps_metrics.get("low_1pct_fps") if fps_metrics else None,
            "last_model_usage": {
                model: {
                    "inputTokens": usage.input_tokens,
                    "outputTokens": usage.output_tokens,
                    "cacheReadInputTokens": usage.cache_read_input_tokens,
                    "cacheCreationInputTokens": usage.cache_creation_input_tokens,
                    "webSearchRequests": usage.web_search_requests,
                    "costUSD": usage.cost_usd,
                }
                for model, usage in get_model_usage().items()
            },
            "last_session_id": get_session_id(),
        }

    save_current_project_config(update_config)


def add_to_total_session_cost(
    cost: float,
    usage: dict[str, Any],
    model: str,
) -> float:
    """
    Add usage to the total session cost.

    Returns the total cost added (including any advisor usage).
    """
    model_usage = ModelUsage(
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cache_read_input_tokens=usage.get("cache_read_input_tokens", 0),
        cache_creation_input_tokens=usage.get("cache_creation_input_tokens", 0),
        web_search_requests=usage.get("server_tool_use", {}).get("web_search_requests", 0),
        cost_usd=cost,
    )

    add_to_total_cost_state(cost, model_usage, model)

    return cost
