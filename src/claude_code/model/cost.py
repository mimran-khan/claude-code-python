"""
Model Cost Calculation.

Handles pricing and cost calculation for model usage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelCosts:
    """Cost configuration for a model (per million tokens)."""

    input_tokens: float
    output_tokens: float
    prompt_cache_write_tokens: float
    prompt_cache_read_tokens: float
    web_search_requests: float = 0.01


# Standard pricing tiers
COST_TIER_3_15 = ModelCosts(
    input_tokens=3.0,
    output_tokens=15.0,
    prompt_cache_write_tokens=3.75,
    prompt_cache_read_tokens=0.3,
)

COST_TIER_15_75 = ModelCosts(
    input_tokens=15.0,
    output_tokens=75.0,
    prompt_cache_write_tokens=18.75,
    prompt_cache_read_tokens=1.5,
)

COST_TIER_5_25 = ModelCosts(
    input_tokens=5.0,
    output_tokens=25.0,
    prompt_cache_write_tokens=6.25,
    prompt_cache_read_tokens=0.5,
)

COST_TIER_30_150 = ModelCosts(
    input_tokens=30.0,
    output_tokens=150.0,
    prompt_cache_write_tokens=37.5,
    prompt_cache_read_tokens=3.0,
)

COST_HAIKU_35 = ModelCosts(
    input_tokens=0.8,
    output_tokens=4.0,
    prompt_cache_write_tokens=1.0,
    prompt_cache_read_tokens=0.08,
)

COST_HAIKU_45 = ModelCosts(
    input_tokens=1.0,
    output_tokens=5.0,
    prompt_cache_write_tokens=1.25,
    prompt_cache_read_tokens=0.1,
)

# Model to cost tier mapping
MODEL_COSTS: dict[str, ModelCosts] = {
    # Sonnet 4 series
    "claude-sonnet-4-20250514": COST_TIER_3_15,
    "claude-4-sonnet-20250514": COST_TIER_3_15,
    # Opus 4 series
    "claude-opus-4-20250514": COST_TIER_15_75,
    "claude-4-opus-20250514": COST_TIER_15_75,
    # Haiku 3.5 series
    "claude-3-5-haiku-20241022": COST_HAIKU_35,
    # Sonnet 3.5 series
    "claude-3-5-sonnet-20241022": COST_TIER_3_15,
    "claude-3-5-sonnet-20240620": COST_TIER_3_15,
    # Opus 3 series
    "claude-3-opus-20240229": COST_TIER_15_75,
}

# Default costs for unknown models
DEFAULT_COSTS = COST_TIER_3_15


def get_model_costs(model: str) -> ModelCosts:
    """Get the cost configuration for a model.

    Args:
        model: The model name

    Returns:
        ModelCosts configuration for the model
    """
    return MODEL_COSTS.get(model, DEFAULT_COSTS)


def get_model_input_cost_per_token(model: str) -> float:
    """Get the input cost per token for a model.

    Args:
        model: The model name

    Returns:
        Cost per input token (in dollars)
    """
    costs = get_model_costs(model)
    return costs.input_tokens / 1_000_000


def get_model_output_cost_per_token(model: str) -> float:
    """Get the output cost per token for a model.

    Args:
        model: The model name

    Returns:
        Cost per output token (in dollars)
    """
    costs = get_model_costs(model)
    return costs.output_tokens / 1_000_000


def calculate_cost_from_tokens(
    model: str,
    input_tokens: int,
    output_tokens: int,
    *,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
) -> float:
    """Calculate the cost from token counts.

    Args:
        model: The model name
        input_tokens: Number of input tokens (excluding cache)
        output_tokens: Number of output tokens
        cache_creation_input_tokens: Number of tokens written to cache
        cache_read_input_tokens: Number of tokens read from cache

    Returns:
        Total cost in dollars
    """
    costs = get_model_costs(model)

    # Calculate per-million costs
    base_input_cost = (input_tokens / 1_000_000) * costs.input_tokens
    output_cost = (output_tokens / 1_000_000) * costs.output_tokens
    cache_write_cost = (cache_creation_input_tokens / 1_000_000) * costs.prompt_cache_write_tokens
    cache_read_cost = (cache_read_input_tokens / 1_000_000) * costs.prompt_cache_read_tokens

    return base_input_cost + output_cost + cache_write_cost + cache_read_cost


def format_cost(cost_usd: float) -> str:
    """Format a cost value for display.

    Args:
        cost_usd: Cost in dollars

    Returns:
        Formatted cost string
    """
    if cost_usd < 0.01:
        return f"${cost_usd:.4f}"
    if cost_usd < 1.00:
        return f"${cost_usd:.3f}"
    return f"${cost_usd:.2f}"


def format_model_pricing(model: str) -> str:
    """Get a formatted pricing string for a model.

    Args:
        model: The model name

    Returns:
        Formatted pricing string like "$3/$15 per MTok"
    """
    costs = get_model_costs(model)
    input_cost = int(costs.input_tokens) if costs.input_tokens == int(costs.input_tokens) else costs.input_tokens
    output_cost = int(costs.output_tokens) if costs.output_tokens == int(costs.output_tokens) else costs.output_tokens
    return f"${input_cost}/${output_cost} per MTok"
