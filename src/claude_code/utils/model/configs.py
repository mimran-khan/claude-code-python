"""
Model configurations.

Model-specific configuration settings.

Migrated from: utils/model/configs.ts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a model."""

    name: str
    display_name: str
    family: str
    max_tokens: int = 8192
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int | None = None
    stop_sequences: list[str] | None = None

    # Cost per 1M tokens (in USD)
    input_cost_per_1m: float = 0.0
    output_cost_per_1m: float = 0.0


# Default model configurations
DEFAULT_MODEL_CONFIGS: dict[str, ModelConfig] = {
    "claude-opus-4-20250514": ModelConfig(
        name="claude-opus-4-20250514",
        display_name="Claude Opus 4",
        family="opus",
        max_tokens=8192,
        input_cost_per_1m=15.0,
        output_cost_per_1m=75.0,
    ),
    "claude-sonnet-4-20250514": ModelConfig(
        name="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        family="sonnet",
        max_tokens=8192,
        input_cost_per_1m=3.0,
        output_cost_per_1m=15.0,
    ),
    "claude-3-5-haiku-latest": ModelConfig(
        name="claude-3-5-haiku-latest",
        display_name="Claude Haiku 3.5",
        family="haiku",
        max_tokens=8192,
        input_cost_per_1m=0.25,
        output_cost_per_1m=1.25,
    ),
}


def get_model_config(model: str) -> ModelConfig:
    """
    Get configuration for a model.

    Args:
        model: The model name

    Returns:
        ModelConfig instance
    """
    # Check exact match
    if model in DEFAULT_MODEL_CONFIGS:
        return DEFAULT_MODEL_CONFIGS[model]

    # Check by family
    model_lower = model.lower()

    if "opus" in model_lower:
        return ModelConfig(
            name=model,
            display_name="Claude Opus",
            family="opus",
            input_cost_per_1m=15.0,
            output_cost_per_1m=75.0,
        )

    if "sonnet" in model_lower:
        return ModelConfig(
            name=model,
            display_name="Claude Sonnet",
            family="sonnet",
            input_cost_per_1m=3.0,
            output_cost_per_1m=15.0,
        )

    if "haiku" in model_lower:
        return ModelConfig(
            name=model,
            display_name="Claude Haiku",
            family="haiku",
            input_cost_per_1m=0.25,
            output_cost_per_1m=1.25,
        )

    # Default config
    return ModelConfig(
        name=model,
        display_name=model,
        family="unknown",
    )


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Calculate the cost for a model usage.

    Args:
        model: The model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    config = get_model_config(model)

    input_cost = (input_tokens / 1_000_000) * config.input_cost_per_1m
    output_cost = (output_tokens / 1_000_000) * config.output_cost_per_1m

    return input_cost + output_cost
