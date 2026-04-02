"""
Upload/download user settings and memory files (OAuth).

Migrated from: services/settingsSync/index.ts (feature flags omitted; core HTTP parity).
"""

from __future__ import annotations

import asyncio
import os
import random

import httpx

from ...constants.oauth import CLAUDE_AI_INFERENCE_SCOPE, OAUTH_BETA_HEADER, get_oauth_config
from ...utils.debug import log_for_debugging
from .types import (
    SettingsSyncFetchResult,
    SettingsSyncUploadResult,
    parse_user_sync_data,
)

SETTINGS_SYNC_TIMEOUT_S = 10.0
DEFAULT_MAX_RETRIES = 3
MAX_FILE_SIZE_BYTES = 500 * 1024

_download_task: asyncio.Task[bool] | None = None


def _retry_delay_ms(attempt: int, max_delay_ms: int = 32000) -> float:
    base = min(500 * (2 ** (attempt - 1)), max_delay_ms)
    return base + random.random() * 0.25 * base


def _endpoint() -> str:
    return f"{get_oauth_config().BASE_API_URL}/api/claude_code/user_settings"


def is_using_oauth() -> bool:
    try:
        from ...utils.model.providers import get_api_provider, is_first_party
    except ImportError:
        return False
    if get_api_provider() != "firstParty" or not is_first_party():
        return False
    base = os.getenv("ANTHROPIC_API_URL", "").strip()
    if base and base.rstrip("/") != "https://api.anthropic.com":
        return False
    try:
        from ..oauth.client import get_claude_ai_oauth_tokens
    except ImportError:
        return False
    tokens = get_claude_ai_oauth_tokens()
    if not tokens or not tokens.access_token:
        return False
    scopes = getattr(tokens, "scopes", None) or []
    return CLAUDE_AI_INFERENCE_SCOPE in scopes


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
    }


async def fetch_user_settings_once() -> SettingsSyncFetchResult:
    try:
        from ..oauth.client import check_and_refresh_oauth_token_if_needed

        await check_and_refresh_oauth_token_if_needed()
    except ImportError:
        pass
    auth = _oauth_headers()
    if not auth:
        return SettingsSyncFetchResult(
            success=False,
            error="No OAuth token available",
            skip_retry=True,
        )
    headers = {**auth, "User-Agent": "claude-code-python"}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(_endpoint(), headers=headers, timeout=SETTINGS_SYNC_TIMEOUT_S)
    except httpx.TimeoutException:
        return SettingsSyncFetchResult(success=False, error="Settings sync request timeout")
    except httpx.RequestError:
        return SettingsSyncFetchResult(success=False, error="Cannot connect to server")
    if r.status_code == 404:
        return SettingsSyncFetchResult(success=True, is_empty=True)
    if r.status_code == 401:
        return SettingsSyncFetchResult(
            success=False,
            error="Not authorized for settings sync",
            skip_retry=True,
        )
    if r.status_code != 200:
        return SettingsSyncFetchResult(success=False, error=r.text[:500])
    data = parse_user_sync_data(r.json())
    if data is None:
        return SettingsSyncFetchResult(success=False, error="Invalid settings sync response format")
    return SettingsSyncFetchResult(success=True, data=data, is_empty=False)


async def fetch_user_settings(max_retries: int = DEFAULT_MAX_RETRIES) -> SettingsSyncFetchResult:
    last: SettingsSyncFetchResult | None = None
    for attempt in range(1, max_retries + 2):
        last = await fetch_user_settings_once()
        if last.success:
            return last
        if last.skip_retry:
            return last
        if attempt > max_retries:
            return last
        await asyncio.sleep(_retry_delay_ms(attempt) / 1000.0)
    assert last is not None
    return last


