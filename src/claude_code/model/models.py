"""
Model Configuration.

Model names, defaults, and utility functions.
"""

from __future__ import annotations

import os
from typing import Literal

# Model aliases
ModelAlias = Literal["sonnet", "opus", "haiku", "default", "best", "fast"]

# Default model names
DEFAULT_SONNET_MODEL = "claude-sonnet-4-20250514"
DEFAULT_OPUS_MODEL = "claude-opus-4-20250514"
DEFAULT_HAIKU_MODEL = "claude-3-5-haiku-20241022"

# Model context windows
MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    # Sonnet 4 series
    "claude-sonnet-4-20250514": 200_000,
    "claude-4-sonnet-20250514": 200_000,
    # Opus 4 series
    "claude-opus-4-20250514": 200_000,
    "claude-4-opus-20250514": 200_000,
    # Haiku 3.5 series
    "claude-3-5-haiku-20241022": 200_000,
    # Sonnet 3.5 series
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-5-sonnet-20240620": 200_000,
    # Opus 3 series
    "claude-3-opus-20240229": 200_000,
    # Haiku 3 series
    "claude-3-haiku-20240307": 200_000,
}

# Default context window
DEFAULT_CONTEXT_WINDOW = 200_000


def get_default_model() -> str:
    """Get the default model to use.

    Checks environment variables first, then falls back to default.
    """
    env_model = os.environ.get("ANTHROPIC_MODEL")
    if env_model:
        return env_model
    return DEFAULT_SONNET_MODEL


def get_default_sonnet_model() -> str:
    """Get the default Sonnet model."""
    return DEFAULT_SONNET_MODEL


def get_default_opus_model() -> str:
    """Get the default Opus model."""
    return DEFAULT_OPUS_MODEL


def get_default_haiku_model() -> str:
    """Get the default Haiku model."""
    return DEFAULT_HAIKU_MODEL


def get_small_fast_model() -> str:
    """Get the small/fast model for quick tasks.

    Uses ANTHROPIC_SMALL_FAST_MODEL env var if set.
    """
    return os.environ.get("ANTHROPIC_SMALL_FAST_MODEL", DEFAULT_HAIKU_MODEL)


def is_opus_model(model: str) -> bool:
    """Check if a model is an Opus model."""
    model_lower = model.lower()
    return "opus" in model_lower


def is_sonnet_model(model: str) -> bool:
    """Check if a model is a Sonnet model."""
    model_lower = model.lower()
    return "sonnet" in model_lower


def is_haiku_model(model: str) -> bool:
    """Check if a model is a Haiku model."""
    model_lower = model.lower()
    return "haiku" in model_lower


def get_model_context_window(model: str) -> int:
    """Get the context window size for a model.

    Args:
        model: The model name

    Returns:
        Context window size in tokens
    """
    return MODEL_CONTEXT_WINDOWS.get(model, DEFAULT_CONTEXT_WINDOW)


def resolve_model_alias(alias: ModelAlias | str) -> str:
    """Resolve a model alias to a full model name.

    Args:
        alias: The model alias or name

    Returns:
        The resolved model name
    """
    alias_lower = alias.lower()

    if alias_lower in ("sonnet", "default"):
        return get_default_sonnet_model()
    if alias_lower in ("opus", "best"):
        return get_default_opus_model()
    if alias_lower in ("haiku", "fast"):
        return get_small_fast_model()

    # Not an alias, return as-is
    return alias


def is_model_alias(value: str) -> bool:
    """Check if a value is a model alias."""
    return value.lower() in ("sonnet", "opus", "haiku", "default", "best", "fast")


def get_model_display_name(model: str) -> str:
    """Get a human-readable display name for a model.

    Args:
        model: The model identifier

    Returns:
        Display name for the model
    """
    # Check for aliases
    if is_model_alias(model):
        model = resolve_model_alias(model)

    # Extract model family and version
    if "opus" in model.lower():
        if "4-" in model or "-4" in model:
            return "Claude Opus 4"
        return "Claude Opus 3"

    if "sonnet" in model.lower():
        if "4-" in model or "-4" in model:
            return "Claude Sonnet 4"
        if "3-5" in model or "3.5" in model:
            return "Claude Sonnet 3.5"
        return "Claude Sonnet 3"

    if "haiku" in model.lower():
        if "3-5" in model or "3.5" in model:
            return "Claude Haiku 3.5"
        return "Claude Haiku 3"

    # Unknown model, return as-is
    return model


def get_model_family(model: str) -> str:
    """Get the model family name.

    Args:
        model: The model identifier

    Returns:
        Model family name (opus, sonnet, haiku, or unknown)
    """
    model_lower = model.lower()

    if "opus" in model_lower:
        return "opus"
    if "sonnet" in model_lower:
        return "sonnet"
    if "haiku" in model_lower:
        return "haiku"

    return "unknown"


def get_main_loop_model() -> str:
    """Get the model to use for the main query loop.

    Priority:
    1. ANTHROPIC_MODEL environment variable
    2. User settings (not yet implemented)
    3. Built-in default

    Returns:
        The resolved model name
    """
    # Check environment variable
    env_model = os.environ.get("ANTHROPIC_MODEL")
    if env_model:
        if is_model_alias(env_model):
            return resolve_model_alias(env_model)
        return env_model

    # TODO: Check user settings

    return get_default_model()
