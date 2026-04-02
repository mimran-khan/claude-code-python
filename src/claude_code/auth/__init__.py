"""
Authentication Module.

Handles API key management and authentication.
"""

from .helpers import (
    get_api_key,
    get_subscription_type,
    is_authenticated,
    is_max_subscriber,
    is_pro_subscriber,
    is_team_subscriber,
)
from .types import (
    AccountInfo,
    AuthState,
    SubscriptionType,
)

__all__ = [
    "SubscriptionType",
    "AccountInfo",
    "AuthState",
    "get_api_key",
    "is_authenticated",
    "is_pro_subscriber",
    "is_max_subscriber",
    "is_team_subscriber",
    "get_subscription_type",
]
