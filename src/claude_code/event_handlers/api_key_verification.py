"""
Anthropic API key probe for interactive sessions.

Migrated from: hooks/useApiKeyVerification.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal

VerificationStatus = Literal["loading", "valid", "invalid", "missing", "error"]


@dataclass
class ApiKeyVerificationState:
    status: VerificationStatus = "loading"
    error: Exception | None = None


@dataclass
class ApiKeyVerificationDeps:
    """Inject environment-specific auth (mirrors TS bootstrap + auth utils)."""

    is_anthropic_auth_enabled: Callable[[], bool] = lambda: True
    is_claude_ai_subscriber: Callable[[], bool] = lambda: False
    get_key_and_source: Callable[
        [],
        tuple[str | None, str | None],
    ] = lambda: (None, None)
    warm_api_key_helper: Callable[[bool], Awaitable[None]] | None = None
    verify_api_key: Callable[[str, bool], Awaitable[bool]] | None = None


async def initial_verification_status(deps: ApiKeyVerificationDeps) -> VerificationStatus:
    if not deps.is_anthropic_auth_enabled() or deps.is_claude_ai_subscriber():
        return "valid"
    key, source = deps.get_key_and_source()
    if key or source == "apiKeyHelper":
        return "loading"
    return "missing"


async def verify_api_key_now(
    state: ApiKeyVerificationState,
    deps: ApiKeyVerificationDeps,
    *,
    non_interactive: bool = False,
) -> None:
    if not deps.is_anthropic_auth_enabled() or deps.is_claude_ai_subscriber():
        state.status = "valid"
        state.error = None
        return
    if deps.warm_api_key_helper is not None:
        await deps.warm_api_key_helper(non_interactive)
    key, source = deps.get_key_and_source()
    if not key:
        if source == "apiKeyHelper":
            state.status = "error"
            state.error = RuntimeError("API key helper did not return a valid key")
            return
        state.status = "missing"
        state.error = None
        return
    if deps.verify_api_key is None:
        state.status = "error"
        state.error = RuntimeError("verify_api_key not configured")
        return
    try:
        is_valid = await deps.verify_api_key(key, False)
        state.status = "valid" if is_valid else "invalid"
        state.error = None
    except Exception as exc:  # noqa: BLE001 — parity with TS catch
        state.error = exc
        state.status = "error"
