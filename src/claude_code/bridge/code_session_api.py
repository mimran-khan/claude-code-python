"""CCR v2 code-session HTTP helpers (ported from bridge/codeSessionApi.ts)."""

from __future__ import annotations

import logging
from typing import Any, TypedDict, cast

import httpx

from claude_code.bridge.debug_utils import extract_error_detail

logger = logging.getLogger(__name__)

ANTHROPIC_VERSION = "2023-06-01"


def _oauth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "anthropic-version": ANTHROPIC_VERSION,
    }


async def create_code_session(
    base_url: str,
    access_token: str,
    title: str,
    timeout_ms: float,
    tags: list[str] | None = None,
) -> str | None:
    url = f"{base_url.rstrip('/')}/v1/code/sessions"
    body: dict[str, Any] = {"title": title, "bridge": {}}
    if tags:
        body["tags"] = tags
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                url,
                json=body,
                headers=_oauth_headers(access_token),
                timeout=timeout_ms / 1000.0,
            )
    except Exception as e:
        logger.debug("[code-session] Session create request failed: %s", e)
        return None
    if r.status_code not in (200, 201):
        detail = extract_error_detail(r.json() if r.content else None)
        logger.debug(
            "[code-session] Session create failed %s%s",
            r.status_code,
            f": {detail}" if detail else "",
        )
        return None
    data = r.json()
    sess = data.get("session") if isinstance(data, dict) else None
    sid = sess.get("id") if isinstance(sess, dict) else None
    if not isinstance(sid, str) or not sid.startswith("cse_"):
        logger.debug("[code-session] No session.id (cse_*) in response")
        return None
    return sid


class RemoteCredentials(TypedDict):
    worker_jwt: str
    api_base_url: str
    expires_in: int
    worker_epoch: int


async def fetch_remote_credentials(
    session_id: str,
    base_url: str,
    access_token: str,
    timeout_ms: float,
    trusted_device_token: str | None = None,
) -> RemoteCredentials | None:
    url = f"{base_url.rstrip('/')}/v1/code/sessions/{session_id}/bridge"
    h = _oauth_headers(access_token)
    if trusted_device_token:
        h["X-Trusted-Device-Token"] = trusted_device_token
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json={}, headers=h, timeout=timeout_ms / 1000.0)
    except Exception as e:
        logger.debug("[code-session] /bridge request failed: %s", e)
        return None
    if r.status_code != 200:
        detail = extract_error_detail(r.json() if r.content else None)
        logger.debug(
            "[code-session] /bridge failed %s%s",
            r.status_code,
            f": {detail}" if detail else "",
        )
        return None
    data = r.json()
    if not isinstance(data, dict):
        return None
    raw_epoch = data.get("worker_epoch")
    epoch = int(raw_epoch) if isinstance(raw_epoch, str) else raw_epoch
    if (
        not isinstance(data.get("worker_jwt"), str)
        or not isinstance(data.get("expires_in"), int)
        or not isinstance(data.get("api_base_url"), str)
        or not isinstance(epoch, int)
    ):
        logger.debug("[code-session] /bridge response malformed")
        return None
    return cast(
        RemoteCredentials,
        {
            "worker_jwt": data["worker_jwt"],
            "api_base_url": data["api_base_url"],
            "expires_in": data["expires_in"],
            "worker_epoch": epoch,
        },
    )
