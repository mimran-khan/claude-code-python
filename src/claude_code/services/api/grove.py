"""
Grove notification settings (account OAuth API).

Migrated from: services/api/grove.ts
"""

from __future__ import annotations

import asyncio
import sys
import time
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import httpx

from ...constants.oauth import CLAUDE_AI_PROFILE_SCOPE, OAUTH_BETA_HEADER, get_oauth_config
from ...utils.config_utils import get_global_config, load_global_config_dict, save_global_config
from ...utils.env_utils import is_env_truthy
from ...utils.http import get_auth_headers, get_user_agent
from ...utils.model.providers import get_api_provider
from ..analytics.index import log_event
from ..oauth.client import get_claude_ai_oauth_tokens

T = TypeVar("T")

GROVE_CACHE_EXPIRATION_MS = 24 * 60 * 60 * 1000


@dataclass
class AccountSettings:
    grove_enabled: bool | None
    grove_notice_viewed_at: str | None


@dataclass
class GroveConfig:
    grove_enabled: bool
    domain_excluded: bool
    notice_is_grace_period: bool
    notice_reminder_frequency: int | None


@dataclass(frozen=True)
class ApiResult(Generic[T]):
    """Distinguishes API success from failure (matches TS ApiResult)."""

    success: bool
    data: T | None = None


def _is_essential_traffic_only() -> bool:
    import os

    return is_env_truthy(os.getenv("CLAUDE_CODE_ESSENTIAL_TRAFFIC_ONLY", ""))


def is_consumer_subscriber() -> bool:
    """True if user is a Claude.ai consumer (pro/max) subscriber."""
    tokens = get_claude_ai_oauth_tokens()
    if not tokens:
        return False
    st = tokens.subscription_type
    return st in ("pro", "max")


def get_oauth_account_uuid() -> str | None:
    cfg = get_global_config()
    oa = cfg.oauth_account
    if not oa or not isinstance(oa, dict):
        return None
    u = oa.get("accountUuid")
    return str(u) if u else None


def _auth_headers_for_oauth_account_api() -> dict[str, str] | None:
    """Prefer OAuth bearer + beta header when profile scope is present; else API key."""
    tokens = get_claude_ai_oauth_tokens()
    scopes = list(tokens.scopes) if tokens else []
    if tokens and tokens.access_token and CLAUDE_AI_PROFILE_SCOPE in scopes:
        return {
            "Authorization": f"Bearer {tokens.access_token}",
            "anthropic-beta": OAUTH_BETA_HEADER,
            "Content-Type": "application/json",
        }
    auth = get_auth_headers()
    if auth.error:
        return None
    return {**auth.headers, "Content-Type": "application/json"}


_settings_success: AccountSettings | None = None
_notice_config_success: GroveConfig | None = None


def _clear_grove_settings_memo() -> None:
    global _settings_success
    _settings_success = None


def _clear_grove_notice_config_memo() -> None:
    global _notice_config_success
    _notice_config_success = None


async def get_grove_settings() -> ApiResult[AccountSettings]:
    """GET /api/oauth/account/settings — memoized until cleared."""
    global _settings_success
    if _is_essential_traffic_only():
        return ApiResult(success=False)
    if _settings_success is not None:
        return ApiResult(success=True, data=_settings_success)

    headers = _auth_headers_for_oauth_account_api()
    if not headers:
        return ApiResult(success=False)

    url = f"{get_oauth_config().BASE_API_URL}/api/oauth/account/settings"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                url,
                headers={**headers, "User-Agent": get_user_agent()},
            )
            r.raise_for_status()
            d = r.json()
    except Exception:
        return ApiResult(success=False)

    if not isinstance(d, dict):
        return ApiResult(success=False)
    _settings_success = AccountSettings(
        grove_enabled=d.get("grove_enabled"),
        grove_notice_viewed_at=d.get("grove_notice_viewed_at"),
    )
    return ApiResult(success=True, data=_settings_success)


async def mark_grove_notice_viewed() -> None:
    """POST grove_notice_viewed; clears settings memo so viewed_at is fresh."""
    headers = _auth_headers_for_oauth_account_api()
    if not headers:
        return
    url = f"{get_oauth_config().BASE_API_URL}/api/oauth/account/grove_notice_viewed"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(
                url,
                headers={**headers, "User-Agent": get_user_agent()},
                json={},
            )
    except Exception:
        return
    _clear_grove_settings_memo()


async def update_grove_settings(grove_enabled: bool) -> None:
    """PATCH account settings; clears settings memo."""
    headers = _auth_headers_for_oauth_account_api()
    if not headers:
        return
    url = f"{get_oauth_config().BASE_API_URL}/api/oauth/account/settings"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.patch(
                url,
                headers={**headers, "User-Agent": get_user_agent()},
                json={"grove_enabled": grove_enabled},
            )
    except Exception:
        return
    _clear_grove_settings_memo()


