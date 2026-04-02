"""
Advisor tool configuration and message blocks.

Migrated from: utils/advisor.ts
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, TypeGuard

# Optional GrowthBook hook: set at startup to mirror TS getFeatureValue_CACHED_MAY_BE_STALE
AdvisorFeatureGetter = Callable[[str, Any], Any]
_advisor_feature_getter: AdvisorFeatureGetter | None = None


def set_advisor_feature_getter(getter: AdvisorFeatureGetter | None) -> None:
    """Register a feature-flag reader (e.g. GrowthBook)."""
    global _advisor_feature_getter
    _advisor_feature_getter = getter


def _get_advisor_config() -> dict[str, Any]:
    if _advisor_feature_getter is None:
        return {}
    return _get_advisor_feature_getter_result("tengu_sage_compass", {})


def _get_advisor_feature_getter_result(key: str, default: Any) -> Any:
    assert _advisor_feature_getter is not None
    return _advisor_feature_getter(key, default)


@dataclass
class AdvisorServerToolUseBlock:
    type: Literal["server_tool_use"]
    id: str
    name: Literal["advisor"]
    input: dict[str, Any]


@dataclass
class AdvisorToolResultBlock:
    type: Literal["advisor_tool_result"]
    tool_use_id: str
    content: dict[str, Any]


AdvisorBlock = AdvisorServerToolUseBlock | AdvisorToolResultBlock


def is_advisor_block(param: dict[str, Any]) -> TypeGuard[AdvisorBlock]:
    t = param.get("type")
    if t == "advisor_tool_result":
        return True
    return t == "server_tool_use" and param.get("name") == "advisor"


def _env_truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.lower() in ("1", "true", "yes", "on")


def _should_include_first_party_only_betas() -> bool:
    """Bedrock/Vertex omit some 1P-only betas; mirror utils/betas.ts intent."""
    return not (
        _env_truthy(os.environ.get("CLAUDE_CODE_USE_BEDROCK"))
        or _env_truthy(os.environ.get("CLAUDE_CODE_USE_VERTEX"))
        or _env_truthy(os.environ.get("CLAUDE_CODE_USE_FOUNDRY"))
    )


def is_advisor_enabled() -> bool:
    if _env_truthy(os.environ.get("CLAUDE_CODE_DISABLE_ADVISOR_TOOL")):
        return False
    if not _should_include_first_party_only_betas():
        return False
    cfg = _get_advisor_config()
    if isinstance(cfg, dict):
        return bool(cfg.get("enabled", False))
    return False


def can_user_configure_advisor() -> bool:
    if not is_advisor_enabled():
        return False
    cfg = _get_advisor_config()
    if isinstance(cfg, dict):
        return bool(cfg.get("canUserConfigure", False))
    return False


def get_experiment_advisor_models() -> dict[str, str] | None:
    cfg = _get_advisor_config()
    if not isinstance(cfg, dict):
        return None
    if not is_advisor_enabled() or can_user_configure_advisor():
        return None
    base = cfg.get("baseModel")
    advisor = cfg.get("advisorModel")
    if isinstance(base, str) and isinstance(advisor, str):
        return {"baseModel": base, "advisorModel": advisor}
    return None


def model_supports_advisor(model: str) -> bool:
    m = model.lower()
    if "opus-4-6" in m or "sonnet-4-6" in m:
        return True
    return os.environ.get("USER_TYPE") == "ant"


def is_valid_advisor_model(model: str) -> bool:
    return model_supports_advisor(model)


def get_initial_advisor_setting(
    get_initial_settings: Callable[[], dict[str, Any]] | None = None,
) -> str | None:
    if not is_advisor_enabled():
        return None
    if get_initial_settings is None:
        return None
    settings = get_initial_settings()
    val = settings.get("advisorModel")
    return val if isinstance(val, str) else None


def get_advisor_usage(usage: dict[str, Any]) -> list[dict[str, Any]]:
    iterations = usage.get("iterations")
    if not isinstance(iterations, list):
        return []
    out: list[dict[str, Any]] = []
    for it in iterations:
        if isinstance(it, dict) and it.get("type") == "advisor_message":
            merged = {**usage, **it}
            out.append(merged)
    return out


ADVISOR_TOOL_INSTRUCTIONS = (
    "# Advisor Tool\n\n"
    "You have access to an `advisor` tool backed by a stronger reviewer model. "
    "It takes NO parameters; your conversation is forwarded automatically.\n\n"
    "Call advisor BEFORE substantive work, when complete (after durable writes), "
    "when stuck, or when changing approach.\n\n"
    "Give the advice serious weight; reconcile conflicts with another advisor "
    "call when evidence disagrees."
)
