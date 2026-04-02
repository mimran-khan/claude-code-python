"""
Session ingress: append and fetch remote transcript logs.

Migrated from: services/api/sessionIngress.ts
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from typing import Any

import httpx
import structlog

from ...constants.oauth import get_oauth_config
from ...utils.http import get_user_agent

logger = structlog.get_logger(__name__)

MAX_RETRIES = 10
BASE_DELAY_MS = 500
_MAX_PAGES = 100

_last_uuid_map: dict[str, str] = {}
_sequential_locks: dict[str, asyncio.Lock] = {}


def _session_lock(session_id: str) -> asyncio.Lock:
    if session_id not in _sequential_locks:
        _sequential_locks[session_id] = asyncio.Lock()
    return _sequential_locks[session_id]


async def _sleep_backoff(attempt: int) -> None:
    delay_ms = min(BASE_DELAY_MS * (2 ** (attempt - 1)), 8000)
    await asyncio.sleep(delay_ms / 1000.0)


async def fetch_session_logs_from_url(
    session_id: str,
    url: str,
    headers: dict[str, str],
) -> list[dict[str, Any]] | None:
    params: dict[str, str] | None = None
    if os.environ.get("CLAUDE_AFTER_LAST_COMPACT", "").lower() in ("1", "true", "yes"):
        params = {"after_last_compact": "true"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, headers=headers, params=params)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and isinstance(data.get("loglines"), list):
                return [x for x in data["loglines"] if isinstance(x, dict)]
            return None
        if r.status_code == 404:
            return []
        if r.status_code == 401:
            raise RuntimeError("Your session has expired. Please run /login to sign in again.")
    except RuntimeError:
        raise
    except Exception as exc:
        logger.warning("session_get_failed", error=str(exc))
    return None


def _find_last_uuid(logs: list[dict[str, Any]] | None) -> str | None:
    if not logs:
        return None
    for e in reversed(logs):
        u = e.get("uuid")
        if isinstance(u, str):
            return u
    return None


async def _append_session_log_impl(
    session_id: str,
    entry: dict[str, Any],
    url: str,
    headers: dict[str, str],
) -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            last_uuid = _last_uuid_map.get(session_id)
            req_headers = {**headers}
            if last_uuid:
                req_headers["Last-Uuid"] = last_uuid
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.put(url, json=entry, headers=req_headers)
            status = r.status_code
            if status in (200, 201):
                eu = entry.get("uuid")
                if isinstance(eu, str):
                    _last_uuid_map[session_id] = eu
                logger.debug("session_log_persisted", session_id=session_id)
                return True
            if status == 409:
                server_last = r.headers.get("x-last-uuid")
                eu = entry.get("uuid")
                if server_last and eu and server_last == eu:
                    _last_uuid_map[session_id] = eu
                    return True
                if server_last:
                    _last_uuid_map[session_id] = server_last
                    continue
                logs = await fetch_session_logs_from_url(session_id, url, headers)
                adopted = _find_last_uuid(logs)
                if adopted:
                    _last_uuid_map[session_id] = adopted
                    continue
                logger.error("session_persist_conflict", session_id=session_id)
                return False
            if status == 401:
                return False
            logger.warning("session_persist_status", status=status, attempt=attempt)
        except Exception as exc:
            logger.warning("session_persist_error", error=str(exc), attempt=attempt)
        if attempt == MAX_RETRIES:
            return False
        await _sleep_backoff(attempt)
    return False


async def append_session_log(
    session_id: str,
    entry: dict[str, Any],
    url: str,
    *,
    get_session_token: Callable[[], str | None],
) -> bool:
    token = get_session_token()
    if not token:
        return False
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": get_user_agent(),
    }
    lock = _session_lock(session_id)
    async with lock:
        return await _append_session_log_impl(session_id, entry, url, headers)


async def get_session_logs(
    session_id: str,
    url: str,
    *,
    get_session_token: Callable[[], str | None],
) -> list[dict[str, Any]] | None:
    token = get_session_token()
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}", "User-Agent": get_user_agent()}
    logs = await fetch_session_logs_from_url(session_id, url, headers)
    if logs:
        last = _find_last_uuid(logs)
        if last:
            _last_uuid_map[session_id] = last
    return logs


def _oauth_org_headers(access_token: str, org_uuid: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "x-organization-uuid": org_uuid,
        "User-Agent": get_user_agent(),
    }


async def get_session_logs_via_oauth(
    session_id: str,
    access_token: str,
    org_uuid: str,
) -> list[dict[str, Any]] | None:
    base = get_oauth_config().BASE_API_URL
    url = f"{base}/v1/session_ingress/session/{session_id}"
    headers = _oauth_org_headers(access_token, org_uuid)
    return await fetch_session_logs_from_url(session_id, url, headers)


async def get_teleport_events(
    session_id: str,
    access_token: str,
    org_uuid: str,
) -> list[dict[str, Any]] | None:
    base = get_oauth_config().BASE_API_URL
    base_url = f"{base}/v1/code/sessions/{session_id}/teleport-events"
    headers = _oauth_org_headers(access_token, org_uuid)
    all_entries: list[dict[str, Any]] = []
    cursor: str | None = None
    pages = 0
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            while pages < _MAX_PAGES:
                params: dict[str, str | int] = {"limit": 1000}
                if cursor is not None:
                    params["cursor"] = cursor
                r = await client.get(base_url, headers=headers, params=params)
                if r.status_code == 404:
                    return None if pages == 0 else all_entries
                if r.status_code == 401:
                    raise RuntimeError("Your session has expired. Please run /login to sign in again.")
                if r.status_code != 200:
                    logger.error("teleport_events_status", status=r.status_code)
                    return None
                payload = r.json()
                if not isinstance(payload, dict):
                    return None
                data = payload.get("data", [])
                if not isinstance(data, list):
                    return None
                for ev in data:
                    if isinstance(ev, dict) and ev.get("payload") is not None:
                        p = ev["payload"]
                        if isinstance(p, dict):
                            all_entries.append(p)
                pages += 1
                nc = payload.get("next_cursor")
                if nc is None:
                    break
                cursor = str(nc)
    except RuntimeError:
        raise
    except Exception as exc:
        logger.warning("teleport_events_failed", error=str(exc))
        return None
    if pages >= _MAX_PAGES:
        logger.warning("teleport_events_page_cap", session_id=session_id)
    return all_entries


def clear_session(session_id: str) -> None:
    _last_uuid_map.pop(session_id, None)
    _sequential_locks.pop(session_id, None)


def clear_all_sessions() -> None:
    _last_uuid_map.clear()
    _sequential_locks.clear()
