"""
Model effort level resolution and persistence helpers.

Migrated from: utils/effort.ts
"""

from __future__ import annotations

import os
from typing import Literal, TypeAlias

from .env_utils import is_env_truthy
from .model.providers import get_api_provider

EffortLevel = Literal["low", "medium", "high", "max"]
EffortValue: TypeAlias = EffortLevel | int

EFFORT_LEVELS: tuple[EffortLevel, ...] = ("low", "medium", "high", "max")


def _get_3p_model_capability_override(model: str, capability: str) -> bool | None:
    try:
        from .model.model_support_overrides import get_3p_model_capability_override as _fn

        return _fn(model, capability)
    except ImportError:
        return None


def model_supports_effort(model: str) -> bool:
    m = model.lower()
    if is_env_truthy(os.getenv("CLAUDE_CODE_ALWAYS_ENABLE_EFFORT")):
        return True
    supported_3p = _get_3p_model_capability_override(model, "effort")
    if supported_3p is not None:
        return supported_3p
    if "opus-4-6" in m or "sonnet-4-6" in m:
        return True
    if "haiku" in m or "sonnet" in m or "opus" in m:
        return False
    return get_api_provider() == "firstParty"


def model_supports_max_effort(model: str) -> bool:
    supported_3p = _get_3p_model_capability_override(model, "max_effort")
    if supported_3p is not None:
        return supported_3p
    if "opus-4-6" in model.lower():
        return True
    return bool(os.getenv("USER_TYPE") == "ant" and _resolve_ant_model(model))


def is_effort_level(value: str) -> bool:
    return value in EFFORT_LEVELS


def parse_effort_value(value: object) -> EffortValue | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and float(value).is_integer():
        iv = int(value)
        if _is_valid_numeric_effort(iv):
            return iv
    s = str(value).lower().strip()
    if is_effort_level(s):
        return s  # type: ignore[return-value]
    try:
        numeric = int(s, 10)
    except ValueError:
        return None
    if _is_valid_numeric_effort(numeric):
        return numeric
    return None


def to_persistable_effort(value: EffortValue | None) -> EffortLevel | None:
    if value in ("low", "medium", "high"):
        return value  # type: ignore[return-value]
    if value == "max" and os.getenv("USER_TYPE") == "ant":
        return "max"
    return None


def _read_initial_effort_from_settings() -> EffortValue | None:
    try:
        from .settings.settings import get_merged_settings

        merged = get_merged_settings()
        if isinstance(merged, dict):
            return parse_effort_value(merged.get("effortLevel"))
    except Exception:
        pass
    return None


def get_initial_effort_setting() -> EffortLevel | None:
    return to_persistable_effort(_read_initial_effort_from_settings())


def resolve_picker_effort_persistence(
    picked: EffortLevel | None,
    model_default: EffortLevel,
    prior_persisted: EffortLevel | None,
    toggled_in_picker: bool,
) -> EffortLevel | None:
    had_explicit = prior_persisted is not None or toggled_in_picker
    if had_explicit or picked != model_default:
        return picked
    return None


def get_displayed_effort_level(model: str, app_state_effort: EffortValue | None) -> EffortLevel:
    resolved = resolve_applied_effort(model, app_state_effort)
    if resolved is None:
        resolved = "high"
    return convert_effort_value_to_level(resolved)


def get_effort_suffix(model: str, effort_value: EffortValue | None) -> str:
    if effort_value is None:
        return ""
    resolved = resolve_applied_effort(model, effort_value)
    if resolved is None:
        return ""
    return f" with {convert_effort_value_to_level(resolved)} effort"


def _is_valid_numeric_effort(value: int) -> bool:
    return isinstance(value, int)


def convert_effort_value_to_level(value: EffortValue) -> EffortLevel:
    if isinstance(value, str):
        return value if is_effort_level(value) else "high"
    if os.getenv("USER_TYPE") == "ant" and isinstance(value, int):
        if value <= 50:
            return "low"
        if value <= 85:
            return "medium"
        if value <= 100:
            return "high"
        return "max"
    return "high"


