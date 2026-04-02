"""
Authentication context helpers (environment and OAuth-aware).

There is no `services/auth/` in the TypeScript tree; logic lives in `utils/auth.ts`.
This package exposes a small async-friendly surface for the Python port.
"""

from .context import (
    AnthropicApiKeyResult,
    ApiKeySource,
    AuthTokenSource,
    AuthTokenSourceResult,
    calculate_api_key_helper_ttl,
    get_anthropic_api_key,
    get_auth_token_source,
    has_anthropic_api_key_auth,
    is_anthropic_auth_enabled,
    is_managed_oauth_context,
    is_using_3p_services,
    is_valid_api_key,
)

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
