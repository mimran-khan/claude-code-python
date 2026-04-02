"""
Model aliases.

Alias resolution for model names.

Migrated from: utils/model/aliases.ts
"""

from __future__ import annotations

from typing import Literal

# Available model aliases
ModelAlias = Literal["opus", "sonnet", "haiku", "best", "fast"]

AVAILABLE_ALIASES: list[ModelAlias] = ["opus", "sonnet", "haiku", "best", "fast"]


def is_model_alias(name: str) -> bool:
    """
    Check if a string is a model alias.

    Args:
        name: The string to check

    Returns:
        True if it's a valid alias
    """
    return name.lower() in AVAILABLE_ALIASES


def resolve_model_alias(alias: str) -> str:
    """
    Resolve a model alias to an actual model name.

    Args:
        alias: The alias to resolve

    Returns:
        The resolved model name
    """
    from .model import (
        get_best_model,
        get_default_haiku_model,
        get_default_opus_model,
        get_default_sonnet_model,
        get_small_fast_model,
    )

    alias_lower = alias.lower()

    if alias_lower == "opus":
        return get_default_opus_model()

    if alias_lower == "sonnet":
        return get_default_sonnet_model()

    if alias_lower == "haiku":
        return get_default_haiku_model()

    if alias_lower == "best":
        return get_best_model()

    if alias_lower == "fast":
        return get_small_fast_model()

    # Not an alias, return as-is
    return alias


def get_alias_description(alias: str) -> str:
    """
    Get a description for a model alias.

    Args:
        alias: The alias

    Returns:
        Description string
    """
    descriptions = {
        "opus": "Most capable model (highest cost)",
        "sonnet": "Balanced performance and cost (default)",
        "haiku": "Fast and efficient (lowest cost)",
        "best": "Best available model",
        "fast": "Fastest model for quick tasks",
    }

    return descriptions.get(alias.lower(), "Unknown alias")
