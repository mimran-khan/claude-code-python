"""
Context window utilities.

Provides functions for managing model context windows and token limits.

Migrated from: utils/context.ts (222 lines)
"""

from __future__ import annotations

import os
import re

from .env import is_env_truthy
from .model.capabilities import get_model_capabilities

# Beta header for 1M context (TS: constants/betas.js)
CONTEXT_1M_BETA_HEADER = "context-1m-2025-01-01"

# Model context window size (200k tokens for all models right now)
MODEL_CONTEXT_WINDOW_DEFAULT = 200_000

# Maximum output tokens for compact operations
COMPACT_MAX_OUTPUT_TOKENS = 20_000

# Default max output tokens
MAX_OUTPUT_TOKENS_DEFAULT = 32_000
MAX_OUTPUT_TOKENS_UPPER_LIMIT = 64_000

# Capped default for slot-reservation optimization
CAPPED_DEFAULT_MAX_TOKENS = 8_000
ESCALATED_MAX_TOKENS = 64_000


def is_1m_context_disabled() -> bool:
    """
    Check if 1M context is disabled via environment variable.

    Used by admins to disable 1M context for compliance.

    Returns:
        True if 1M context is disabled.
    """
    return is_env_truthy(os.environ.get("CLAUDE_CODE_DISABLE_1M_CONTEXT"))


def has_1m_context(model: str) -> bool:
    """
    Check if model has 1M context suffix.

    Args:
        model: The model name.

    Returns:
        True if model has [1m] suffix.
    """
    if is_1m_context_disabled():
        return False
    return bool(re.search(r"\[1m\]", model, re.IGNORECASE))


def model_supports_1m(model: str) -> bool:
    """
    Check if model supports 1M context.

    Args:
        model: The model name.

    Returns:
        True if model supports 1M context.
    """
    if is_1m_context_disabled():
        return False
    canonical = model.lower()
    return "claude-sonnet-4" in canonical or "opus-4-6" in canonical


def get_sonnet_1m_exp_treatment_enabled(model: str) -> bool:
    """Sonnet 4.6 implicit 1M when clientDataCache coral_reef_sonnet is set."""
    if is_1m_context_disabled():
        return False
    if has_1m_context(model):
        return False
    if "sonnet-4-6" not in model.lower():
        return False
    try:
        from .config_utils import get_global_config

        cache = get_global_config().client_data_cache
        if isinstance(cache, dict):
            return cache.get("coral_reef_sonnet") == "true"
    except Exception:
        return False
    return False


def get_context_window_for_model(
    model: str,
    betas: list[str] | None = None,
) -> int:
    """
    Get the context window size for a model.

    Args:
        model: The model name.
        betas: Optional list of beta features.

    Returns:
        The context window size in tokens.
    """
    # Ant-only override via env (TS: USER_TYPE === 'ant')
    if os.environ.get("USER_TYPE") == "ant":
        override = os.environ.get("CLAUDE_CODE_MAX_CONTEXT_TOKENS")
        if override:
            try:
                parsed = int(override, 10)
                if parsed > 0:
                    return parsed
            except ValueError:
                pass

    # [1m] suffix — explicit client-side opt-in
    if has_1m_context(model):
        return 1_000_000

    cap = get_model_capabilities(model)
    max_in = cap.max_context_window
    if max_in >= 100_000:
        if max_in > MODEL_CONTEXT_WINDOW_DEFAULT and is_1m_context_disabled():
            return MODEL_CONTEXT_WINDOW_DEFAULT
        return max_in

    if betas and CONTEXT_1M_BETA_HEADER in betas and model_supports_1m(model):
        return 1_000_000
    if get_sonnet_1m_exp_treatment_enabled(model):
        return 1_000_000

    return MODEL_CONTEXT_WINDOW_DEFAULT


def calculate_context_percentages(
    current_usage: dict[str, int] | None,
    context_window_size: int,
) -> dict[str, int | None]:
    """
    Calculate context window usage percentage from token usage data.

    Args:
        current_usage: Dict with input_tokens, cache_creation_input_tokens,
            and cache_read_input_tokens.
        context_window_size: The total context window size.

    Returns:
        Dict with 'used' and 'remaining' percentages.
    """
    if not current_usage:
        return {"used": None, "remaining": None}

    total_input_tokens = (
        current_usage.get("input_tokens", 0)
        + current_usage.get("cache_creation_input_tokens", 0)
        + current_usage.get("cache_read_input_tokens", 0)
    )

    used_percentage = round((total_input_tokens / context_window_size) * 100)
    clamped_used = min(100, max(0, used_percentage))

    return {
        "used": clamped_used,
        "remaining": 100 - clamped_used,
    }


def get_model_max_output_tokens(model: str) -> dict[str, int]:
    """
    Get the model's default and upper limit for max output tokens.

    Args:
        model: The model name.

    Returns:
        Dict with 'default' and 'upper_limit' token counts.
    """
    m = model.lower()

    if "opus-4-6" in m:
        default_tokens = 64_000
        upper_limit = 128_000
    elif "sonnet-4-6" in m:
        default_tokens = 32_000
        upper_limit = 128_000
    elif "opus-4-5" in m or "sonnet-4" in m or "haiku-4" in m:
        default_tokens = 32_000
        upper_limit = 64_000
    elif "opus-4-1" in m or "opus-4" in m:
        default_tokens = 32_000
        upper_limit = 32_000
    elif "claude-3-opus" in m:
        default_tokens = 4_096
        upper_limit = 4_096
    elif "claude-3-sonnet" in m:
        default_tokens = 8_192
        upper_limit = 8_192
    elif "claude-3-haiku" in m:
        default_tokens = 4_096
        upper_limit = 4_096
    elif "3-5-sonnet" in m or "3-5-haiku" in m:
        default_tokens = 8_192
        upper_limit = 8_192
    elif "3-7-sonnet" in m:
        default_tokens = 32_000
        upper_limit = 64_000
    else:
        default_tokens = MAX_OUTPUT_TOKENS_DEFAULT
        upper_limit = MAX_OUTPUT_TOKENS_UPPER_LIMIT

    cap = get_model_capabilities(model)
    if cap.max_output_tokens >= 4096:
        upper_limit = cap.max_output_tokens
        default_tokens = min(default_tokens, upper_limit)

    return {"default": default_tokens, "upper_limit": upper_limit}


def get_max_thinking_tokens_for_model(model: str) -> int:
    """
    Get the max thinking budget tokens for a model.

    The max thinking tokens should be strictly less than the max output tokens.

    Deprecated since newer models use adaptive thinking rather than a
    strict thinking token budget.

    Args:
        model: The model name.

    Returns:
        The max thinking tokens.
    """
    return get_model_max_output_tokens(model)["upper_limit"] - 1
