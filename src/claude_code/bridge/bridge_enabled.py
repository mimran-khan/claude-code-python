"""Bridge feature gates (ported from bridge/bridgeEnabled.ts; GrowthBook + auth stubs)."""

from __future__ import annotations

# TODO: feature('BRIDGE_MODE') build-time gate — use env or package flag
# TODO: checkGate_CACHED_OR_BLOCKING, getFeatureValue from services.analytics.growthbook
# TODO: authModule.is_claude_ai_subscriber, has_profile_scope, get_oauth_account_info


def _bridge_mode_build_enabled() -> bool:
    import os

    return os.environ.get("CLAUDE_CODE_BRIDGE_MODE", "1") == "1"


def is_claude_ai_subscriber() -> bool:
    try:
        # TODO: from claude_code.utils import auth as auth_module
        # return auth_module.is_claude_ai_subscriber()
        return True
    except Exception:
        return False


def is_bridge_enabled() -> bool:
    if not _bridge_mode_build_enabled():
        return False
    # TODO: and get_feature_value_cached_may_be_stale('tengu_ccr_bridge', False)
    return is_claude_ai_subscriber()


async def is_bridge_enabled_blocking() -> bool:
    if not _bridge_mode_build_enabled():
        return False
    # TODO: await check_gate_cached_or_blocking('tengu_ccr_bridge')
    return is_claude_ai_subscriber()


async def get_bridge_disabled_reason() -> str | None:
    if not _bridge_mode_build_enabled():
        return "Remote Control is not available in this build."
    if not is_claude_ai_subscriber():
        return (
            "Remote Control requires a claude.ai subscription. "
            "Run `claude auth login` to sign in with your claude.ai account."
        )
    # TODO: has_profile_scope, oauth org, gate checks
    return None


def is_env_less_bridge_enabled() -> bool:
    """Env-less (v2) REPL bridge path."""
    if not _bridge_mode_build_enabled():
        return False
    # TODO: get_feature_value_cached_may_be_stale('tengu_bridge_repl_v2', False)
    return False


def is_cse_shim_enabled() -> bool:
    # TODO: GrowthBook tengu_ccr_v2_compat or equivalent
    return True


async def check_bridge_min_version() -> str | None:
    """Returns error message if CLI below tengu_bridge_min_version, else None."""
    # TODO: semver compare MACRO.VERSION vs growthbook min_version
    return None
