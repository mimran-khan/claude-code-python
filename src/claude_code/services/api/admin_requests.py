"""
Admin requests API (limit increase, seat upgrade).

Migrated from: services/api/adminRequests.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx

from ...constants.oauth import get_oauth_config
from ...utils.http import get_user_agent

AdminRequestType = Literal["limit_increase", "seat_upgrade"]
AdminRequestStatus = Literal["pending", "approved", "dismissed"]


@dataclass
class AdminRequestSeatUpgradeDetails:
    message: str | None = None
    current_seat_tier: str | None = None


@dataclass
class AdminRequestLimitIncrease:
    uuid: str
    status: AdminRequestStatus
    request_type: Literal["limit_increase"] = "limit_increase"
    details: None = None
    requester_uuid: str | None = None
    created_at: str = ""


@dataclass
class AdminRequestSeatUpgrade:
    uuid: str
    status: AdminRequestStatus
    request_type: Literal["seat_upgrade"] = "seat_upgrade"
    details: AdminRequestSeatUpgradeDetails | None = None
    requester_uuid: str | None = None
    created_at: str = ""


AdminRequest = AdminRequestLimitIncrease | AdminRequestSeatUpgrade


def _parse_status(raw: object) -> AdminRequestStatus:
    s = str(raw) if raw is not None else "pending"
    if s == "pending" or s == "approved" or s == "dismissed":
        return s
    return "pending"


def _parse_admin_request(data: dict[str, object]) -> AdminRequest:
    rt = data.get("request_type")
    uuid = str(data.get("uuid", ""))
    status = _parse_status(data.get("status", "pending"))
    created_at = str(data.get("created_at", ""))
    requester = data.get("requester_uuid")
    requester_uuid = str(requester) if requester is not None else None
    if rt == "seat_upgrade":
        raw = data.get("details")
        details: AdminRequestSeatUpgradeDetails | None = None
        if isinstance(raw, dict):
            details = AdminRequestSeatUpgradeDetails(
                message=raw.get("message") if isinstance(raw.get("message"), str) else None,
                current_seat_tier=raw.get("current_seat_tier")
                if isinstance(raw.get("current_seat_tier"), str)
                else None,
            )
        return AdminRequestSeatUpgrade(
            uuid=uuid,
            status=status,
            details=details,
            requester_uuid=requester_uuid,
            created_at=created_at,
        )
    return AdminRequestLimitIncrease(
        uuid=uuid,
        status=status,
        requester_uuid=requester_uuid,
        created_at=created_at,
    )


def _org_headers(access_token: str, org_uuid: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "x-organization-uuid": org_uuid,
        "User-Agent": get_user_agent(),
        "Content-Type": "application/json",
    }


async def create_admin_request(
    params: dict[str, object],
    *,
    access_token: str,
    org_uuid: str,
    client: httpx.AsyncClient | None = None,
) -> AdminRequest:
    """Create an admin request (limit increase or seat upgrade)."""
    base = get_oauth_config().BASE_API_URL
    url = f"{base}/api/oauth/organizations/{org_uuid}/admin_requests"
    headers = _org_headers(access_token, org_uuid)
    close = False
    if client is None:
        client = httpx.AsyncClient(timeout=30.0)
        close = True
    try:
        r = await client.post(url, json=params, headers=headers)
        r.raise_for_status()
        body = r.json()
        if not isinstance(body, dict):
            msg = "Invalid admin request response"
            raise ValueError(msg)
        return _parse_admin_request(body)
    finally:
        if close:
            await client.aclose()


async def get_my_admin_requests(
    request_type: AdminRequestType,
    statuses: list[AdminRequestStatus],
    *,
    access_token: str,
    org_uuid: str,
    client: httpx.AsyncClient | None = None,
) -> list[AdminRequest] | None:
    """Get pending admin requests for the current user."""
    base = get_oauth_config().BASE_API_URL
    url = f"{base}/api/oauth/organizations/{org_uuid}/admin_requests/me"
    qparams: list[tuple[str, str]] = [("request_type", request_type)]
    qparams.extend(("statuses", s) for s in statuses)
    headers = _org_headers(access_token, org_uuid)
    close = False
    if client is None:
        client = httpx.AsyncClient(timeout=30.0)
        close = True
    try:
        r = await client.get(url, headers=headers, params=qparams)
        r.raise_for_status()
        body = r.json()
        if body is None:
            return None
        if not isinstance(body, list):
            return None
        return [_parse_admin_request(item) for item in body if isinstance(item, dict)]
    finally:
        if close:
            await client.aclose()


@dataclass
class AdminRequestEligibilityResponse:
    request_type: AdminRequestType
    is_allowed: bool


async def check_admin_request_eligibility(
    request_type: AdminRequestType,
    *,
    access_token: str,
    org_uuid: str,
    client: httpx.AsyncClient | None = None,
) -> AdminRequestEligibilityResponse | None:
    """Check if a specific admin request type is allowed for this org."""
    base = get_oauth_config().BASE_API_URL
    url = f"{base}/api/oauth/organizations/{org_uuid}/admin_requests/eligibility?request_type={request_type}"
    headers = _org_headers(access_token, org_uuid)
    close = False
    if client is None:
        client = httpx.AsyncClient(timeout=30.0)
        close = True
    try:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        body = r.json()
        if not isinstance(body, dict):
            return None
        rt = body.get("request_type")
        allowed = body.get("is_allowed")
        if rt not in ("limit_increase", "seat_upgrade") or not isinstance(allowed, bool):
            return None
        return AdminRequestEligibilityResponse(request_type=rt, is_allowed=allowed)
    finally:
        if close:
            await client.aclose()
