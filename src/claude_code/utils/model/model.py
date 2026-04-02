"""
Model utilities.

Core model selection and configuration.

Migrated from: utils/model/model.ts (619 lines)
"""

from __future__ import annotations

import os
import re

from ..context import has_1m_context, is_1m_context_disabled
from ..env_utils import is_env_truthy
from .aliases import is_model_alias, resolve_model_alias
from .providers import get_api_provider

# Type aliases
ModelName = str
ModelAlias = str
ModelSetting = ModelName | ModelAlias | None


# Model name patterns
MODEL_STRINGS = {
    "opus40": "claude-opus-4-20250514",
    "opus41": "claude-opus-4.1-20250514",
    "opus45": "claude-opus-4.5-20250514",
    "opus46": "claude-opus-4-20250514",
    "sonnet40": "claude-sonnet-4-20250514",
    "sonnet45": "claude-sonnet-4.5-20250514",
    "sonnet46": "claude-sonnet-4-20250514",
    "haiku40": "claude-haiku-4-20250514",
    "haiku45": "claude-3-5-haiku-latest",
}


def get_model_strings() -> dict[str, str]:
    """Get the model string mappings."""
    return MODEL_STRINGS


def get_small_fast_model() -> ModelName:
    """Get the small fast model for quick operations."""
    return os.getenv("ANTHROPIC_SMALL_FAST_MODEL") or get_default_haiku_model()


def is_non_custom_opus_model(model: ModelName) -> bool:
    """Check if a model is a non-custom Opus model."""
    opus_models = [
        MODEL_STRINGS["opus40"],
        MODEL_STRINGS["opus41"],
        MODEL_STRINGS["opus45"],
        MODEL_STRINGS["opus46"],
    ]
    return model in opus_models


def get_user_specified_model_setting() -> ModelSetting | None:
    """
    Get the user-specified model setting.

    Priority:
    1. Model override during session (from /model command)
    2. Model override at startup (from --model flag)
    3. ANTHROPIC_MODEL environment variable
    4. Settings (from user's saved settings)
    """
    # Check environment variable
    model = os.getenv("ANTHROPIC_MODEL")
    if model:
        return model

    # Would check settings here
    return None


def get_main_loop_model() -> ModelName:
    """
    Get the main loop model to use for the current session.

    Priority:
    1. Model override during session
    2. Model override at startup
    3. ANTHROPIC_MODEL environment variable
    4. Settings
    5. Built-in default
    """
    model = get_user_specified_model_setting()
    if model is not None:
        return parse_user_specified_model(model)
    return get_default_main_loop_model()


def parse_user_specified_model(model: str) -> ModelName:
    """
    Parse a user-specified model setting.

    Resolves aliases and validates model names.
    """
    base = model
    if base.endswith("[1m]"):
        base = base[: -len("[1m]")]
    if is_model_alias(base):
        resolved = resolve_model_alias(base)
        return resolved + "[1m]" if model.endswith("[1m]") else resolved
    if is_model_alias(model):
        return resolve_model_alias(model)
    return model


def is_legacy_model_remap_enabled() -> bool:
    """Opt-out for legacy Opus 4.0/4.1 → current Opus remap (TS parity)."""
    return not is_env_truthy(os.environ.get("CLAUDE_CODE_DISABLE_LEGACY_MODEL_REMAP"))


def is_opus_1m_merge_enabled() -> bool:
    """
    Whether eligible users get merged Opus + 1M experience (Max/Team Premium on 1P).

    Pro-only subscribers are excluded; 3P and 1M-disabled are excluded.
    """
    from claude_code.auth.helpers import get_subscription_type

    if is_1m_context_disabled() or get_api_provider() != "firstParty":
        return False
    if get_subscription_type() == "pro":
        return False
    # Fail closed when subscription is unknown for Claude.ai OAuth users (TS parity stub).
    if is_env_truthy(os.environ.get("CLAUDE_CODE_CLAUDE_AI_SUBSCRIBER")):
        if os.environ.get("CLAUDE_CODE_SUBSCRIPTION_TYPE", "").strip() == "":
            return False
    return True


def get_default_main_loop_model_setting() -> str:
    """
    Built-in default model *setting* (alias or ID) before user overrides.

    Mirrors ``getDefaultMainLoopModelSetting`` from TS ``utils/model/model.ts``.
    """
    from claude_code.auth.helpers import is_max_subscriber, is_team_premium_subscriber

    if os.environ.get("USER_TYPE") == "ant":
        ant_default = os.environ.get("CLAUDE_CODE_ANT_DEFAULT_MODEL")
        if ant_default:
            return ant_default
        # Ants default to Opus 1M when no flag-config override (TS parity).
        return get_default_opus_model() + "[1m]"

    if is_max_subscriber() or is_team_premium_subscriber():
        suffix = "[1m]" if is_opus_1m_merge_enabled() else ""
        return get_default_opus_model() + suffix

    return get_default_sonnet_model()