async def get_grove_notice_config() -> ApiResult[GroveConfig]:
    """GET /api/claude_code_grove — short timeout; memoized until cleared."""
    global _notice_config_success
    if _is_essential_traffic_only():
        return ApiResult(success=False)
    if _notice_config_success is not None:
        return ApiResult(success=True, data=_notice_config_success)

    headers = _auth_headers_for_oauth_account_api()
    if not headers:
        return ApiResult(success=False)

    url = f"{get_oauth_config().BASE_API_URL}/api/claude_code_grove"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                url,
                headers={**headers, "User-Agent": get_user_agent()},
            )
            r.raise_for_status()
            raw = r.json()
    except Exception:
        return ApiResult(success=False)

    if not isinstance(raw, dict):
        return ApiResult(success=False)
    grove_enabled = raw.get("grove_enabled")
    if not isinstance(grove_enabled, bool):
        return ApiResult(success=False)
    domain_excluded = raw.get("domain_excluded")
    notice_is_grace_period = raw.get("notice_is_grace_period")
    notice_reminder_frequency = raw.get("notice_reminder_frequency")
    _notice_config_success = GroveConfig(
        grove_enabled=grove_enabled,
        domain_excluded=bool(domain_excluded) if domain_excluded is not None else False,
        notice_is_grace_period=bool(notice_is_grace_period) if notice_is_grace_period is not None else True,
        notice_reminder_frequency=int(notice_reminder_frequency)
        if isinstance(notice_reminder_frequency, int)
        else None,
    )
    return ApiResult(success=True, data=_notice_config_success)


async def _fetch_and_store_grove_config(account_id: str) -> None:
    result = await get_grove_notice_config()
    if not result.success or result.data is None:
        return
    grove_enabled = result.data.grove_enabled
    data = load_global_config_dict()
    cache_raw = data.get("groveConfigCache")
    cache: dict[str, Any] = dict(cache_raw) if isinstance(cache_raw, dict) else {}
    cached_entry = cache.get(account_id)
    now_ms = int(time.time() * 1000)
    if isinstance(cached_entry, dict) and (
        cached_entry.get("grove_enabled") == grove_enabled
        and now_ms - int(cached_entry.get("timestamp") or 0) <= GROVE_CACHE_EXPIRATION_MS
    ):
        return

    def updater(cur: dict[str, Any]) -> dict[str, Any]:
        n = dict(cur)
        prev = n.get("groveConfigCache")
        merged: dict[str, Any] = dict(prev) if isinstance(prev, dict) else {}
        merged[account_id] = {"grove_enabled": grove_enabled, "timestamp": now_ms}
        n["groveConfigCache"] = merged
        return n

    save_global_config(updater)


async def is_qualified_for_grove() -> bool:
    """Non-blocking, cache-first eligibility (mirrors TS)."""
    if not is_consumer_subscriber():
        return False
    account_id = get_oauth_account_uuid()
    if not account_id:
        return False

    data = load_global_config_dict()
    cache_raw = data.get("groveConfigCache")
    cache: dict[str, Any] = dict(cache_raw) if isinstance(cache_raw, dict) else {}
    cached_entry = cache.get(account_id)
    now_ms = int(time.time() * 1000)

    if not cached_entry:
        asyncio.create_task(_fetch_and_store_grove_config(account_id))
        return False

    if not isinstance(cached_entry, dict):
        return False

    ts = int(cached_entry.get("timestamp") or 0)
    if now_ms - ts > GROVE_CACHE_EXPIRATION_MS:
        asyncio.create_task(_fetch_and_store_grove_config(account_id))
        return bool(cached_entry.get("grove_enabled"))

    return bool(cached_entry.get("grove_enabled"))


def calculate_should_show_grove(
    settings_result: ApiResult[AccountSettings],
    config_result: ApiResult[GroveConfig],
    show_if_already_viewed: bool,
) -> bool:
    if not settings_result.success or settings_result.data is None:
        return False
    if not config_result.success or config_result.data is None:
        return False

    settings = settings_result.data
    config = config_result.data

    if settings.grove_enabled is not None:
        return False
    if show_if_already_viewed:
        return True
    if not config.notice_is_grace_period:
        return True
    reminder_frequency = config.notice_reminder_frequency
    if reminder_frequency is not None and settings.grove_notice_viewed_at:
        viewed = settings.grove_notice_viewed_at
        try:
            from datetime import datetime

            viewed_dt = datetime.fromisoformat(viewed.replace("Z", "+00:00"))
            days_since = (time.time() - viewed_dt.timestamp()) / (60 * 60 * 24)
            return int(days_since) >= int(reminder_frequency)
        except (ValueError, TypeError, OSError):
            return True
    viewed_at = settings.grove_notice_viewed_at
    return viewed_at is None


async def check_grove_for_non_interactive() -> None:
    """CLI non-interactive Grove terms check (stderr + optional exit)."""
    if get_api_provider() != "firstParty":
        return
    settings_result, config_result = await asyncio.gather(
        get_grove_settings(),
        get_grove_notice_config(),
    )
    should_show = calculate_should_show_grove(
        settings_result,
        config_result,
        False,
    )
    if not should_show:
        return

    config = config_result.data if config_result.success else None
    log_event(
        "tengu_grove_print_viewed",
        {
            "dismissable": bool(config.notice_is_grace_period) if config else False,
        },
    )
    if config is None or config.notice_is_grace_period:
        sys.stderr.write(
            "\nAn update to our Consumer Terms and Privacy Policy will take effect "
            "on October 8, 2025. Run `claude` to review the updated terms.\n\n",
        )
        await mark_grove_notice_viewed()
    else:
        sys.stderr.write(
            "\n[ACTION REQUIRED] An update to our Consumer Terms and Privacy Policy "
            "has taken effect on October 8, 2025. You must run `claude` to review "
            "the updated terms.\n\n",
        )
        raise SystemExit(1)
