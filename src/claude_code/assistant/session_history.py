"""
Paginated session event history from the organization API.

Migrated from: assistant/sessionHistory.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from ..constants.oauth import get_oauth_config
from ..utils.debug import log_for_debugging
from ..utils.teleport.api import get_oauth_headers, prepare_api_request

HISTORY_PAGE_SIZE = 100


@dataclass
class HistoryPage:
    """One page of session events (chronological within the page)."""

    events: list[dict[str, Any]]
    first_id: str | None
    has_more: bool


@dataclass(frozen=True)
class HistoryAuthCtx:
    """Precomputed base URL and headers for session history requests."""

    base_url: str
    headers: dict[str, str]


async def create_history_auth_ctx(session_id: str) -> HistoryAuthCtx:
    """Resolve OAuth token and build URL + headers for ``session_id`` events."""
    prep = await prepare_api_request()
    base = get_oauth_config().BASE_API_URL.rstrip("/")
    return HistoryAuthCtx(
        base_url=f"{base}/v1/sessions/{session_id}/events",
        headers={
            **get_oauth_headers(prep.access_token),
            "anthropic-beta": "ccr-byoc-2025-07-29",
            "x-organization-uuid": prep.org_uuid,
        },
    )


async def _fetch_page(
    ctx: HistoryAuthCtx,
    params: dict[str, str | int | bool],
    label: str,
) -> HistoryPage | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(ctx.base_url, headers=ctx.headers, params=params)
    except httpx.HTTPError as exc:
        log_for_debugging(f"[{label}] HTTP error: {exc}")
        return None
    if response.status_code != 200:
        log_for_debugging(f"[{label}] HTTP {response.status_code}")
        return None
    try:
        body = response.json()
    except ValueError:
        log_for_debugging(f"[{label}] invalid JSON")
        return None
    data = body.get("data")
    if not isinstance(data, list):
        data = []
    return HistoryPage(
        events=data,
        first_id=body.get("first_id"),
        has_more=bool(body.get("has_more")),
    )


async def fetch_latest_events(
    ctx: HistoryAuthCtx,
    limit: int = HISTORY_PAGE_SIZE,
) -> HistoryPage | None:
    """Newest page: last ``limit`` events, chronological (``anchor_to_latest``)."""
    return await _fetch_page(
        ctx,
        {"limit": limit, "anchor_to_latest": True},
        "fetch_latest_events",
    )


async def fetch_older_events(
    ctx: HistoryAuthCtx,
    before_id: str,
    limit: int = HISTORY_PAGE_SIZE,
) -> HistoryPage | None:
    """Older page: events immediately before ``before_id``."""
    return await _fetch_page(
        ctx,
        {"limit": limit, "before_id": before_id},
        "fetch_older_events",
    )