def get_best_model() -> ModelName:
    """Get the best available model."""
    return get_default_opus_model()


def get_default_opus_model() -> ModelName:
    """Get the default Opus model."""
    if os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL"):
        return os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL")

    return MODEL_STRINGS["opus46"]


def get_default_sonnet_model() -> ModelName:
    """Get the default Sonnet model."""
    if os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL"):
        return os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL")

    # Default to Sonnet 4.5 for 3P since they may not have 4.6 yet
    if get_api_provider() != "firstParty":
        return MODEL_STRINGS["sonnet45"]

    return MODEL_STRINGS["sonnet46"]


def get_default_haiku_model() -> ModelName:
    """Get the default Haiku model."""
    if os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL"):
        return os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL")

    return MODEL_STRINGS["haiku45"]


def get_default_main_loop_model() -> ModelName:
    """Resolve the built-in default main loop model (no user override)."""
    return parse_user_specified_model(get_default_main_loop_model_setting())


def is_opus_model(model: ModelName) -> bool:
    """Check if a model is an Opus model."""
    return "opus" in model.lower()


def is_sonnet_model(model: ModelName) -> bool:
    """Check if a model is a Sonnet model."""
    return "sonnet" in model.lower()


def is_haiku_model(model: ModelName) -> bool:
    """Check if a model is a Haiku model."""
    return "haiku" in model.lower()


def get_model_family(model: ModelName) -> str:
    """Get the model family (opus, sonnet, haiku)."""
    model_lower = model.lower()
    if "opus" in model_lower:
        return "opus"
    if "sonnet" in model_lower:
        return "sonnet"
    if "haiku" in model_lower:
        return "haiku"
    return "unknown"


def get_canonical_name(model: ModelName) -> str:
    """Get the canonical display name for a model."""
    family = get_model_family(model)

    if family == "opus":
        return "Claude Opus"
    if family == "sonnet":
        return "Claude Sonnet"
    if family == "haiku":
        return "Claude Haiku"

    return model


def get_public_model_display_name(model: ModelName) -> str | None:
    """
    Human-readable display name for known public models, or ``None`` if unknown.

    Mirrors ``getPublicModelDisplayName`` from TS ``utils/model/model.ts`` for
    entries present in :data:`MODEL_STRINGS`.
    """
    ms = get_model_strings()
    pairs: list[tuple[str, str]] = [
        (ms["opus46"] + "[1m]", "Opus 4.6 (1M context)"),
        (ms["opus46"], "Opus 4.6"),
        (ms["opus45"], "Opus 4.5"),
        (ms["opus41"], "Opus 4.1"),
        (ms["opus40"], "Opus 4"),
        (ms["sonnet46"] + "[1m]", "Sonnet 4.6 (1M context)"),
        (ms["sonnet46"], "Sonnet 4.6"),
        (ms["sonnet45"] + "[1m]", "Sonnet 4.5 (1M context)"),
        (ms["sonnet45"], "Sonnet 4.5"),
        (ms["sonnet40"] + "[1m]", "Sonnet 4 (1M context)"),
        (ms["sonnet40"], "Sonnet 4"),
        (ms["haiku45"], "Haiku 4.5"),
    ]
    for key, label in pairs:
        if model == key:
            return label
    return None


def _mask_model_codename(base_name: str) -> str:
    """Mask the first dash-separated segment (codename); preserve the rest (TS parity)."""
    segments = base_name.split("-")
    if not segments:
        return base_name
    codename = segments[0]
    rest = segments[1:]
    masked = codename[:3] + ("*" * max(0, len(codename) - 3))
    return "-".join([masked, *rest]) if rest else masked


def render_model_name(model: ModelName) -> str:
    """
    User-facing label for a model id or alias (TS ``renderModelName``).

    Public catalog names first; internal ``ant`` users get masked codenames when
    :func:`claude_code.utils.effort._resolve_ant_model` returns metadata.
    """
    public = get_public_model_display_name(model)
    if public is not None:
        return public
    if os.environ.get("USER_TYPE") == "ant":
        resolved = parse_user_specified_model(model)
        from claude_code.utils.effort import _resolve_ant_model

        ant_model = _resolve_ant_model(model)
        if ant_model is not None:
            raw_model = ant_model.get("model")
            if isinstance(raw_model, str):
                base_name = re.sub(r"\[1m\]$", "", raw_model, flags=re.IGNORECASE)
                masked = _mask_model_codename(base_name)
                suffix = "[1m]" if has_1m_context(resolved) else ""
                return masked + suffix
        if resolved != model:
            return f"{model} ({resolved})"
        return resolved
    return model
