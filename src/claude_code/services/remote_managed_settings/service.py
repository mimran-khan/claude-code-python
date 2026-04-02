"""
Fetch and cache remotely managed settings (enterprise).

Migrated from: services/remoteManagedSettings/index.ts (reduced; security UI stubbed).
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import random
from typing import Any

import httpx

from ...constants.oauth import OAUTH_BETA_HEADER, get_oauth_config
from ...utils.debug import log_for_debugging
from .sync_cache import is_remote_managed_settings_eligible
from .sync_cache import reset_sync_cache as reset_eligibility_cache
from .sync_cache_state import (
    get_remote_managed_settings_sync_from_cache,
    get_settings_path,
    reset_sync_cache,
    set_session_cache,
)
from .types import RemoteManagedSettingsFetchResult, parse_remote_settings_response

SETTINGS_TIMEOUT_S = 10.0
DEFAULT_MAX_RETRIES = 5
POLL_INTERVAL_S = 60 * 60

_loading_event: asyncio.Event | None = None
_poll_task: asyncio.Task[None] | None = None


def _retry_delay_ms(attempt: int, max_delay_ms: int = 32000) -> float:
    base = min(500 * (2 ** (attempt - 1)), max_delay_ms)
    return base + random.random() * 0.25 * base


def _endpoint() -> str:
    return f"{get_oauth_config().BASE_API_URL}/api/claude_code/settings"


def compute_checksum_from_settings(settings: dict[str, Any]) -> str:
    normalized = json.dumps(settings, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(normalized.encode()).hexdigest()


def is_eligible_for_remote_managed_settings() -> bool:
    return is_remote_managed_settings_eligible()


def initialize_remote_managed_settings_loading_promise() -> None:
    global _loading_event
    if _loading_event is not None:
        return
    if not is_remote_managed_settings_eligible():
        return
    _loading_event = asyncio.Event()

    def _timeout() -> None:
        if _loading_event and not _loading_event.is_set():
            log_for_debugging("Remote settings: Loading promise timed out, resolving anyway")
            _loading_event.set()

    try:
        loop = asyncio.get_event_loop()
        loop.call_later(30.0, _timeout)
    except RuntimeError:
        pass


async def wait_for_remote_managed_settings_to_load() -> None:
    if _loading_event:
        await _loading_event.wait()


def _auth_headers() -> dict[str, str] | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return {"x-api-key": key}
    try:
        from ..oauth.client import get_claude_ai_oauth_tokens
    except ImportError:
        return None
    tokens = get_claude_ai_oauth_tokens()
    if tokens and tokens.access_token:
        return {
            "Authorization": f"Bearer {tokens.access_token}",
            "anthropic-beta": OAUTH_BETA_HEADER,
        }
    return None


async def _fetch_once(cached_checksum: str | None) -> RemoteManagedSettingsFetchResult:
    auth = _auth_headers()
    if not auth:
        return RemoteManagedSettingsFetchResult(
            success=False,
            error="No authentication available",
            skip_retry=True,
        )
    headers = {**auth, "User-Agent": "claude-code-python"}
    if cached_checksum:
        headers["If-None-Match"] = f'"{cached_checksum}"'
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(_endpoint(), headers=headers, timeout=SETTINGS_TIMEOUT_S)
    except httpx.TimeoutException:
        return RemoteManagedSettingsFetchResult(success=False, error="Remote settings request timeout")
    except httpx.RequestError:
        return RemoteManagedSettingsFetchResult(success=False, error="Cannot connect to server")

    if r.status_code == 304:
        log_for_debugging("Remote settings: Using cached settings (304)")
        return RemoteManagedSettingsFetchResult(
            success=True,
            settings=None,
            checksum=cached_checksum,
        )
    if r.status_code in (204, 404):
        log_for_debugging(f"Remote settings: No settings found ({r.status_code})")
        return RemoteManagedSettingsFetchResult(success=True, settings={}, checksum=None)
    if r.status_code == 401:
        return RemoteManagedSettingsFetchResult(
            success=False,
            error="Not authorized for remote settings",
            skip_retry=True,
        )
    if r.status_code != 200:
        return RemoteManagedSettingsFetchResult(success=False, error=r.text[:500])
    parsed = parse_remote_settings_response(r.json())
    if parsed is None:
        return RemoteManagedSettingsFetchResult(success=False, error="Invalid remote settings format")
    settings, checksum = parsed
    log_for_debugging("Remote settings: Fetched successfully")
    return RemoteManagedSettingsFetchResult(success=True, settings=settings, checksum=checksum)


async def _fetch_with_retry(cached_checksum: str | None) -> RemoteManagedSettingsFetchResult:
    last: RemoteManagedSettingsFetchResult | None = None
    for attempt in range(1, DEFAULT_MAX_RETRIES + 2):
        last = await _fetch_once(cached_checksum)
        if last.success:
            return last
        if last.skip_retry:
            return last
        if attempt > DEFAULT_MAX_RETRIES:
            return last
        await asyncio.sleep(_retry_delay_ms(attempt) / 1000.0)
    assert last is not None
    return last


async def _save_settings(settings: dict[str, Any]) -> None:
    path = get_settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    log_for_debugging(f"Remote settings: Saved to {path}")


async def fetch_and_load_remote_managed_settings() -> dict[str, Any] | None:
    if not is_remote_managed_settings_eligible():
        return None
    cached = get_remote_managed_settings_sync_from_cache()
    checksum = compute_checksum_from_settings(cached) if cached else None
    try:
        result = await _fetch_with_retry(checksum)
        if not result.success:
            if cached:
                log_for_debugging("Remote settings: Using stale cache after fetch failure")
                set_session_cache(cached)
                return cached
            return None
        if result.settings is None and cached:
            log_for_debugging("Remote settings: Cache still valid (304 Not Modified)")
            set_session_cache(cached)
            return cached
        new_settings = result.settings or {}
        if new_settings:
            set_session_cache(new_settings)
            await _save_settings(new_settings)
            return new_settings
        set_session_cache({})
        with contextlib.suppress(OSError):
            os.unlink(get_settings_path())
        return {}
    except Exception:
        if cached:
            set_session_cache(cached)
            return cached
        return None


async def clear_remote_managed_settings_cache() -> None:
    global _loading_event, _poll_task
    stop_background_polling()
    reset_sync_cache()
    reset_eligibility_cache()
    _loading_event = None
    with contextlib.suppress(OSError):
        os.unlink(get_settings_path())


async def load_remote_managed_settings() -> None:
    global _loading_event
    initialize_remote_managed_settings_loading_promise()
    if is_remote_managed_settings_eligible() and _loading_event is None:
        _loading_event = asyncio.Event()
    if get_remote_managed_settings_sync_from_cache() and _loading_event and not _loading_event.is_set():
        _loading_event.set()
    try:
        await fetch_and_load_remote_managed_settings()
        if is_remote_managed_settings_eligible():
            start_background_polling()
    finally:
        if _loading_event and not _loading_event.is_set():
            _loading_event.set()


async def refresh_remote_managed_settings() -> None:
    await clear_remote_managed_settings_cache()
    if not is_remote_managed_settings_eligible():
        return
    await fetch_and_load_remote_managed_settings()
    log_for_debugging("Remote settings: Refreshed after auth change")


async def _poll() -> None:
    while True:
        await asyncio.sleep(POLL_INTERVAL_S)
        if not is_remote_managed_settings_eligible():
            continue
        prev = json.dumps(get_remote_managed_settings_sync_from_cache() or {}, sort_keys=True)
        await fetch_and_load_remote_managed_settings()
        new = json.dumps(get_remote_managed_settings_sync_from_cache() or {}, sort_keys=True)
        if new != prev:
            log_for_debugging("Remote settings: Changed during background poll")


def start_background_polling() -> None:
    global _poll_task
    if _poll_task and not _poll_task.done():
        return
    if not is_remote_managed_settings_eligible():
        return
    loop = asyncio.get_event_loop()
    _poll_task = loop.create_task(_poll())


def stop_background_polling() -> None:
    global _poll_task
    if _poll_task and not _poll_task.done():
        _poll_task.cancel()
    _poll_task = None
