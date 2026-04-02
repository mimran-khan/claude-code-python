"""
Authentication helpers (API keys, OAuth gating, TTL helpers).

Migrated from: utils/auth.ts (subset aligned with services layer).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from .debug import log_for_debugging

ApiKeySource = Literal["ANTHROPIC_API_KEY", "apiKeyHelper", "/login managed key", "none"]

AuthTokenSource = Literal[
    "none",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR",
    "CCR_OAUTH_TOKEN_FILE",
    "apiKeyHelper",
    "claude.ai",
]


@dataclass(frozen=True)
class AuthTokenSourceResult:
    source: AuthTokenSource
    has_token: bool


@dataclass(frozen=True)
class AnthropicApiKeyResult:
    key: str | None
    source: ApiKeySource


def _env_truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.lower() in ("1", "true", "yes", "on")


def is_managed_oauth_context() -> bool:
    return _env_truthy(os.environ.get("CLAUDE_CODE_REMOTE")) or (
        os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "claude-desktop"
    )


def is_anthropic_auth_enabled() -> bool:
    if _env_truthy(os.environ.get("CLAUDE_CODE_BARE")):
        return False
    if os.environ.get("ANTHROPIC_UNIX_SOCKET") and os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return True
    is_3p = any(
        _env_truthy(os.environ.get(k))
        for k in (
            "CLAUDE_CODE_USE_BEDROCK",
            "CLAUDE_CODE_USE_VERTEX",
            "CLAUDE_CODE_USE_FOUNDRY",
        )
    )
    has_external_token = bool(
        os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR")
    )
    has_external_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    managed = is_managed_oauth_context()
    should_disable = is_3p or ((has_external_token or has_external_key) and not managed)
    return not should_disable


def get_auth_token_source() -> AuthTokenSourceResult:
    if _env_truthy(os.environ.get("CLAUDE_CODE_BARE")):
        return AuthTokenSourceResult(source="none", has_token=False)
    if os.environ.get("ANTHROPIC_AUTH_TOKEN") and not is_managed_oauth_context():
        return AuthTokenSourceResult(source="ANTHROPIC_AUTH_TOKEN", has_token=True)
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return AuthTokenSourceResult(source="CLAUDE_CODE_OAUTH_TOKEN", has_token=True)
    return AuthTokenSourceResult(source="none", has_token=False)


def get_anthropic_api_key_with_source(
    *,
    skip_retrieving_key_from_api_key_helper: bool = False,
) -> AnthropicApiKeyResult:
    _ = skip_retrieving_key_from_api_key_helper
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return AnthropicApiKeyResult(key=key, source="ANTHROPIC_API_KEY")
    return AnthropicApiKeyResult(key=None, source="none")


def get_anthropic_api_key() -> str | None:
    return get_anthropic_api_key_with_source().key


def has_anthropic_api_key_auth() -> bool:
    r = get_anthropic_api_key_with_source(skip_retrieving_key_from_api_key_helper=True)
    return r.key is not None and r.source != "none"


DEFAULT_API_KEY_HELPER_TTL_MS = 5 * 60 * 1000


def calculate_api_key_helper_ttl() -> int:
    raw = os.environ.get("CLAUDE_CODE_API_KEY_HELPER_TTL_MS")
    if raw:
        try:
            parsed = int(raw, 10)
            if parsed >= 0:
                return parsed
        except ValueError:
            pass
        log_for_debugging(
            f"CLAUDE_CODE_API_KEY_HELPER_TTL_MS invalid: {raw}",
            level="error",
        )
    return DEFAULT_API_KEY_HELPER_TTL_MS


def is_valid_api_key(api_key: str) -> bool:
    import re

    return bool(re.fullmatch(r"[a-zA-Z0-9_-]+", api_key))


def is_using_3p_services() -> bool:
    return bool(
        _env_truthy(os.environ.get("CLAUDE_CODE_USE_BEDROCK"))
        or _env_truthy(os.environ.get("CLAUDE_CODE_USE_VERTEX"))
        or _env_truthy(os.environ.get("CLAUDE_CODE_USE_FOUNDRY"))
    )
