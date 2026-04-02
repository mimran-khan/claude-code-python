"""
Authentication Helpers.

Helper functions for authentication.
"""

from __future__ import annotations

import os

from .types import SubscriptionType


def get_api_key() -> str | None:
    """Get the API key from environment or config.

    Returns:
        The API key, or None if not configured
    """
    # Check environment variable first
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    # In a full implementation, this would also check:
    # 1. Secure storage (keychain)
    # 2. Config file
    # 3. OAuth tokens

    return None


def is_authenticated() -> bool:
    """Check if the user is authenticated.

    Returns:
        True if authenticated
    """
    return get_api_key() is not None


def get_subscription_type() -> SubscriptionType:
    """Get the current subscription type.

    Returns:
        The subscription type
    """
    # In a full implementation, this would check:
    # 1. OAuth profile
    # 2. API response headers
    # 3. Mock subscription (for testing)

    return "free"


def is_pro_subscriber() -> bool:
    """Check if the user has a Pro subscription.

    Returns:
        True if Pro subscriber
    """
    return get_subscription_type() in ("pro", "max", "team", "team_premium", "enterprise")


def is_max_subscriber() -> bool:
    """Check if the user has a Max subscription.

    Returns:
        True if Max subscriber
    """
    return get_subscription_type() in ("max", "enterprise")


def is_team_subscriber() -> bool:
    """Check if the user has a Team subscription.

    Returns:
        True if Team subscriber
    """
    return get_subscription_type() in ("team", "team_premium")


def is_team_premium_subscriber() -> bool:
    """Check if the user has a Team Premium subscription.

    Returns:
        True if Team Premium subscriber
    """
    return get_subscription_type() == "team_premium"


def is_enterprise_subscriber() -> bool:
    """Check if the user has an Enterprise subscription.

    Returns:
        True if Enterprise subscriber
    """
    return get_subscription_type() == "enterprise"