def get_effort_level_description(level: EffortLevel) -> str:
    if level == "low":
        return "Quick, straightforward implementation with minimal overhead"
    if level == "medium":
        return "Balanced approach with standard implementation and testing"
    if level == "high":
        return "Comprehensive implementation with extensive testing and documentation"
    return "Maximum capability with deepest reasoning (Opus 4.6 only)"


def get_effort_value_description(value: EffortValue) -> str:
    if os.getenv("USER_TYPE") == "ant" and isinstance(value, int):
        return f"[ANT-ONLY] Numeric effort value of {value}"
    if isinstance(value, str):
        return get_effort_level_description(value)
    return "Balanced approach with standard implementation and testing"


def _is_ultrathink_enabled() -> bool:
    try:
        from .thinking import is_ultrathink_enabled

        return bool(is_ultrathink_enabled())
    except ImportError:
        return False


def get_opus_default_effort_config() -> dict[str, object]:
    default: dict[str, object] = {
        "enabled": True,
        "dialogTitle": "We recommend medium effort for Opus",
        "dialogDescription": (
            "Effort determines how long Claude thinks for when completing your task. "
            "We recommend medium effort for most tasks to balance speed and intelligence "
            "and maximize rate limits. Use ultrathink to trigger high effort when needed."
        ),
    }
    try:
        from claude_code.services.analytics.growthbook import get_feature_value_cached

        cfg = get_feature_value_cached("tengu_grey_step2", default)
        if isinstance(cfg, dict):
            return {**default, **cfg}
    except Exception:
        pass
    return default


def _resolve_ant_model(_model: str) -> dict[str, object] | None:
    return None


def get_default_effort_for_model(model: str) -> EffortValue | None:
    if os.getenv("USER_TYPE") == "ant":
        ant_model = _resolve_ant_model(model)
        if ant_model:
            if ant_model.get("defaultEffortLevel"):
                return ant_model["defaultEffortLevel"]  # type: ignore[return-value]
            if ant_model.get("defaultEffortValue") is not None:
                return ant_model["defaultEffortValue"]  # type: ignore[return-value]
        return None

    ml = model.lower()
    if "opus-4-6" in ml:
        try:
            from claude_code.auth.helpers import (
                is_max_subscriber,
                is_pro_subscriber,
                is_team_subscriber,
            )
        except ImportError:

            def is_pro_subscriber() -> bool:
                return False

            def is_max_subscriber() -> bool:
                return False

            def is_team_subscriber() -> bool:
                return False

        if is_pro_subscriber():
            return "medium"
        cfg = get_opus_default_effort_config()
        if cfg.get("enabled") and (is_max_subscriber() or is_team_subscriber()):
            return "medium"

    if _is_ultrathink_enabled() and model_supports_effort(model):
        return "medium"

    return None


def resolve_applied_effort(
    model: str,
    app_state_effort_value: EffortValue | None,
) -> EffortValue | None:
    raw = os.getenv("CLAUDE_CODE_EFFORT_LEVEL")
    if raw is not None:
        el = raw.lower().strip()
        if el in ("unset", "auto"):
            return None
        env_parsed = parse_effort_value(raw)
        resolved = env_parsed
    else:
        resolved = app_state_effort_value
    if resolved is None:
        resolved = get_default_effort_for_model(model)
    if resolved == "max" and not model_supports_max_effort(model):
        return "high"
    return resolved


def get_effort_env_override() -> EffortValue | None | Literal["__unset_sentinel__"]:
    env_override = os.getenv("CLAUDE_CODE_EFFORT_LEVEL")
    if env_override is None:
        return None
    el = env_override.lower().strip()
    if el in ("unset", "auto"):
        return None
    return parse_effort_value(env_override)
