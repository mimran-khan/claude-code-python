"""
Fast mode (org-gated) availability and runtime cooldown state.

Migrated from: utils/fastMode.ts (trimmed).
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import httpx

from claude_code.services.analytics.growthbook import get_feature_value_cached

from .debug import log_for_debugging
from .env_utils import is_env_truthy
from .model.providers import get_api_provider

FAST_MODE_MODEL_DISPLAY = "Opus 4.6"
CooldownReason = Literal["rate_limit", "overloaded"]
FastModeDisabledReason = Literal[
    "free",
    "preference",
    "extra_usage_disabled",
    "network_error",
    "unknown",
]


@dataclass
class FastModeRuntimeState:
    status: Literal["active", "cooldown"] = "active"
    reset_at: float = 0.0
    reason: CooldownReason | None = None


@dataclass
class FastModeOrgStatus:
    kind: Literal["pending", "enabled", "disabled"] = "pending"
    reason: FastModeDisabledReason | None = None


_org_status = FastModeOrgStatus()
_runtime = FastModeRuntimeState()
_has_logged_cooldown_expiry = False
_last_prefetch_at = 0.0
_cooldown_handlers: list[Callable[[float, CooldownReason], None]] = []
_expiry_handlers: list[Callable[[], None]] = []
_org_handlers: list[Callable[[bool], None]] = []


def is_fast_mode_enabled() -> bool:
    return not is_env_truthy(os.getenv("CLAUDE_CODE_DISABLE_FAST_MODE"))


def _disabled_message(reason: FastModeDisabledReason) -> str:
    if reason == "free":
        return "Fast mode requires a paid subscription"
    if reason == "preference":
        return "Fast mode has been disabled by your organization"
    if reason == "extra_usage_disabled":
        return "Fast mode requires extra usage billing"
    if reason == "network_error":
        return "Fast mode unavailable due to network connectivity issues"
    return "Fast mode is currently unavailable"


def get_fast_mode_unavailable_reason() -> str | None:
    if not is_fast_mode_enabled():
        return "Fast mode is not available"
    statig = get_feature_value_cached("tengu_penguins_off", None)
    if statig is not None:
        log_for_debugging(f"Fast mode unavailable: {statig}")
        return str(statig)
    if get_api_provider() != "firstParty":
        r = "Fast mode is not available on Bedrock, Vertex, or Foundry"
        log_for_debugging(f"Fast mode unavailable: {r}")
        return r
    if _org_status.kind == "disabled":
        if _org_status.reason in ("network_error", "unknown") and is_env_truthy(
            os.getenv("CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS")
        ):
            return None
        return _disabled_message(_org_status.reason or "unknown")
    return None


def is_fast_mode_available() -> bool:
    if not is_fast_mode_enabled():
        return False
    return get_fast_mode_unavailable_reason() is None


def get_fast_mode_model() -> str:
    return "opus"


def get_fast_mode_runtime_state() -> FastModeRuntimeState:
    global _runtime, _has_logged_cooldown_expiry
    if _runtime.status == "cooldown" and time.time() >= _runtime.reset_at:
        if is_fast_mode_enabled() and not _has_logged_cooldown_expiry:
            log_for_debugging("Fast mode cooldown expired, re-enabling fast mode")
            _has_logged_cooldown_expiry = True
            for h in _expiry_handlers:
                h()
        _runtime = FastModeRuntimeState()
    return _runtime


def trigger_fast_mode_cooldown(reset_timestamp: float, reason: CooldownReason) -> None:
    global _runtime, _has_logged_cooldown_expiry
    if not is_fast_mode_enabled():
        return
    _runtime = FastModeRuntimeState(status="cooldown", reset_at=reset_timestamp, reason=reason)
    _has_logged_cooldown_expiry = False
    for h in _cooldown_handlers:
        h(reset_timestamp, reason)


def clear_fast_mode_cooldown() -> None:
    global _runtime
    _runtime = FastModeRuntimeState()


def is_fast_mode_cooldown() -> bool:
    return get_fast_mode_runtime_state().status == "cooldown"


def on_cooldown_triggered(cb: Callable[[float, CooldownReason], None]) -> None:
    _cooldown_handlers.append(cb)


def on_cooldown_expired(cb: Callable[[], None]) -> None:
    _expiry_handlers.append(cb)


def on_org_fast_mode_changed(cb: Callable[[bool], None]) -> None:
    _org_handlers.append(cb)


async def prefetch_fast_mode_status() -> None:
    global _org_status, _last_prefetch_at
    if not is_fast_mode_enabled():
        return
    now = time.time() * 1000
    if now - _last_prefetch_at < 30_000:
        return
    _last_prefetch_at = now
    base = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    url = f"{base}/api/claude_code_penguin_mode"
    token = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
    if not token:
        _org_status = FastModeOrgStatus(kind="disabled", reason="preference")
        return
    headers = {"x-api-key": token} if token.startswith("sk-") else {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(f"status {r.status_code}")
        data = r.json()
        enabled = bool(data.get("enabled"))
        reason = data.get("disabled_reason")
        _org_status = (
            FastModeOrgStatus(kind="enabled")
            if enabled
            else FastModeOrgStatus(kind="disabled", reason=(reason or "preference"))
        )
        for h in _org_handlers:
            h(enabled)
    except Exception as exc:
        log_for_debugging(f"fast mode prefetch failed: {exc}", level="error")
        is_ant = os.getenv("USER_TYPE") == "ant"
        _org_status = (
            FastModeOrgStatus(kind="enabled") if is_ant else FastModeOrgStatus(kind="disabled", reason="network_error")
        )
