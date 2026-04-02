"""
Policy limits fetch with disk cache, ETag, retries, hourly polling.

Migrated from: services/policyLimits/index.ts (structure parity; auth hooks stubbed).
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

from ...constants.oauth import get_oauth_config
from ...utils.config_utils import get_claude_config_dir
from ...utils.debug import log_for_debugging
from .types import PolicyLimitsFetchResult, PolicyRestriction, parse_policy_limits_payload

CACHE_FILENAME = "policy-limits.json"
FETCH_TIMEOUT_S = 10.0
DEFAULT_MAX_RETRIES = 5
POLL_INTERVAL_S = 60 * 60
LOADING_PROMISE_TIMEOUT_S = 30.0

_session_cache: dict[str, PolicyRestriction] | None = None
_polling_task: asyncio.Task[None] | None = None
_loading_complete: asyncio.Event | None = None
_loading_timer: asyncio.TimerHandle | None = None

ESSENTIAL_TRAFFIC_DENY_ON_MISS = frozenset({"allow_product_feedback"})


def _cache_path() -> str:
    return os.path.join(get_claude_config_dir(), CACHE_FILENAME)


def _endpoint() -> str:
    return f"{get_oauth_config().BASE_API_URL}/api/claude_code/policy_limits"


def _sort_keys_deep(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_sort_keys_deep(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _sort_keys_deep(obj[k]) for k in sorted(obj.keys())}
    return obj


def _compute_checksum(restrictions: dict[str, PolicyRestriction]) -> str:
    serializable = {k: {"allowed": v.allowed} for k, v in restrictions.items()}
    normalized = json.dumps(_sort_keys_deep(serializable), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return f"sha256:{digest}"


def _retry_delay_ms(attempt: int, max_delay_ms: int = 32000) -> float:
    base = min(500 * (2 ** (attempt - 1)), max_delay_ms)
    return base + random.random() * 0.25 * base


def is_policy_limits_eligible() -> bool:
    """Return True if this build should call the policy limits API."""
    try:
        from ...utils.model.providers import get_api_provider, is_first_party
    except ImportError:
        return False
    if get_api_provider() != "firstParty":
        return False
    if not is_first_party():
        return False
    # Custom base URL: skip policy endpoint (parity with TS isFirstPartyAnthropicBaseUrl)
    base = os.getenv("ANTHROPIC_API_URL", "").strip()
    if base and base.rstrip("/") != "https://api.anthropic.com":
        return False
    # API key in env/config (minimal check)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    # OAuth: would need token + team/enterprise — stub False without full auth port
    return False


def reset_policy_limits_for_testing() -> None:
    global _session_cache, _polling_task, _loading_complete, _loading_timer
    stop_background_polling()
    _session_cache = None
    _loading_complete = None
    if _loading_timer:
        _loading_timer.cancel()
        _loading_timer = None


def initialize_policy_limits_loading_promise() -> None:
    global _loading_complete, _loading_timer
    if _loading_complete is not None:
        return
    if not is_policy_limits_eligible():
        return
    loop = asyncio.get_event_loop()
    _loading_complete = asyncio.Event()

    def _fire() -> None:
        if _loading_complete and not _loading_complete.is_set():
            log_for_debugging("Policy limits: Loading promise timed out, resolving anyway")
            _loading_complete.set()

    _loading_timer = loop.call_later(LOADING_PROMISE_TIMEOUT_S, _fire)


async def wait_for_policy_limits_to_load() -> None:
    if _loading_complete:
        await asyncio.wait_for(_loading_complete.wait(), timeout=LOADING_PROMISE_TIMEOUT_S + 1)


def _load_disk_cache() -> dict[str, PolicyRestriction] | None:
    path = _cache_path()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return parse_policy_limits_payload(data)
    except OSError:
        return None
    except json.JSONDecodeError:
        return None


async def _save_disk_cache(restrictions: dict[str, PolicyRestriction]) -> None:
    path = _cache_path()
    payload = {"restrictions": {k: {"allowed": v.allowed} for k, v in restrictions.items()}}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


async def _fetch_once(cached_checksum: str | None) -> PolicyLimitsFetchResult:
    headers: dict[str, str] = {"User-Agent": "claude-code-python"}
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    else:
        return PolicyLimitsFetchResult(
            success=False,
            error="No authentication available",
            skip_retry=True,
        )
    if cached_checksum:
        headers["If-None-Match"] = f'"{cached_checksum}"'
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                _endpoint(),
                headers=headers,
                timeout=FETCH_TIMEOUT_S,
            )
    except httpx.TimeoutException:
        return PolicyLimitsFetchResult(success=False, error="Policy limits request timeout")
    except httpx.RequestError:
        return PolicyLimitsFetchResult(success=False, error="Cannot connect to server")

    if response.status_code == 304:
        log_for_debugging("Policy limits: Using cached restrictions (304)")
        return PolicyLimitsFetchResult(
            success=True,
            restrictions=None,
            etag=cached_checksum,
        )
    if response.status_code == 404:
        log_for_debugging("Policy limits: No restrictions found (404)")
        return PolicyLimitsFetchResult(success=True, restrictions={})
    if response.status_code == 401:
        return PolicyLimitsFetchResult(
            success=False,
            error="Not authorized for policy limits",
            skip_retry=True,
        )
    if response.status_code != 200:
        return PolicyLimitsFetchResult(success=False, error=response.text[:500])

    parsed = parse_policy_limits_payload(response.json())
    if parsed is None:
        return PolicyLimitsFetchResult(success=False, error="Invalid policy limits format")
    log_for_debugging("Policy limits: Fetched successfully")
    return PolicyLimitsFetchResult(success=True, restrictions=parsed)


async def _fetch_with_retry(cached_checksum: str | None) -> PolicyLimitsFetchResult:
    last: PolicyLimitsFetchResult | None = None
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


async def _fetch_and_apply() -> dict[str, PolicyRestriction] | None:
    global _session_cache
    if not is_policy_limits_eligible():
        return None
    cached = _load_disk_cache()
    checksum = _compute_checksum(cached) if cached else None
    try:
        result = await _fetch_with_retry(checksum)
        if not result.success:
            if cached:
                log_for_debugging("Policy limits: Using stale cache after fetch failure")
                _session_cache = cached
                return cached
            return None
        if result.restrictions is None and cached:
            log_for_debugging("Policy limits: Cache still valid (304 Not Modified)")
            _session_cache = cached
            return cached
        new_r = result.restrictions or {}
        if new_r:
            _session_cache = new_r
            await _save_disk_cache(new_r)
            return new_r
        _session_cache = {}
        with contextlib.suppress(OSError):
            os.unlink(_cache_path())
        return new_r
    except Exception:
        if cached:
            _session_cache = cached
            return cached
        return None


def _restrictions_from_cache() -> dict[str, PolicyRestriction] | None:
    global _session_cache
    if not is_policy_limits_eligible():
        return None
    if _session_cache:
        return _session_cache
    cached = _load_disk_cache()
    if cached:
        _session_cache = cached
    return _session_cache


def is_policy_allowed(policy: str) -> bool:
    restrictions = _restrictions_from_cache()
    if not restrictions:
        try:
            from ...utils.env_utils import is_env_truthy

            essential_only = is_env_truthy(os.environ.get("CLAUDE_CODE_ESSENTIAL_TRAFFIC_ONLY"))
        except ImportError:
            essential_only = False
        return not (essential_only and policy in ESSENTIAL_TRAFFIC_DENY_ON_MISS)
    rule = restrictions.get(policy)
    if rule is None:
        return True
    return rule.allowed


async def load_policy_limits() -> None:
    global _loading_complete
    initialize_policy_limits_loading_promise()
    if is_policy_limits_eligible() and _loading_complete and not _loading_complete.is_set():
        pass
    try:
        await _fetch_and_apply()
        if is_policy_limits_eligible():
            start_background_polling()
    finally:
        if _loading_complete and not _loading_complete.is_set():
            _loading_complete.set()


async def refresh_policy_limits() -> None:
    await clear_policy_limits_cache()
    if not is_policy_limits_eligible():
        return
    await _fetch_and_apply()
    log_for_debugging("Policy limits: Refreshed after auth change")


async def clear_policy_limits_cache() -> None:
    global _session_cache, _loading_complete, _loading_timer
    stop_background_polling()
    _session_cache = None
    _loading_complete = None
    if _loading_timer:
        _loading_timer.cancel()
        _loading_timer = None
    with contextlib.suppress(OSError):
        os.unlink(_cache_path())


async def _poll_loop() -> None:
    while True:
        await asyncio.sleep(POLL_INTERVAL_S)
        if not is_policy_limits_eligible():
            continue
        prev = json.dumps(
            {k: v.allowed for k, v in (_session_cache or {}).items()},
            sort_keys=True,
        )
        await _fetch_and_apply()
        new = json.dumps(
            {k: v.allowed for k, v in (_session_cache or {}).items()},
            sort_keys=True,
        )
        if new != prev:
            log_for_debugging("Policy limits: Changed during background poll")


def start_background_polling() -> None:
    global _polling_task
    if _polling_task and not _polling_task.done():
        return
    if not is_policy_limits_eligible():
        return
    loop = asyncio.get_event_loop()
    _polling_task = loop.create_task(_poll_loop())


def stop_background_polling() -> None:
    global _polling_task
    if _polling_task and not _polling_task.done():
        _polling_task.cancel()
    _polling_task = None
