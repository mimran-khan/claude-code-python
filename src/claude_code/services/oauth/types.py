"""
OAuth types for token exchange and profile responses.

Migrated from: services/oauth/types (inferred from client.ts / index.ts).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SubscriptionType = Literal["max", "pro", "enterprise", "team"] | None
RateLimitTier = str | None
BillingType = str | None


@dataclass
class OAuthOrganization:
    """Organization block from OAuth profile."""

    uuid: str | None = None
    organization_type: str | None = None
    rate_limit_tier: str | None = None
    has_extra_usage_enabled: bool | None = None
    billing_type: str | None = None
    subscription_created_at: str | None = None


@dataclass
class OAuthAccount:
    """Account block from OAuth profile."""

    uuid: str | None = None
    email: str | None = None
    display_name: str | None = None
    created_at: str | None = None


@dataclass
class OAuthProfileResponse:
    """Response from GET /api/oauth/profile."""

    account: OAuthAccount | None = None
    organization: OAuthOrganization | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> OAuthProfileResponse | None:
        if not data or not isinstance(data, dict):
            return None
        acc = data.get("account")
        org = data.get("organization")
        account = None
        if isinstance(acc, dict):
            account = OAuthAccount(
                uuid=acc.get("uuid"),
                email=acc.get("email"),
                display_name=acc.get("display_name"),
                created_at=acc.get("created_at"),
            )
        organization = None
        if isinstance(org, dict):
            organization = OAuthOrganization(
                uuid=org.get("uuid"),
                organization_type=org.get("organization_type"),
                rate_limit_tier=org.get("rate_limit_tier"),
                has_extra_usage_enabled=org.get("has_extra_usage_enabled"),
                billing_type=org.get("billing_type"),
                subscription_created_at=org.get("subscription_created_at"),
            )
        return cls(account=account, organization=organization)


@dataclass
class OAuthTokenAccount:
    """Account summary returned with token exchange."""

    uuid: str
    email_address: str
    organization_uuid: str | None = None


@dataclass
class OAuthTokenExchangeResponse:
    """Raw token endpoint JSON."""

    access_token: str
    refresh_token: str | None = None
    expires_in: int = 3600
    scope: str | None = None
    account: dict[str, Any] | None = None
    organization: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OAuthTokenExchangeResponse:
        return cls(
            access_token=str(data["access_token"]),
            refresh_token=data.get("refresh_token"),
            expires_in=int(data.get("expires_in", 3600)),
            scope=data.get("scope"),
            account=data.get("account") if isinstance(data.get("account"), dict) else None,
            organization=data.get("organization") if isinstance(data.get("organization"), dict) else None,
        )


@dataclass
class OAuthTokens:
    """Normalized tokens after exchange or refresh."""

    access_token: str
    refresh_token: str
    expires_at: int
    scopes: list[str] = field(default_factory=list)
    subscription_type: SubscriptionType = None
    rate_limit_tier: RateLimitTier = None
    profile: OAuthProfileResponse | None = None
    token_account: OAuthTokenAccount | None = None


@dataclass
class UserRolesResponse:
    """Roles endpoint payload."""

    organization_role: str | None = None
    workspace_role: str | None = None
    organization_name: str | None = None


@dataclass
class ProfileInfo:
    """Derived profile fields for config updates."""

    subscription_type: SubscriptionType
    display_name: str | None
    rate_limit_tier: RateLimitTier
    has_extra_usage_enabled: bool | None
    billing_type: BillingType
    account_created_at: str | None
    subscription_created_at: str | None
    raw_profile: OAuthProfileResponse | None = None
