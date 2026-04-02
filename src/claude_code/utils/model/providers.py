"""
API provider utilities.

Provider detection and configuration.

Migrated from: utils/model/providers.ts
"""

from __future__ import annotations

import os
from typing import Literal

APIProvider = Literal["firstParty", "bedrock", "vertex", "foundry"]


def get_api_provider() -> APIProvider:
    """
    Get the current API provider.

    Checks environment variables to determine which provider to use.
    """
    from ..env_utils import is_env_truthy

    if is_env_truthy(os.getenv("CLAUDE_CODE_USE_BEDROCK")):
        return "bedrock"

    if is_env_truthy(os.getenv("CLAUDE_CODE_USE_VERTEX")):
        return "vertex"

    if is_env_truthy(os.getenv("CLAUDE_CODE_USE_FOUNDRY")):
        return "foundry"

    return "firstParty"


def is_first_party() -> bool:
    """Check if using first-party API."""
    return get_api_provider() == "firstParty"


def is_bedrock() -> bool:
    """Check if using Bedrock."""
    return get_api_provider() == "bedrock"


def is_vertex() -> bool:
    """Check if using Vertex AI."""
    return get_api_provider() == "vertex"


def is_foundry() -> bool:
    """Check if using Foundry."""
    return get_api_provider() == "foundry"


def is_third_party_provider() -> bool:
    """Check if using any third-party provider."""
    return get_api_provider() != "firstParty"


def get_provider_name() -> str:
    """Get the display name for the current provider."""
    provider = get_api_provider()

    names = {
        "firstParty": "Anthropic",
        "bedrock": "AWS Bedrock",
        "vertex": "Google Vertex AI",
        "foundry": "Azure Foundry",
    }

    return names.get(provider, "Unknown")


def get_api_base_url() -> str:
    """Get the API base URL for the current provider."""
    provider = get_api_provider()

    if provider == "firstParty":
        return os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com")

    if provider == "bedrock":
        region = os.getenv("AWS_REGION", "us-east-1")
        return f"https://bedrock-runtime.{region}.amazonaws.com"

    if provider == "vertex":
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        region = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
        return f"https://{region}-aiplatform.googleapis.com/v1/projects/{project}"

    if provider == "foundry":
        return os.getenv("AZURE_FOUNDRY_ENDPOINT", "")

    return ""
