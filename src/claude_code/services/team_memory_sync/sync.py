"""
Team memory HTTP sync (pull/push).

Migrated from: services/teamMemorySync/index.ts (core transport; full merge logic incremental).
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import httpx

from ...constants.oauth import OAUTH_BETA_HEADER, get_oauth_config
from ...utils.debug import log_for_debugging
from .types import SyncState, TeamMemorySyncFetchResult, TeamMemorySyncPushResult

TEAM_MEMORY_TIMEOUT_S = 30.0


def create_sync_state() -> SyncState:
    return SyncState()


def team_memory_endpoint(repo_slug: str) -> str:
    base = os.environ.get("TEAM_MEMORY_SYNC_URL") or get_oauth_config().BASE_API_URL
    return f"{base}/api/claude_code/team_memory?repo={quote(repo_slug, safe='')}"


def _oauth_headers() -> dict[str, str] | None:
    try:
        from ..oauth.client import get_claude_ai_oauth_tokens
    except ImportError:
        return None
    tokens = get_claude_ai_oauth_tokens()
    if not tokens or not tokens.access_token:
        return None
    return {
        "Authorization": f"Bearer {tokens.access_token}",
        "anthropic-beta": OAUTH_BETA_HEADER,
        "User-Agent": "claude-code-python",
    }


async def fetch_team_memory_once(
    state: SyncState,
    repo_slug: str,
    etag: str | None = None,
) -> TeamMemorySyncFetchResult:
    auth = _oauth_headers()
    if not auth:
        return TeamMemorySyncFetchResult(
            success=False,
            error="No OAuth token available for team memory sync",
            skip_retry=True,
            error_type="auth",
        )
    headers = dict(auth)
    if etag:
        headers["If-None-Match"] = f'"{etag.replace(chr(34), "")}"'
    url = team_memory_endpoint(repo_slug)
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers, timeout=TEAM_MEMORY_TIMEOUT_S)
    except httpx.TimeoutException:
        return TeamMemorySyncFetchResult(
            success=False,
            error="Team memory sync request timeout",
            error_type="timeout",
        )
    except httpx.RequestError:
        return TeamMemorySyncFetchResult(
            success=False,
            error="Cannot connect to server",
            error_type="network",
        )
    if r.status_code == 304:
        return TeamMemorySyncFetchResult(
            success=True,
            not_modified=True,
            checksum=etag,
        )
    if r.status_code == 404:
        state.last_known_checksum = None
        return TeamMemorySyncFetchResult(success=True, is_empty=True)
    if r.status_code != 200:
        return TeamMemorySyncFetchResult(
            success=False,
            error=r.text[:500],
            http_status=r.status_code,
            error_type="unknown",
        )
    data = r.json()
    if not isinstance(data, dict):
        return TeamMemorySyncFetchResult(
            success=False,
            error="Invalid team memory response format",
            skip_retry=True,
            error_type="parse",
        )
    content = data.get("content")
    if not isinstance(content, dict):
        return TeamMemorySyncFetchResult(
            success=False,
            error="Invalid team memory response format",
            skip_retry=True,
            error_type="parse",
        )
    cs = data.get("checksum")
    if isinstance(cs, str):
        state.last_known_checksum = cs
    return TeamMemorySyncFetchResult(
        success=True,
        data=data,
        checksum=state.last_known_checksum,
    )


async def pull_team_memory(state: SyncState, repo_slug: str) -> TeamMemorySyncFetchResult:
    result = await fetch_team_memory_once(state, repo_slug, state.last_known_checksum)
    log_for_debugging(f"team_memory pull success={result.success}")
    return result


async def push_team_memory(
    state: SyncState,
    repo_slug: str,
    body: dict[str, Any],
) -> TeamMemorySyncPushResult:
    auth = _oauth_headers()
    if not auth:
        return TeamMemorySyncPushResult(
            success=False,
            error="no oauth",
            error_type="no_oauth",
        )
    headers = {**auth, "Content-Type": "application/json"}
    if state.last_known_checksum:
        headers["If-Match"] = f'"{state.last_known_checksum}"'
    url = team_memory_endpoint(repo_slug)
    try:
        async with httpx.AsyncClient() as client:
            r = await client.put(url, headers=headers, json=body, timeout=TEAM_MEMORY_TIMEOUT_S)
    except Exception as err:
        return TeamMemorySyncPushResult(success=False, error=str(err))
    if r.status_code == 412:
        return TeamMemorySyncPushResult(
            success=False,
            conflict=True,
            http_status=412,
            error_type="conflict",
        )
    if r.status_code == 200:
        return TeamMemorySyncPushResult(success=True, files_uploaded=1, http_status=200)
    return TeamMemorySyncPushResult(
        success=False,
        http_status=r.status_code,
        error=r.text[:500],
    )


def is_team_memory_sync_available() -> bool:
    return _oauth_headers() is not None
