"""
Poll remote CCR session events (SDK-shaped JSON).

Migrated from: utils/teleport.tsx (pollRemoteSessionEvents)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)

SessionPollStatus = Literal["idle", "running", "requires_action", "archived"]


@dataclass
class PollRemoteSessionResponse:
    new_events: list[dict[str, Any]]
    last_event_id: str | None
    branch: str | None = None
    session_status: SessionPollStatus | None = None


def _session_headers(access_token: str, org_uuid: str) -> dict[str, str]:
    from .api import CCR_BYOC_BETA, get_oauth_headers

    h = dict(get_oauth_headers(access_token))
    h["Content-Type"] = "application/json"
    h["anthropic-version"] = "2023-06-01"
    h["anthropic-beta"] = CCR_BYOC_BETA
    h["x-organization-uuid"] = org_uuid
    return h


async def poll_remote_session_events(
    session_id: str,
    after_id: str | None = None,
    *,
    skip_metadata: bool = False,
    base_api_url: str | None = None,
) -> PollRemoteSessionResponse:
    import httpx

    from claude_code.constants.oauth import get_oauth_config

    from .api import prepare_api_request

    creds = await prepare_api_request()
    if not creds.access_token or not creds.org_uuid:
        raise RuntimeError("No access token or org UUID for polling")

    cfg = get_oauth_config()
    base = base_api_url or cfg.BASE_API_URL
    headers = _session_headers(creds.access_token, creds.org_uuid)
    events_url = f"{base}/v1/sessions/{session_id}/events"

    sdk_messages: list[dict[str, Any]] = []
    cursor: str | None = after_id
    max_pages = 50

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(max_pages):
            params = {"after_id": cursor} if cursor else None
            r = await client.get(events_url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            chunk = data.get("data") or []
            if not isinstance(chunk, list):
                raise RuntimeError("Invalid events response")
            for event in chunk:
                if not isinstance(event, dict) or "type" not in event:
                    continue
                if event["type"] in ("env_manager_log", "control_response"):
                    continue
                if "session_id" in event:
                    sdk_messages.append(event)
            last_id = data.get("last_id")
            if not last_id:
                break
            cursor = str(last_id)
            if not data.get("has_more"):
                break

    if skip_metadata:
        return PollRemoteSessionResponse(
            new_events=sdk_messages,
            last_event_id=cursor,
        )

    branch: str | None = None
    session_status: SessionPollStatus | None = None
    try:
        meta_url = f"{base}/v1/sessions/{session_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            mr = await client.get(meta_url, headers=headers)
            if mr.status_code == 200:
                body = mr.json()
                session_status = body.get("session_status")
                ctx = body.get("session_context") or {}
                outcomes = ctx.get("outcomes") or []
                for oc in outcomes:
                    if isinstance(oc, dict) and oc.get("type") == "git_repository":
                        gi = oc.get("git_info") or {}
                        branches = gi.get("branches") or []
                        if branches:
                            branch = str(branches[0])
                            break
    except Exception as e:
        logger.debug("teleport poll metadata fetch failed: %s", e)

    return PollRemoteSessionResponse(
        new_events=sdk_messages,
        last_event_id=cursor,
        branch=branch,
        session_status=session_status,
    )
