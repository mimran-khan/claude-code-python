"""
OAuth Services.

OAuth 2.0 PKCE, token exchange, profile fetch, and OAuthService orchestration.

Migrated from: services/oauth/*.ts
"""

from .auth_code_listener import AuthCodeListener
from .client import (
    build_auth_url,
    check_and_refresh_oauth_token_if_needed,
    clear_claude_ai_oauth_tokens,
    create_and_store_api_key,
    exchange_code_for_tokens,
    fetch_and_store_user_roles,
    fetch_profile_info,
    get_claude_ai_oauth_tokens,
    get_organization_uuid,
    is_oauth_token_expired,
    parse_scopes,
    populate_oauth_account_info_if_needed,
    refresh_oauth_token,
    save_claude_ai_oauth_tokens,
    should_use_claude_ai_auth,
    store_oauth_account_info,
)
from .crypto import (
    base64_url_encode,
    generate_code_challenge,
    generate_code_verifier,
    generate_state,
)
from .get_oauth_profile import (
    get_oauth_profile_from_api_key,
    get_oauth_profile_from_oauth_token,
)
from .oauth_service import OAuthService
from .types import (
    OAuthProfileResponse,
    OAuthTokenAccount,
    OAuthTokenExchangeResponse,
    OAuthTokens,
    ProfileInfo,
)

__all__ = [
    "generate_code_verifier",
    "generate_code_challenge",
    "generate_state",
    "base64_url_encode",
    "OAuthProfileResponse",
    "OAuthTokens",
    "OAuthTokenExchangeResponse",
    "OAuthTokenAccount",
    "ProfileInfo",
    "get_oauth_profile_from_api_key",
    "get_oauth_profile_from_oauth_token",
    "should_use_claude_ai_auth",
    "parse_scopes",
    "build_auth_url",
    "exchange_code_for_tokens",
    "refresh_oauth_token",
    "fetch_and_store_user_roles",
    "create_and_store_api_key",
    "is_oauth_token_expired",
    "fetch_profile_info",
    "get_organization_uuid",
    "populate_oauth_account_info_if_needed",
    "store_oauth_account_info",
    "get_claude_ai_oauth_tokens",
    "save_claude_ai_oauth_tokens",
    "clear_claude_ai_oauth_tokens",
    "check_and_refresh_oauth_token_if_needed",
    "OAuthService",
    "AuthCodeListener",
]
