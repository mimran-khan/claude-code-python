"""
Overage credit grant API and cache.

Migrated from: services/api/overageCreditGrant.ts
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from ...constants.oauth import get_oauth_config
from ...utils.http import get_user_agent

logger = structlog.get_logger(__name__)

CACHE_TTL_MS = 60 * 60 * 1000

_overage_grant_cache: dict[str, dict[str, Any]] = {}
_cache_lock = asyncio.Lock()


@dataclass
class OverageCreditGrantInfo:
    available: bool
    eligible: bool
    granted: bool
    amount_minor_units: int | None
    currency: str | None


def _oauth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": get_user_agent(),
    }


async def fetch_overage_credit_grant(
    access_token: str,
    org_uuid: str,
    client: httpx.AsyncClient | None = None,
) -> OverageCreditGrantInfo | None:
    """Fetch grant info from the backend."""
    base = get_oauth_config().BASE_API_URL
    url = f"{base}/api/oauth/organizations/{org_uuid}/overage_credit_grant"
    close = False
    if client is None:
        client = httpx.AsyncClient(timeout=30.0)
        close = True
    try:
        try:
            r = await client.get(url, headers=_oauth_headers(access_token))
            r.raise_for_status()
            raw = r.json()
        except Exception as exc:
            logger.warning("overage_credit_grant_fetch_failed", error=str(exc))
            return None
        if not isinstance(raw, dict):
            return None
        amt = raw.get("amount_minor_units")
        return OverageCreditGrantInfo(
            available=bool(raw.get("available")),
            eligible=bool(raw.get("eligible")),
            granted=bool(raw.get("granted")),
            amount_minor_units=int(amt) if isinstance(amt, (int, float)) else None,
            currency=raw.get("currency") if isinstance(raw.get("currency"), str) else None,
        )
    finally:
        if close:
            await client.aclose()


def get_cached_overage_credit_grant(org_id: str | None) -> OverageCreditGrantInfo | None:
    """Return cached grant info if fresh, else None."""
    if not org_id:
        return None
    cached = _overage_grant_cache.get(org_id)
    if not cached:
        return None
    if time.time() * 1000 - float(cached["timestamp"]) > CACHE_TTL_MS:
        return None
    info = cached["info"]
    if not isinstance(info, OverageCreditGrantInfo):
        return None
    return info


def invalidate_overage_credit_grant_cache(org_id: str | None) -> None:
    if org_id and org_id in _overage_grant_cache:
        del _overage_grant_cache[org_id]


async def refresh_overage_credit_grant_cache(
    access_token: str,
    org_id: str | None,
    *,
    is_essential_traffic_only: Callable[[], bool] = lambda: False,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Fetch and cache grant info."""
    if is_essential_traffic_only() or not org_id:
        return
    info = await fetch_overage_credit_grant(access_token, org_id, client=client)
    if info is None:
        return
    async with _cache_lock:
        prev = _overage_grant_cache.get(org_id)
        data_unchanged = (
            prev
            and isinstance(prev.get("info"), OverageCreditGrantInfo)
            and prev["info"].available == info.available
            and prev["info"].eligible == info.eligible
            and prev["info"].granted == info.granted
            and prev["info"].amount_minor_units == info.amount_minor_units
            and prev["info"].currency == info.currency
        )
        now_ms = time.time() * 1000
        if data_unchanged and prev and now_ms - float(prev["timestamp"]) <= CACHE_TTL_MS:
            return
        _overage_grant_cache[org_id] = {"info": info, "timestamp": now_ms}


def format_grant_amount(info: OverageCreditGrantInfo) -> str | None:
    if info.amount_minor_units is None or not info.currency:
        return None
    if info.currency.upper() == "USD":
        dollars = info.amount_minor_units / 100
        return f"${dollars:.0f}" if dollars == int(dollars) else f"${dollars:.2f}"
    return None
