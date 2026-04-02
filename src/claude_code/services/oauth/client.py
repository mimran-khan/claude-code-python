"""
OAuth HTTP client: PKCE URLs, token exchange, refresh, profile, roles.

Migrated from: services/oauth/client.ts
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any
from urllib.parse import urlencode

import httpx

from ...constants.oauth import (
    ALL_OAUTH_SCOPES,
    CLAUDE_AI_INFERENCE_SCOPE,
    CLAUDE_AI_OAUTH_SCOPES,
    get_oauth_config,
)
from ...utils.config_utils import get_global_config, save_global_config
from ...utils.secure_storage import delete_credential, get_credential, set_credential
from ..analytics.index import log_event
from .get_oauth_profile import get_oauth_profile_from_oauth_token
from .types import (
    OAuthProfileResponse,
    OAuthTokenAccount,
    OAuthTokenExchangeResponse,
    OAuthTokens,
    ProfileInfo,
    SubscriptionType,
    UserRolesResponse,
)

# Keychain / secure storage identifiers for persisted Claude.ai OAuth tokens
CLAUDE_AI_OAUTH_STORAGE_SERVICE = "com.anthropic.claude-code"
CLAUDE_AI_OAUTH_STORAGE_ACCOUNT = "claude_ai_oauth_tokens"


def _tokens_from_storage_blob(parsed: dict[str, Any]) -> OAuthTokens | None:
    """Rehydrate :class:`OAuthTokens` from a JSON object stored in secure storage."""
    access = parsed.get("access_token")
    refresh = parsed.get("refresh_token")
    exp = parsed.get("expires_at")
    if not isinstance(access, str) or not isinstance(refresh, str):
        return None
    if not isinstance(exp, (int, float)):
        return None
    scopes_raw = parsed.get("scopes")
    scopes: list[str] = [str(s) for s in scopes_raw] if isinstance(scopes_raw, list) else []
    sub: SubscriptionType = None
    raw_sub = parsed.get("subscription_type")
    if raw_sub in ("max", "pro", "enterprise", "team"):
        sub = raw_sub
    rate = parsed.get("rate_limit_tier")
    rate_limit_tier = str(rate) if rate is not None else None
    profile = None
    prof = parsed.get("profile")
    if isinstance(prof, dict):
        profile = OAuthProfileResponse.from_dict(prof)
    token_account = None
    ta = parsed.get("token_account")
    if isinstance(ta, dict):
        token_account = OAuthTokenAccount(
            uuid=str(ta.get("uuid", "")),
            email_address=str(ta.get("email_address", "")),
            organization_uuid=ta.get("organization_uuid"),
        )
    return OAuthTokens(
        access_token=access,
        refresh_token=refresh,
        expires_at=int(exp),
        scopes=scopes,
        subscription_type=sub,
        rate_limit_tier=rate_limit_tier,
        profile=profile,
        token_account=token_account,
    )


def _profile_to_storage_dict(profile: OAuthProfileResponse) -> dict[str, Any]:
    """Serialize profile for JSON storage (nested dataclasses)."""
    return asdict(profile)


def save_claude_ai_oauth_tokens(tokens: OAuthTokens) -> bool:
    """Persist Claude.ai OAuth tokens to secure storage as a single JSON blob."""
    blob: dict[str, Any] = {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "expires_at": tokens.expires_at,
        "scopes": tokens.scopes,
    }
    if tokens.subscription_type is not None:
        blob["subscription_type"] = tokens.subscription_type
    if tokens.rate_limit_tier is not None:
        blob["rate_limit_tier"] = tokens.rate_limit_tier
    if tokens.profile is not None:
        blob["profile"] = _profile_to_storage_dict(tokens.profile)
    if tokens.token_account is not None:
        blob["token_account"] = {
            "uuid": tokens.token_account.uuid,
            "email_address": tokens.token_account.email_address,
            "organization_uuid": tokens.token_account.organization_uuid,
        }
    return set_credential(
        CLAUDE_AI_OAUTH_STORAGE_SERVICE,
        CLAUDE_AI_OAUTH_STORAGE_ACCOUNT,
        json.dumps(blob),
    )


def clear_claude_ai_oauth_tokens() -> bool:
    """Remove persisted Claude.ai OAuth tokens from secure storage."""
    return delete_credential(
        CLAUDE_AI_OAUTH_STORAGE_SERVICE,
        CLAUDE_AI_OAUTH_STORAGE_ACCOUNT,
    )


def should_use_claude_ai_auth(scopes: list[str] | None) -> bool:
    return bool(scopes and CLAUDE_AI_INFERENCE_SCOPE in scopes)


def parse_scopes(scope_string: str | None) -> list[str]:
    if not scope_string:
        return []
    return [s for s in scope_string.split(" ") if s]


def build_auth_url(
    *,
    code_challenge: str,
    state: str,
    port: int,
    is_manual: bool,
    login_with_claude_ai: bool | None = None,
    inference_only: bool | None = None,
    org_uuid: str | None = None,
    login_hint: str | None = None,
    login_method: str | None = None,
) -> str:
    cfg = get_oauth_config()
    base = cfg.CLAUDE_AI_AUTHORIZE_URL if login_with_claude_ai else cfg.CONSOLE_AUTHORIZE_URL
    redirect_uri = cfg.MANUAL_REDIRECT_URL if is_manual else f"http://localhost:{port}/callback"
    scopes_to_use = [CLAUDE_AI_INFERENCE_SCOPE] if inference_only else list(ALL_OAUTH_SCOPES)
    params: dict[str, str] = {
        "code": "true",
        "client_id": cfg.CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes_to_use),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    if org_uuid:
        params["orgUUID"] = org_uuid
    if login_hint:
        params["login_hint"] = login_hint
    if login_method:
        params["login_method"] = login_method
    return f"{base}?{urlencode(params)}"


async def exchange_code_for_tokens(
    authorization_code: str,
    state: str,
    code_verifier: str,
    port: int,
    use_manual_redirect: bool = False,
    expires_in: int | None = None,
    *,
    timeout_s: float = 15.0,
) -> OAuthTokenExchangeResponse:
    cfg = get_oauth_config()
    body: dict[str, Any] = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": cfg.MANUAL_REDIRECT_URL if use_manual_redirect else f"http://localhost:{port}/callback",
        "client_id": cfg.CLIENT_ID,
        "code_verifier": code_verifier,
        "state": state,
    }
    if expires_in is not None:
        body["expires_in"] = expires_in

    async with httpx.AsyncClient() as client:
        response = await client.post(
            cfg.TOKEN_URL,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=timeout_s,
        )

    if response.status_code != 200:
        msg = (
            "Authentication failed: Invalid authorization code"
            if response.status_code == 401
            else f"Token exchange failed ({response.status_code}): {response.text}"
        )
        raise RuntimeError(msg)

    log_event("tengu_oauth_token_exchange_success", {})
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("Token exchange returned non-object JSON")
    return OAuthTokenExchangeResponse.from_dict(data)


def _subscription_from_org_type(org_type: str | None) -> SubscriptionType:
    if org_type == "claude_max":
        return "max"
    if org_type == "claude_pro":
        return "pro"
    if org_type == "claude_enterprise":
        return "enterprise"
    if org_type == "claude_team":
        return "team"
    return None


async def fetch_profile_info(access_token: str) -> ProfileInfo:
    profile = await get_oauth_profile_from_oauth_token(access_token)
    if not profile:
        return ProfileInfo(
            subscription_type=None,
            display_name=None,
            rate_limit_tier=None,
            has_extra_usage_enabled=None,
            billing_type=None,
            account_created_at=None,
            subscription_created_at=None,
            raw_profile=None,
        )
    org_type = profile.organization.organization_type if profile.organization else None
    subscription_type = _subscription_from_org_type(org_type)
    org = profile.organization
    acc = profile.account
    log_event("tengu_oauth_profile_fetch_success", {})
    return ProfileInfo(
        subscription_type=subscription_type,
        display_name=acc.display_name if acc else None,
        rate_limit_tier=org.rate_limit_tier if org else None,
        has_extra_usage_enabled=org.has_extra_usage_enabled if org else None,
        billing_type=org.billing_type if org else None,
        account_created_at=acc.created_at if acc else None,
        subscription_created_at=org.subscription_created_at if org else None,
        raw_profile=profile,
    )


def get_claude_ai_oauth_tokens() -> OAuthTokens | None:
    """
    Load Claude.ai OAuth tokens from secure storage (JSON blob).

    Tests may monkeypatch this function to bypass storage.
    """
    raw = get_credential(CLAUDE_AI_OAUTH_STORAGE_SERVICE, CLAUDE_AI_OAUTH_STORAGE_ACCOUNT)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return _tokens_from_storage_blob(parsed)


async def refresh_oauth_token(
    refresh_token: str,
    *,
    scopes: list[str] | None = None,
    timeout_s: float = 15.0,
) -> OAuthTokens:
    cfg = get_oauth_config()
    scope_list = scopes if scopes else list(CLAUDE_AI_OAUTH_SCOPES)
    body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": cfg.CLIENT_ID,
        "scope": " ".join(scope_list),
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cfg.TOKEN_URL,
                json=body,
                headers={"Content-Type": "application/json"},
                timeout=timeout_s,
            )
        if response.status_code != 200:
            raise RuntimeError(f"Token refresh failed: {response.text}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Refresh returned non-object JSON")
        data = OAuthTokenExchangeResponse.from_dict(payload)
        access_token = data.access_token
        new_refresh = data.refresh_token or refresh_token
        expires_at = int(time.time() * 1000) + int(data.expires_in) * 1000
        scopes_out = parse_scopes(data.scope)

        log_event("tengu_oauth_token_refresh_success", {})

        config = get_global_config()
        existing = get_claude_ai_oauth_tokens()
        oa = config.oauth_account or {}
        have_profile = (
            oa.get("billingType") is not None
            and oa.get("accountCreatedAt") is not None
            and oa.get("subscriptionCreatedAt") is not None
            and existing is not None
            and existing.subscription_type is not None
            and existing.rate_limit_tier is not None
        )
        profile_info = None if have_profile else await fetch_profile_info(access_token)

        if profile_info and profile_info.raw_profile and config.oauth_account is not None:
            updates: dict[str, Any] = {}
            if profile_info.display_name is not None:
                updates["displayName"] = profile_info.display_name
            if isinstance(profile_info.has_extra_usage_enabled, bool):
                updates["hasExtraUsageEnabled"] = profile_info.has_extra_usage_enabled
            if profile_info.billing_type is not None:
                updates["billingType"] = profile_info.billing_type
            if profile_info.account_created_at is not None:
                updates["accountCreatedAt"] = profile_info.account_created_at
            if profile_info.subscription_created_at is not None:
                updates["subscriptionCreatedAt"] = profile_info.subscription_created_at
            if updates:

                def _merge(cur: dict[str, Any]) -> dict[str, Any]:
                    oacct = cur.get("oauthAccount")
                    if not isinstance(oacct, dict):
                        return cur
                    merged_o = {**oacct, **updates}
                    return {**cur, "oauthAccount": merged_o}

                save_global_config(_merge)

        token_account = None
        if data.account:
            org_uuid = None
            if data.organization and isinstance(data.organization, dict):
                org_uuid = data.organization.get("uuid")
            token_account = OAuthTokenAccount(
                uuid=str(data.account.get("uuid", "")),
                email_address=str(data.account.get("email_address", "")),
                organization_uuid=org_uuid,
            )

        refreshed = OAuthTokens(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_at=expires_at,
            scopes=scopes_out,
            subscription_type=(
                profile_info.subscription_type if profile_info else (existing.subscription_type if existing else None)
            ),
            rate_limit_tier=(
                profile_info.rate_limit_tier if profile_info else (existing.rate_limit_tier if existing else None)
            ),
            profile=profile_info.raw_profile if profile_info else None,
            token_account=token_account,
        )
        save_claude_ai_oauth_tokens(refreshed)
        return refreshed
    except Exception as err:
        body = ""
        if isinstance(err, httpx.HTTPStatusError) and err.response is not None:
            try:
                body = json.dumps(err.response.json())
            except Exception:
                body = err.response.text
        log_event(
            "tengu_oauth_token_refresh_failure",
            {"error": str(err), **({"responseBody": body} if body else {})},
        )
        raise


async def fetch_and_store_user_roles(access_token: str, *, timeout_s: float = 15.0) -> None:
    cfg = get_oauth_config()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            cfg.ROLES_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=timeout_s,
        )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch user roles: {response.text}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Roles response not an object")
    data = UserRolesResponse(
        organization_role=payload.get("organization_role"),
        workspace_role=payload.get("workspace_role"),
        organization_name=payload.get("organization_name"),
    )
    config = get_global_config()
    if not config.oauth_account:
        raise RuntimeError("OAuth account information not found in config")

    def _upd(cur: dict[str, Any]) -> dict[str, Any]:
        oa = cur.get("oauthAccount")
        if not isinstance(oa, dict):
            return cur
        oa = {
            **oa,
            "organizationRole": data.organization_role,
            "workspaceRole": data.workspace_role,
            "organizationName": data.organization_name,
        }
        return {**cur, "oauthAccount": oa}

    save_global_config(_upd)
    log_event("tengu_oauth_roles_stored", {"org_role": data.organization_role or ""})


async def create_and_store_api_key(access_token: str, *, timeout_s: float = 15.0) -> str | None:
    cfg = get_oauth_config()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cfg.API_KEY_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=timeout_s,
            )
        payload = response.json() if response.content else {}
        api_key = payload.get("raw_key") if isinstance(payload, dict) else None
        if api_key:
            log_event(
                "tengu_oauth_api_key",
                {"status": "success", "statusCode": response.status_code},
            )
            return str(api_key)
        log_event("tengu_oauth_api_key", {"status": "failure", "error": "empty"})
        return None
    except Exception as err:
        log_event(
            "tengu_oauth_api_key",
            {"status": "failure", "error": str(err)},
        )
        raise


def is_oauth_token_expired(expires_at: int | None) -> bool:
    if expires_at is None:
        return False
    buffer_ms = 5 * 60 * 1000
    now = int(time.time() * 1000)
    return now + buffer_ms >= expires_at


async def check_and_refresh_oauth_token_if_needed() -> None:
    """Refresh stored access token when within expiry buffer; updates secure storage on success."""
    tokens = get_claude_ai_oauth_tokens()
    if tokens is None or not tokens.refresh_token:
        return
    if not is_oauth_token_expired(tokens.expires_at):
        return
    try:
        await refresh_oauth_token(tokens.refresh_token, scopes=tokens.scopes or None)
    except Exception:
        # refresh_oauth_token logs failure; callers tolerate stale token until user re-auth
        return


async def get_organization_uuid() -> str | None:
    config = get_global_config()
    oa = config.oauth_account or {}
    org = oa.get("organizationUuid")
    if org:
        return str(org)
    tokens = get_claude_ai_oauth_tokens()
    if tokens is None or not tokens.access_token:
        return None
    profile = await get_oauth_profile_from_oauth_token(tokens.access_token)
    if profile and profile.organization and profile.organization.uuid:
        return profile.organization.uuid
    return None


async def populate_oauth_account_info_if_needed() -> bool:
    import os

    await check_and_refresh_oauth_token_if_needed()
    env_uuid = os.environ.get("CLAUDE_CODE_ACCOUNT_UUID")
    env_email = os.environ.get("CLAUDE_CODE_USER_EMAIL")
    env_org = os.environ.get("CLAUDE_CODE_ORGANIZATION_UUID")
    if env_uuid and env_email and env_org and get_global_config().oauth_account is None:
        store_oauth_account_info(
            account_uuid=env_uuid,
            email_address=env_email,
            organization_uuid=env_org,
        )

    config = get_global_config()
    oa = config.oauth_account or {}
    if (
        oa.get("billingType") is not None
        and oa.get("accountCreatedAt") is not None
        and oa.get("subscriptionCreatedAt") is not None
    ):
        return False

    tokens = get_claude_ai_oauth_tokens()
    if tokens is None or not tokens.access_token:
        return False

    profile = await get_oauth_profile_from_oauth_token(tokens.access_token)
    if not profile or not profile.account or not profile.organization:
        return False

    store_oauth_account_info(
        account_uuid=str(profile.account.uuid or ""),
        email_address=str(profile.account.email or ""),
        organization_uuid=str(profile.organization.uuid or ""),
        display_name=profile.account.display_name,
        has_extra_usage_enabled=profile.organization.has_extra_usage_enabled or False,
        billing_type=profile.organization.billing_type,
        account_created_at=profile.account.created_at,
        subscription_created_at=profile.organization.subscription_created_at,
    )
    return True


def store_oauth_account_info(
    *,
    account_uuid: str,
    email_address: str,
    organization_uuid: str | None,
    display_name: str | None = None,
    has_extra_usage_enabled: bool | None = None,
    billing_type: str | None = None,
    account_created_at: str | None = None,
    subscription_created_at: str | None = None,
) -> None:
    account_info: dict[str, Any] = {
        "accountUuid": account_uuid,
        "emailAddress": email_address,
        "organizationUuid": organization_uuid,
    }
    if has_extra_usage_enabled is not None:
        account_info["hasExtraUsageEnabled"] = has_extra_usage_enabled
    if billing_type is not None:
        account_info["billingType"] = billing_type
    if account_created_at is not None:
        account_info["accountCreatedAt"] = account_created_at
    if subscription_created_at is not None:
        account_info["subscriptionCreatedAt"] = subscription_created_at
    if display_name:
        account_info["displayName"] = display_name

    def _save(cur: dict[str, Any]) -> dict[str, Any]:
        prev = cur.get("oauthAccount")
        if isinstance(prev, dict) and (
            prev.get("accountUuid") == account_info.get("accountUuid")
            and prev.get("emailAddress") == account_info.get("emailAddress")
            and prev.get("organizationUuid") == account_info.get("organizationUuid")
            and prev.get("displayName") == account_info.get("displayName")
            and prev.get("hasExtraUsageEnabled") == account_info.get("hasExtraUsageEnabled")
            and prev.get("billingType") == account_info.get("billingType")
            and prev.get("accountCreatedAt") == account_info.get("accountCreatedAt")
            and prev.get("subscriptionCreatedAt") == account_info.get("subscriptionCreatedAt")
        ):
            return cur
        return {**cur, "oauthAccount": account_info}

    save_global_config(_save)
