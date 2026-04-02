"""GrowthBook feature flag integration."""

import os
from typing import Any, TypeVar

T = TypeVar("T")


# Feature flag cache
_feature_cache: dict[str, Any] = {}


def get_growthbook_client_key() -> str:
    """Get the GrowthBook client key based on environment."""
    user_type = os.environ.get("USER_TYPE", "")
    enable_dev = os.environ.get("ENABLE_GROWTHBOOK_DEV", "")

    if user_type == "ant":
        if enable_dev.lower() in ("1", "true", "yes"):
            return "sdk-yZQvlplybuXjYh6L"
        return "sdk-xRVcrliHIlrg4og4"
    return "sdk-zAZezfDKGoZuXXKe"


def get_feature_value(feature_key: str, default: T) -> T:
    """Get a feature flag value.

    In full implementation, would fetch from GrowthBook SDK.
    """
    if feature_key in _feature_cache:
        return _feature_cache[feature_key]
    return default


def get_feature_value_cached(
    feature_key: str,
    default: T,
    refresh_ms: int = 0,
) -> T:
    """Get a cached feature flag value.

    refresh_ms is ignored in this stub - full implementation would
    refresh the cache periodically.
    """
    return get_feature_value(feature_key, default)


# Aliases matching TypeScript GrowthBook helper names
get_feature_value_cached_may_be_stale = get_feature_value_cached


async def get_dynamic_config_blocks_on_init(key: str, default: T) -> T:
    """
    Remote JSON config (may block session init in full SDK).

    Migrated name from: ``getDynamicConfig_BLOCKS_ON_INIT`` in analytics/growthbook.ts.
    """
    return get_dynamic_config_cached_may_be_stale(key, default)


def set_feature_value(feature_key: str, value: Any) -> None:
    """Set a feature value (for testing)."""
    _feature_cache[feature_key] = value


def clear_feature_cache() -> None:
    """Clear the feature cache."""
    _feature_cache.clear()


def check_statsig_feature_gate_cached_may_be_stale(gate_name: str) -> bool:
    """Statsig-style boolean gate; stub returns False unless set in cache."""
    return bool(_feature_cache.get(f"gate:{gate_name}", False))


def get_dynamic_config_cached_may_be_stale(key: str, default: T) -> T:
    """
    JSON dynamic config (GrowthBook). Fail-open on missing/malformed values.

    Migrated from: services/analytics/growthbook.ts (getDynamicConfig_CACHED_MAY_BE_STALE).
    """
    raw = _feature_cache.get(key)
    if raw is None:
        return default
    return raw  # type: ignore[return-value]
