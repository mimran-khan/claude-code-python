"""
Authentication Types.

Type definitions for authentication.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SubscriptionType = Literal[
    "free",
    "pro",
    "max",
    "team",
    "team_premium",
    "enterprise",
]


@dataclass
class AccountInfo:
    """Account information."""

    email: str | None = None
    organization_id: str | None = None
    subscription_type: SubscriptionType = "free"
    has_trust_dialog_accepted: bool = False


@dataclass
class AuthState:
    """Authentication state."""

    is_authenticated: bool = False
    api_key: str | None = None
    account_info: AccountInfo | None = None
    error: str | None = None
