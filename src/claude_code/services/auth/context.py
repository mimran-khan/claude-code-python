"""Re-export auth helpers from utils.auth (TS: utils/auth.ts)."""

from __future__ import annotations

from ...utils.auth import (
    AnthropicApiKeyResult,
    ApiKeySource,
    AuthTokenSource,
    AuthTokenSourceResult,
    calculate_api_key_helper_ttl,
    get_auth_token_source,
    has_anthropic_api_key_auth,
    is_anthropic_auth_enabled,
    is_managed_oauth_context,
    is_using_3p_services,
    is_valid_api_key,
)
from ...utils.auth import (
    get_anthropic_api_key_with_source as _get_key_with_source,
)


def get_anthropic_api_key() -> tuple[str | None, ApiKeySource]:
    r = _get_key_with_source()
    return (r.key, r.source)


__all__ = [
    "AnthropicApiKeyResult",
    "ApiKeySource",
    "AuthTokenSource",
    "AuthTokenSourceResult",
    "calculate_api_key_helper_ttl",
    "get_anthropic_api_key",
    "get_auth_token_source",
    "has_anthropic_api_key_auth",
    "is_anthropic_auth_enabled",
    "is_managed_oauth_context",
    "is_using_3p_services",
    "is_valid_api_key",
]
