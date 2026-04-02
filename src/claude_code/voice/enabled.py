"""
Voice mode enablement checks.

Migrated from: voice/voiceModeEnabled.ts
"""

import os


def _is_feature_enabled(feature: str) -> bool:
    """Check if a feature flag is enabled."""
    return os.environ.get(feature, "").lower() in ("1", "true", "yes")


def is_voice_growthbook_enabled() -> bool:
    """Check if voice mode is enabled via GrowthBook.

    Returns True unless the tengu_amber_quartz_disabled flag is on.
    A missing/stale cache reads as "not killed" so fresh installs
    get voice working immediately.
    """
    if not _is_feature_enabled("VOICE_MODE"):
        return False

    # Check GrowthBook kill switch
    # In full implementation, would check cached GrowthBook value
    # For now, check environment variable
    kill_switch = os.environ.get("VOICE_MODE_DISABLED", "")
    return kill_switch.lower() not in ("1", "true", "yes")


def has_voice_auth() -> bool:
    """Check if user has voice authentication.

    Voice mode requires Anthropic OAuth - it uses the voice_stream
    endpoint on claude.ai which is not available with API keys,
    Bedrock, Vertex, or Foundry.
    """
    # Check if Anthropic OAuth is enabled
    auth_provider = os.environ.get("CLAUDE_AUTH_PROVIDER", "")
    if auth_provider not in ("anthropic", "oauth"):
        return False

    # Check if we have an access token
    # In full implementation, would check keychain/token storage
    access_token = os.environ.get("CLAUDE_OAUTH_ACCESS_TOKEN", "")
    return bool(access_token)


def is_voice_mode_enabled() -> bool:
    """Full runtime check for voice mode.

    Checks both authentication and GrowthBook kill-switch.
    Use this for command-time paths where a fresh keychain
    read is acceptable.
    """
    return has_voice_auth() and is_voice_growthbook_enabled()


def get_voice_endpoint() -> str | None:
    """Get the voice streaming endpoint URL."""
    if not is_voice_mode_enabled():
        return None

    base_url = os.environ.get("CLAUDE_AI_BASE_URL", "https://claude.ai")
    return f"{base_url}/api/voice_stream"
