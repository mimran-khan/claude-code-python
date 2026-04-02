"""Bridge session create/fetch/archive (ported from bridge/createSession.ts)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypedDict

import httpx

from claude_code.bridge.debug_utils import error_message, extract_error_detail
from claude_code.bridge.session_id_compat import to_compat_session_id

logger = logging.getLogger(__name__)


class SessionEvent(TypedDict):
    type: str
    data: Any


async def create_bridge_session(
    *,
    environment_id: str,
    title: str | None,
    events: list[SessionEvent],
    git_repo_url: str | None,
    branch: str,
    signal: Any = None,
    base_url: str | None = None,
    get_access_token: Callable[[], str | None] | None = None,
    permission_mode: str | None = None,
) -> str | None:
    # TODO: org UUID, OAuth headers, git source building, get_main_loop_model
    access_token = get_access_token() if get_access_token else None
    if not access_token:
        logger.debug("[bridge] No access token for session creation")
        return None
    org_uuid = ""  # TODO: await get_organization_uuid()
    if not org_uuid:
        logger.debug("[bridge] No org UUID for session creation")
        return None
    api_base = base_url or ""
    body: dict[str, Any] = {
        "events": events,
        "session_context": {"sources": [], "outcomes": [], "model": "claude-3-5-sonnet-20241022"},
        "environment_id": environment_id,
        "source": "remote-control",
    }
    if title is not None:
        body["title"] = title
    if permission_mode:
        body["permission_mode"] = permission_mode
    headers = {
        "Authorization": f"Bearer {access_token}",
        "anthropic-beta": "ccr-byoc-2025-07-29",
        "x-organization-uuid": org_uuid,
    }
    url = f"{api_base.rstrip('/')}/v1/sessions"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=body, headers=headers, timeout=60.0)
    except Exception as e:
        logger.debug("[bridge] Session creation request failed: %s", error_message(e))
        return None
    if r.status_code not in (200, 201):
        detail = extract_error_detail(r.json() if r.content else None)
        logger.debug(
            "[bridge] Session creation failed status %s%s",
            r.status_code,
            f": {detail}" if detail else "",
        )
        return None
    data = r.json()
    if not isinstance(data, dict) or not isinstance(data.get("id"), str):
        logger.debug("[bridge] No session ID in response")
        return None
    return data["id"]


async def get_bridge_session(
    session_id: str,
    opts: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    opts = opts or {}
    get_tok = opts.get("get_access_token")
    access_token = get_tok() if callable(get_tok) else None
    if not access_token:
        return None
    org_uuid = opts.get("org_uuid") or ""
    base = opts.get("base_url") or ""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "anthropic-beta": "ccr-byoc-2025-07-29",
        "x-organization-uuid": org_uuid,
    }
    url = f"{base.rstrip('/')}/v1/sessions/{session_id}"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers, timeout=10.0)
    except Exception as e:
        logger.debug("[bridge] Session fetch failed: %s", error_message(e))
        return None
    if r.status_code != 200:
        return None
    out = r.json()
    return out if isinstance(out, dict) else None


async def archive_bridge_session(
    session_id: str,
    opts: dict[str, Any] | None = None,
) -> None:
    opts = opts or {}
    get_tok = opts.get("get_access_token")
    access_token = get_tok() if callable(get_tok) else None
    if not access_token:
        logger.debug("[bridge] No access token for session archive")
        return
    org_uuid = opts.get("org_uuid") or ""
    base = opts.get("base_url") or ""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "anthropic-beta": "ccr-byoc-2025-07-29",
        "x-organization-uuid": org_uuid,
    }
    url = f"{base.rstrip('/')}/v1/sessions/{session_id}/archive"
    timeout_s = (opts.get("timeout_ms") or 10_000) / 1000.0
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json={}, headers=headers, timeout=timeout_s)
    if r.status_code == 200:
        logger.debug("[bridge] Session %s archived successfully", session_id)
    else:
        detail = extract_error_detail(r.json() if r.content else None)
        logger.debug(
            "[bridge] Session archive failed %s%s",
            r.status_code,
            f": {detail}" if detail else "",
        )


async def update_bridge_session_title(
    session_id: str,
    title: str,
    opts: dict[str, Any] | None = None,
) -> None:
    opts = opts or {}
    get_tok = opts.get("get_access_token")
    access_token = get_tok() if callable(get_tok) else None
    if not access_token:
        return
    org_uuid = opts.get("org_uuid") or ""
    compat_id = to_compat_session_id(session_id)
    base = opts.get("base_url") or ""
    url = f"{base.rstrip('/')}/v1/sessions/{compat_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "anthropic-beta": "ccr-byoc-2025-07-29",
        "x-organization-uuid": org_uuid,
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.patch(url, json={"title": title}, headers=headers, timeout=10.0)
        if r.status_code != 200:
            logger.debug("[bridge] Title update failed %s", r.status_code)
    except Exception as e:
        logger.debug("[bridge] Title update request failed: %s", error_message(e))