async def upload_user_settings(entries: dict[str, str]) -> SettingsSyncUploadResult:
    try:
        from ..oauth.client import check_and_refresh_oauth_token_if_needed

        await check_and_refresh_oauth_token_if_needed()
    except ImportError:
        pass
    auth = _oauth_headers()
    if not auth:
        return SettingsSyncUploadResult(success=False, error="No OAuth token available")
    headers = {
        **auth,
        "User-Agent": "claude-code-python",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.put(
                _endpoint(),
                json={"entries": entries},
                headers=headers,
                timeout=SETTINGS_SYNC_TIMEOUT_S,
            )
        payload = r.json() if r.content else {}
        cs = payload.get("checksum") if isinstance(payload, dict) else None
        lm = payload.get("lastModified") if isinstance(payload, dict) else None
        return SettingsSyncUploadResult(
            success=r.status_code == 200,
            checksum=str(cs) if cs is not None else None,
            last_modified=str(lm) if lm is not None else None,
            error=None if r.status_code == 200 else r.text[:500],
        )
    except Exception as err:
        return SettingsSyncUploadResult(success=False, error=str(err))


def reset_download_promise_for_testing() -> None:
    global _download_task
    _download_task = None


async def download_user_settings() -> bool:
    """Single-flight download for headless/startup (parity with TS downloadPromise)."""
    global _download_task
    if _download_task is None or _download_task.done():
        _download_task = asyncio.create_task(_do_download_user_settings())
    return await _download_task


async def redownload_user_settings() -> bool:
    global _download_task
    _download_task = asyncio.create_task(_do_download_user_settings(0))
    return await _download_task


async def _do_download_user_settings(max_retries: int = DEFAULT_MAX_RETRIES) -> bool:
    if not is_using_oauth():
        return False
    result = await fetch_user_settings(max_retries)
    if not result.success or result.is_empty or result.data is None:
        return False
    entries = result.data.content.get("entries", {})
    if not isinstance(entries, dict):
        return False
    await apply_remote_entries_to_local({str(k): str(v) for k, v in entries.items()}, None)
    return True


async def apply_remote_entries_to_local(
    entries: dict[str, str],
    project_id: str | None,
) -> None:
    """Write remote key/value entries to local settings/memory paths when resolvable."""
    from ...memdir.paths import get_memory_dir
    from ...utils.config_utils import get_claude_config_dir
    from .types import (
        SYNC_KEYS_USER_MEMORY,
        SYNC_KEYS_USER_SETTINGS,
        project_memory_key,
        project_settings_key,
    )

    cfg_dir = get_claude_config_dir()
    user_settings_path = os.path.join(cfg_dir, "settings.json")
    user_memory_path = os.path.join(cfg_dir, "CLAUDE.md")

    async def _write(path: str, content: str) -> bool:
        if len(content.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
            return False
        os.makedirs(os.path.dirname(path), exist_ok=True)
        import aiofiles

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        return True

    if SYNC_KEYS_USER_SETTINGS in entries:
        await _write(user_settings_path, entries[SYNC_KEYS_USER_SETTINGS])
    if SYNC_KEYS_USER_MEMORY in entries:
        await _write(user_memory_path, entries[SYNC_KEYS_USER_MEMORY])
    if project_id:
        pk = project_settings_key(project_id)
        mk = project_memory_key(project_id)
        if pk in entries:
            local_settings = os.path.join(os.getcwd(), ".claude", "settings.local.json")
            await _write(local_settings, entries[pk])
        if mk in entries:
            local_mem = os.path.join(get_memory_dir(), "CLAUDE.local.md")
            await _write(local_mem, entries[mk])


async def upload_user_settings_in_background() -> None:
    if not is_using_oauth():
        return
    result = await fetch_user_settings()
    if not result.success or result.data is None:
        return
    remote_entries = {} if result.is_empty else result.data.content.get("entries", {})
    if not isinstance(remote_entries, dict):
        remote_entries = {}
    # Local entries build omitted without full settings path helpers — callers can extend
    log_for_debugging("settings_sync_upload_skipped_no_local_diff_builder")
