"""
Fetch OAuth profile via API key or bearer token.

Migrated from: services/oauth/getOauthProfile.ts
"""

from __future__ import annotations

import httpx

from ...constants.oauth import OAUTH_BETA_HEADER, get_oauth_config
from ...utils.log import log_error
from .types import OAuthProfileResponse


async def get_oauth_profile_from_api_key(
    account_uuid: str | None,
    api_key: str | None,
    *,
    timeout_s: float = 10.0,
) -> OAuthProfileResponse | None:
    """GET /api/claude_cli_profile with x-api-key."""
    if not account_uuid or not api_key:
        return None
    endpoint = f"{get_oauth_config().BASE_API_URL}/api/claude_cli_profile"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                endpoint,
                headers={
                    "x-api-key": api_key,
                    "anthropic-beta": OAUTH_BETA_HEADER,
                },
                params={"account_uuid": account_uuid},
                timeout=timeout_s,
            )
            response.raise_for_status()
            data = response.json()
            return OAuthProfileResponse.from_dict(data if isinstance(data, dict) else None)
    except Exception as exc:
        log_error(exc if isinstance(exc, BaseException) else RuntimeError(str(exc)))
        return None


async def get_oauth_profile_from_oauth_token(
    access_token: str,
    *,
    timeout_s: float = 10.0,
) -> OAuthProfileResponse | None:
    """GET /api/oauth/profile with Bearer token."""
    endpoint = f"{get_oauth_config().BASE_API_URL}/api/oauth/profile"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                endpoint,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=timeout_s,
            )
            response.raise_for_status()
            data = response.json()
            return OAuthProfileResponse.from_dict(data if isinstance(data, dict) else None)
    except Exception as exc:
        log_error(exc if isinstance(exc, BaseException) else RuntimeError(str(exc)))
        return None
