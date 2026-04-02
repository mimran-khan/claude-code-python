"""
API Providers.

Configuration for different API providers.
"""

from __future__ import annotations

import os
from typing import Literal
from urllib.parse import urlparse

# API provider types
APIProvider = Literal["firstParty", "bedrock", "vertex", "foundry"]


def _is_env_truthy(value: str | None) -> bool:
    """Check if environment variable value is truthy."""
    if value is None:
        return False
    return value.lower() in ("1", "true", "yes")


def get_api_provider() -> APIProvider:
    """Get the current API provider based on environment configuration.

    Returns:
        The API provider type
    """
    if _is_env_truthy(os.environ.get("CLAUDE_CODE_USE_BEDROCK")):
        return "bedrock"
    if _is_env_truthy(os.environ.get("CLAUDE_CODE_USE_VERTEX")):
        return "vertex"
    if _is_env_truthy(os.environ.get("CLAUDE_CODE_USE_FOUNDRY")):
        return "foundry"
    return "firstParty"


def is_first_party_base_url() -> bool:
    """Check if ANTHROPIC_BASE_URL is a first-party Anthropic API URL.

    Returns True if not set (default API) or points to api.anthropic.com
    (or api-staging.anthropic.com for ant users).
    """
    base_url = os.environ.get("ANTHROPIC_BASE_URL")

    if not base_url:
        return True

    try:
        parsed = urlparse(base_url)
        host = parsed.netloc

        allowed_hosts = ["api.anthropic.com"]

        # Allow staging for ant users
        if os.environ.get("USER_TYPE") == "ant":
            allowed_hosts.append("api-staging.anthropic.com")

        return host in allowed_hosts
    except Exception:
        return False


def get_base_url() -> str:
    """Get the API base URL.

    Returns:
        The base URL for API requests
    """
    return os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")


def get_bedrock_region() -> str:
    """Get the AWS region for Bedrock API.

    Returns:
        The AWS region (defaults to us-west-2)
    """
    return os.environ.get("AWS_REGION", "us-west-2")


def get_vertex_project() -> str | None:
    """Get the GCP project ID for Vertex AI.

    Returns:
        The project ID, or None if not configured
    """
    return os.environ.get("GOOGLE_CLOUD_PROJECT")


def get_vertex_region() -> str:
    """Get the GCP region for Vertex AI.

    Returns:
        The GCP region (defaults to us-central1)
    """
    return os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")


def get_provider_display_name(provider: APIProvider) -> str:
    """Get a human-readable name for the provider.

    Args:
        provider: The API provider

    Returns:
        Display name for the provider
    """
    names = {
        "firstParty": "Anthropic API",
        "bedrock": "AWS Bedrock",
        "vertex": "Google Vertex AI",
        "foundry": "Foundry",
    }
    return names.get(provider, provider)
