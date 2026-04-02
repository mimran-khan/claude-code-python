"""Ultrareview quota peek endpoint."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import structlog

from ...constants.oauth import get_oauth_config
from ...utils.teleport.api import get_oauth_headers, prepare_api_request

logger = structlog.get_logger(__name__)


@dataclass
class UltrareviewQuotaResponse:
    reviews_used: int
    reviews_limit: int
    reviews_remaining: int
    is_overage: bool


async def fetch_ultrareview_quota() -> UltrareviewQuotaResponse | None:
    """GET /v1/ultrareview/quota (subscriber only)."""
    prep = await prepare_api_request()
    if not prep.access_token:
        return None
    url = f"{get_oauth_config().BASE_API_URL}/v1/ultrareview/quota"
    headers = {
        **get_oauth_headers(prep.access_token),
        "x-organization-uuid": prep.org_uuid,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            d = r.json()
    except Exception as e:
        logger.debug("fetch_ultrareview_quota_failed", error=str(e))
        return None
    if not isinstance(d, dict):
        return None
    return UltrareviewQuotaResponse(
        reviews_used=int(d.get("reviews_used", 0)),
        reviews_limit=int(d.get("reviews_limit", 0)),
        reviews_remaining=int(d.get("reviews_remaining", 0)),
        is_overage=bool(d.get("is_overage", False)),
    )
