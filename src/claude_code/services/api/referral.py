"""
Referral / guest passes eligibility API.

Migrated from: services/api/referral.ts
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx
import structlog

from ...constants.oauth import get_oauth_config
from ...utils.http import get_user_agent

logger = structlog.get_logger(__name__)

CACHE_EXPIRATION_MS = 24 * 60 * 60 * 1000

ReferralCampaign = Literal["claude_code_guest_pass"]

_passes_cache: dict[str, dict[str, Any]] = {}
_inflight: dict[str, asyncio.Task[ReferralEligibilityResponse | None]] = {}


@dataclass
class ReferrerRewardInfo:
    currency: str
    amount_minor_units: int


@dataclass
class ReferralEligibilityResponse:
    eligible: bool
    referrer_reward: ReferrerRewardInfo | None = None
    remaining_passes: int | None = None


@dataclass
class ReferralRedemptionsResponse:
    redemptions: list[dict[str, Any]] = field(default_factory=list)


def _org_headers(access_token: str, org_uuid: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "x-organization-uuid": org_uuid,
        "User-Agent": get_user_agent(),
    }


def _parse_eligibility_payload(data: object) -> ReferralEligibilityResponse:
    if not isinstance(data, dict):
        return ReferralEligibilityResponse(eligible=False)
    reward_raw = data.get("referrer_reward")
    reward: ReferrerRewardInfo | None = None
    if isinstance(reward_raw, dict):
        cur = reward_raw.get("currency")
        amt = reward_raw.get("amount_minor_units")
        if isinstance(cur, str) and isinstance(amt, (int, float)):
            reward = ReferrerRewardInfo(currency=cur, amount_minor_units=int(amt))
    rem = data.get("remaining_passes")
    return ReferralEligibilityResponse(
        eligible=bool(data.get("eligible")),
        referrer_reward=reward,
        remaining_passes=int(rem) if isinstance(rem, (int, float)) else None,
    )


async def fetch_referral_eligibility(
    access_token: str,
    org_uuid: str,
    campaign: ReferralCampaign = "claude_code_guest_pass",
    client: httpx.AsyncClient | None = None,
) -> ReferralEligibilityResponse:
    base = get_oauth_config().BASE_API_URL
    url = f"{base}/api/oauth/organizations/{org_uuid}/referral/eligibility"

    async def _req(c: httpx.AsyncClient) -> ReferralEligibilityResponse:
        try:
            r = await c.get(
                url,
                headers=_org_headers(access_token, org_uuid),
                params={"campaign": campaign},
                timeout=5.0,
            )
            r.raise_for_status()
            return _parse_eligibility_payload(r.json())
        except Exception as exc:
            logger.warning("referral_eligibility_failed", error=str(exc))
            return ReferralEligibilityResponse(eligible=False)

    if client is not None:
        return await _req(client)
    async with httpx.AsyncClient(timeout=30.0) as c:
        return await _req(c)


async def fetch_referral_redemptions(
    access_token: str,
    org_uuid: str,
    campaign: str = "claude_code_guest_pass",
    client: httpx.AsyncClient | None = None,
) -> ReferralRedemptionsResponse:
    base = get_oauth_config().BASE_API_URL
    url = f"{base}/api/oauth/organizations/{org_uuid}/referral/redemptions"

    async def _req(c: httpx.AsyncClient) -> ReferralRedemptionsResponse:
        try:
            r = await c.get(
                url,
                headers=_org_headers(access_token, org_uuid),
                params={"campaign": campaign},
                timeout=10.0,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            logger.warning("referral_redemptions_failed", error=str(exc))
            return ReferralRedemptionsResponse()
        if not isinstance(data, dict):
            return ReferralRedemptionsResponse()
        reds = data.get("redemptions", data.get("data", []))
        if not isinstance(reds, list):
            return ReferralRedemptionsResponse()
        return ReferralRedemptionsResponse(redemptions=[x for x in reds if isinstance(x, dict)])

    if client is not None:
        return await _req(client)
    async with httpx.AsyncClient(timeout=30.0) as c:
        return await _req(c)


CURRENCY_SYMBOLS: dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "BRL": "R$",
    "CAD": "CA$",
    "AUD": "A$",
    "NZD": "NZ$",
    "SGD": "S$",
}


def format_credit_amount(reward: ReferrerRewardInfo) -> str:
    symbol = CURRENCY_SYMBOLS.get(reward.currency, f"{reward.currency} ")
    amount = reward.amount_minor_units / 100
    formatted = str(int(amount)) if amount % 1 == 0 else f"{amount:.2f}"
    return f"{symbol}{formatted}"


def check_cached_passes_eligibility(org_id: str | None) -> dict[str, bool]:
    if not org_id:
        return {"eligible": False, "needs_refresh": False, "has_cache": False}
    cached = _passes_cache.get(org_id)
    if not cached:
        return {"eligible": False, "needs_refresh": True, "has_cache": False}
    ts = float(cached.get("timestamp", 0))
    needs_refresh = time.time() * 1000 - ts > CACHE_EXPIRATION_MS
    return {
        "eligible": bool(cached.get("eligible")),
        "needs_refresh": needs_refresh,
        "has_cache": True,
    }


def get_cached_referrer_reward(org_id: str | None) -> ReferrerRewardInfo | None:
    if not org_id:
        return None
    cached = _passes_cache.get(org_id)
    if not cached:
        return None
    r = cached.get("referrer_reward")
    return r if isinstance(r, ReferrerRewardInfo) else None


def get_cached_remaining_passes(org_id: str | None) -> int | None:
    if not org_id:
        return None
    cached = _passes_cache.get(org_id)
    if not cached:
        return None
    v = cached.get("remaining_passes")
    return int(v) if isinstance(v, (int, float)) else None


async def fetch_and_store_passes_eligibility(
    access_token: str,
    org_id: str,
    client: httpx.AsyncClient | None = None,
) -> ReferralEligibilityResponse | None:
    existing = _inflight.get(org_id)
    if existing is not None:
        return await existing

    async def _inner() -> ReferralEligibilityResponse | None:
        try:
            response = await fetch_referral_eligibility(access_token, org_id, client=client)
            _passes_cache[org_id] = {
                "eligible": response.eligible,
                "referrer_reward": response.referrer_reward,
                "remaining_passes": response.remaining_passes,
                "timestamp": time.time() * 1000,
            }
            logger.debug("passes_eligibility_cached", org_id=org_id, eligible=response.eligible)
            return response
        except Exception as exc:
            logger.warning("passes_eligibility_store_failed", error=str(exc))
            return None
        finally:
            _inflight.pop(org_id, None)

    task = asyncio.create_task(_inner())
    _inflight[org_id] = task
    return await task


async def get_cached_or_fetch_passes_eligibility(
    access_token: str,
    org_id: str | None,
    *,
    should_check: Callable[[], bool],
    client: httpx.AsyncClient | None = None,
) -> ReferralEligibilityResponse | None:
    if not should_check() or not org_id:
        return None
    cached = _passes_cache.get(org_id)
    now = time.time() * 1000
    if not cached:
        asyncio.create_task(fetch_and_store_passes_eligibility(access_token, org_id, client=client))
        return None
    if now - float(cached.get("timestamp", 0)) > CACHE_EXPIRATION_MS:
        asyncio.create_task(fetch_and_store_passes_eligibility(access_token, org_id, client=client))
    rr = cached.get("referrer_reward")
    return ReferralEligibilityResponse(
        eligible=bool(cached.get("eligible")),
        referrer_reward=rr if isinstance(rr, ReferrerRewardInfo) else None,
        remaining_passes=int(cached["remaining_passes"])
        if isinstance(cached.get("remaining_passes"), (int, float))
        else None,
    )


async def prefetch_passes_eligibility(
    access_token: str,
    org_id: str | None,
    *,
    should_check: Callable[[], bool],
    is_essential_traffic_only: Callable[[], bool] = lambda: False,
    client: httpx.AsyncClient | None = None,
) -> None:
    if is_essential_traffic_only() or not org_id or not should_check():
        return
    await get_cached_or_fetch_passes_eligibility(
        access_token,
        org_id,
        should_check=should_check,
        client=client,
    )
