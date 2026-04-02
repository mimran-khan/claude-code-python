"""
Auto-install the official Anthropic marketplace on startup.

Migrated from: utils/plugins/officialMarketplaceStartupCheck.ts
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Literal

from claude_code.services.analytics.events import log_event
from claude_code.services.analytics.growthbook import get_feature_value_cached

from ..config_utils import get_global_config, save_global_config
from ..debug import log_for_debugging
from ..env_utils import is_env_truthy
from ..errors import error_message, to_error
from ..log import log_error
from .git_availability import check_git_available, mark_git_unavailable
from .marketplace_helpers import is_source_allowed_by_policy
from .marketplace_manager import (
    add_marketplace_source,
    get_marketplaces_cache_dir,
    load_known_marketplaces_config,
    save_known_marketplaces_config,
)
from .official_marketplace import OFFICIAL_MARKETPLACE_NAME, OFFICIAL_MARKETPLACE_SOURCE
from .official_marketplace_gcs import fetch_official_marketplace_from_gcs

OfficialMarketplaceSkipReason = Literal[
    "already_attempted",
    "already_installed",
    "policy_blocked",
    "git_unavailable",
    "gcs_unavailable",
    "unknown",
]

RETRY_CONFIG = {
    "MAX_ATTEMPTS": 10,
    "INITIAL_DELAY_MS": 60 * 60 * 1000,
    "BACKOFF_MULTIPLIER": 2,
    "MAX_DELAY_MS": 7 * 24 * 60 * 60 * 1000,
}


def is_official_marketplace_auto_install_disabled() -> bool:
    return is_env_truthy(
        os.environ.get("CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL"),
    )


def _calculate_next_retry_delay(retry_count: int) -> float:
    delay = RETRY_CONFIG["INITIAL_DELAY_MS"] * (RETRY_CONFIG["BACKOFF_MULTIPLIER"] ** retry_count)
    return min(delay, float(RETRY_CONFIG["MAX_DELAY_MS"]))


def _should_retry_installation(cfg: Any) -> bool:
    if cfg.official_marketplace_auto_install_attempted is not True:
        return True
    if cfg.official_marketplace_auto_installed is True:
        return False
    fail_reason = cfg.official_marketplace_auto_install_fail_reason
    retry_count = cfg.official_marketplace_auto_install_retry_count or 0
    next_retry = cfg.official_marketplace_auto_install_next_retry_time
    now = int(time.time() * 1000)
    if retry_count >= RETRY_CONFIG["MAX_ATTEMPTS"]:
        return False
    if fail_reason == "policy_blocked":
        return False
    if next_retry and now < next_retry:
        return False
    return fail_reason in (None, "unknown", "git_unavailable", "gcs_unavailable")


@dataclass
class OfficialMarketplaceCheckResult:
    installed: bool
    skipped: bool
    reason: OfficialMarketplaceSkipReason | None = None
    config_save_failed: bool = False


def _event_payload(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}


async def check_and_install_official_marketplace() -> OfficialMarketplaceCheckResult:
    cfg = get_global_config()

    if not _should_retry_installation(cfg):
        raw_reason = cfg.official_marketplace_auto_install_fail_reason
        reason: OfficialMarketplaceSkipReason = raw_reason if isinstance(raw_reason, str) else "already_attempted"
        log_for_debugging(f"Official marketplace auto-install skipped: {reason}")
        return OfficialMarketplaceCheckResult(installed=False, skipped=True, reason=reason)

    try:
        if is_official_marketplace_auto_install_disabled():
            log_for_debugging(
                "Official marketplace auto-install disabled via env var, skipping",
            )

            def _policy_skip(c: dict[str, Any]) -> dict[str, Any]:
                m = dict(c)
                m["officialMarketplaceAutoInstallAttempted"] = True
                m["officialMarketplaceAutoInstalled"] = False
                m["officialMarketplaceAutoInstallFailReason"] = "policy_blocked"
                return m

            save_global_config(_policy_skip)
            log_event(
                "tengu_official_marketplace_auto_install",
                _event_payload(installed=False, skipped=True, policy_blocked=True),
            )
            return OfficialMarketplaceCheckResult(installed=False, skipped=True, reason="policy_blocked")

        known = await load_known_marketplaces_config()
        if known.get(OFFICIAL_MARKETPLACE_NAME):

            def _already(c: dict[str, Any]) -> dict[str, Any]:
                m = dict(c)
                m["officialMarketplaceAutoInstallAttempted"] = True
                m["officialMarketplaceAutoInstalled"] = True
                return m

            save_global_config(_already)
            log_for_debugging(
                f"Official marketplace '{OFFICIAL_MARKETPLACE_NAME}' already installed, skipping",
            )
            return OfficialMarketplaceCheckResult(installed=False, skipped=True, reason="already_installed")

        if not is_source_allowed_by_policy(dict(OFFICIAL_MARKETPLACE_SOURCE)):
            log_for_debugging("Official marketplace blocked by enterprise policy, skipping")

            def _policy_block(c: dict[str, Any]) -> dict[str, Any]:
                m = dict(c)
                m["officialMarketplaceAutoInstallAttempted"] = True
                m["officialMarketplaceAutoInstalled"] = False
                m["officialMarketplaceAutoInstallFailReason"] = "policy_blocked"
                return m

            save_global_config(_policy_block)
            log_event(
                "tengu_official_marketplace_auto_install",
                _event_payload(installed=False, skipped=True, policy_blocked=True),
            )
            return OfficialMarketplaceCheckResult(installed=False, skipped=True, reason="policy_blocked")

        cache_dir = get_marketplaces_cache_dir()
        os.makedirs(cache_dir, exist_ok=True)
        install_location = os.path.join(cache_dir, OFFICIAL_MARKETPLACE_NAME)

        gcs_sha = await fetch_official_marketplace_from_gcs(install_location, cache_dir)
        if gcs_sha is not None:
            known_after = await load_known_marketplaces_config()
            known_after[OFFICIAL_MARKETPLACE_NAME] = {
                "source": dict(OFFICIAL_MARKETPLACE_SOURCE),
                "installLocation": install_location,
                "lastUpdated": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            }
            await save_known_marketplaces_config(known_after)

            def _success_gcs(c: dict[str, Any]) -> dict[str, Any]:
                m = dict(c)
                m["officialMarketplaceAutoInstallAttempted"] = True
                m["officialMarketplaceAutoInstalled"] = True
                for k in (
                    "officialMarketplaceAutoInstallFailReason",
                    "officialMarketplaceAutoInstallRetryCount",
                    "officialMarketplaceAutoInstallLastAttemptTime",
                    "officialMarketplaceAutoInstallNextRetryTime",
                ):
                    m.pop(k, None)
                return m

            save_global_config(_success_gcs)
            log_event(
                "tengu_official_marketplace_auto_install",
                _event_payload(installed=True, skipped=False, via_gcs=True),
            )
            return OfficialMarketplaceCheckResult(installed=True, skipped=False)

        if not get_feature_value_cached("tengu_plugin_official_mkt_git_fallback", True):
            log_for_debugging(
                "Official marketplace GCS failed; git fallback disabled by flag — skipping install",
            )
            retry_count = (cfg.official_marketplace_auto_install_retry_count or 0) + 1
            now = int(time.time() * 1000)
            next_retry = now + int(_calculate_next_retry_delay(retry_count))

            def _gcs_fail(c: dict[str, Any]) -> dict[str, Any]:
                m = dict(c)
                m["officialMarketplaceAutoInstallAttempted"] = True
                m["officialMarketplaceAutoInstalled"] = False
                m["officialMarketplaceAutoInstallFailReason"] = "gcs_unavailable"
                m["officialMarketplaceAutoInstallRetryCount"] = retry_count
                m["officialMarketplaceAutoInstallLastAttemptTime"] = now
                m["officialMarketplaceAutoInstallNextRetryTime"] = next_retry
                return m

            save_global_config(_gcs_fail)
            log_event(
                "tengu_official_marketplace_auto_install",
                _event_payload(installed=False, skipped=True, gcs_unavailable=True, retry_count=retry_count),
            )
            return OfficialMarketplaceCheckResult(installed=False, skipped=True, reason="gcs_unavailable")

        git_ok = await check_git_available()
        if not git_ok:
            log_for_debugging("Git not available, skipping official marketplace auto-install")
            retry_count = (cfg.official_marketplace_auto_install_retry_count or 0) + 1
            now = int(time.time() * 1000)
            next_retry = now + int(_calculate_next_retry_delay(retry_count))
            config_save_failed = False
            try:

                def _git_fail(c: dict[str, Any]) -> dict[str, Any]:
                    m = dict(c)
                    m["officialMarketplaceAutoInstallAttempted"] = True
                    m["officialMarketplaceAutoInstalled"] = False
                    m["officialMarketplaceAutoInstallFailReason"] = "git_unavailable"
                    m["officialMarketplaceAutoInstallRetryCount"] = retry_count
                    m["officialMarketplaceAutoInstallLastAttemptTime"] = now
                    m["officialMarketplaceAutoInstallNextRetryTime"] = next_retry
                    return m

                save_global_config(_git_fail)
            except Exception as save_exc:
                config_save_failed = True
                log_error(to_error(save_exc))
                log_for_debugging(
                    f"Failed to save marketplace auto-install git_unavailable state: {save_exc}",
                    level="error",
                )
            log_event(
                "tengu_official_marketplace_auto_install",
                _event_payload(installed=False, skipped=True, git_unavailable=True, retry_count=retry_count),
            )
            return OfficialMarketplaceCheckResult(
                installed=False,
                skipped=True,
                reason="git_unavailable",
                config_save_failed=config_save_failed,
            )

        log_for_debugging("Attempting to auto-install official marketplace")
        await add_marketplace_source(dict(OFFICIAL_MARKETPLACE_SOURCE))

        log_for_debugging("Successfully auto-installed official marketplace")
        prev_retry = cfg.official_marketplace_auto_install_retry_count or 0

        def _success_git(c: dict[str, Any]) -> dict[str, Any]:
            m = dict(c)
            m["officialMarketplaceAutoInstallAttempted"] = True
            m["officialMarketplaceAutoInstalled"] = True
            for k in (
                "officialMarketplaceAutoInstallFailReason",
                "officialMarketplaceAutoInstallRetryCount",
                "officialMarketplaceAutoInstallLastAttemptTime",
                "officialMarketplaceAutoInstallNextRetryTime",
            ):
                m.pop(k, None)
            return m

        save_global_config(_success_git)
        log_event(
            "tengu_official_marketplace_auto_install",
            _event_payload(installed=True, skipped=False, retry_count=prev_retry),
        )
        return OfficialMarketplaceCheckResult(installed=True, skipped=False)

    except Exception as error:
        error_message_str = error_message(error)
        if "xcrun: error:" in error_message_str:
            mark_git_unavailable()
            log_for_debugging(
                "Official marketplace auto-install: git is a non-functional macOS xcrun shim, "
                "treating as git_unavailable",
            )
            log_event(
                "tengu_official_marketplace_auto_install",
                _event_payload(
                    installed=False,
                    skipped=True,
                    git_unavailable=True,
                    macos_xcrun_shim=True,
                ),
            )
            return OfficialMarketplaceCheckResult(installed=False, skipped=True, reason="git_unavailable")

        log_for_debugging(
            f"Failed to auto-install official marketplace: {error_message_str}",
            level="error",
        )
        log_error(to_error(error))

        retry_count = (cfg.official_marketplace_auto_install_retry_count or 0) + 1
        now = int(time.time() * 1000)
        next_retry = now + int(_calculate_next_retry_delay(retry_count))
        config_save_failed = False
        try:

            def _unknown_fail(c: dict[str, Any]) -> dict[str, Any]:
                m = dict(c)
                m["officialMarketplaceAutoInstallAttempted"] = True
                m["officialMarketplaceAutoInstalled"] = False
                m["officialMarketplaceAutoInstallFailReason"] = "unknown"
                m["officialMarketplaceAutoInstallRetryCount"] = retry_count
                m["officialMarketplaceAutoInstallLastAttemptTime"] = now
                m["officialMarketplaceAutoInstallNextRetryTime"] = next_retry
                return m

            save_global_config(_unknown_fail)
        except Exception as save_exc:
            config_save_failed = True
            log_error(to_error(save_exc))
            log_for_debugging(
                f"Failed to save marketplace auto-install failure state: {save_exc}",
                level="error",
            )

        log_event(
            "tengu_official_marketplace_auto_install",
            _event_payload(installed=False, skipped=True, failed=True, retry_count=retry_count),
        )
        return OfficialMarketplaceCheckResult(
            installed=False,
            skipped=True,
            reason="unknown",
            config_save_failed=config_save_failed,
        )


async def run_official_marketplace_startup_check() -> None:
    await check_and_install_official_marketplace()


__all__ = [
    "RETRY_CONFIG",
    "OfficialMarketplaceCheckResult",
    "OfficialMarketplaceSkipReason",
    "check_and_install_official_marketplace",
    "is_official_marketplace_auto_install_disabled",
    "run_official_marketplace_startup_check",
]
