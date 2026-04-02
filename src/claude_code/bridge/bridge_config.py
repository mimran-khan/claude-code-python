"""Bridge OAuth / base URL resolution (ported from bridge/bridgeConfig.ts)."""

from __future__ import annotations

import os

from ..constants.oauth import get_oauth_config
from ..services.oauth.client import get_claude_ai_oauth_tokens


def get_bridge_token_override() -> str | None:
    """Ant-only dev override: CLAUDE_BRIDGE_OAUTH_TOKEN, else None."""
    if os.environ.get("USER_TYPE") == "ant":
        return os.environ.get("CLAUDE_BRIDGE_OAUTH_TOKEN")
    return None


def get_bridge_base_url_override() -> str | None:
    """Ant-only dev override: CLAUDE_BRIDGE_BASE_URL, else None."""
    if os.environ.get("USER_TYPE") == "ant":
        return os.environ.get("CLAUDE_BRIDGE_BASE_URL")
    return None


def get_bridge_access_token() -> str | None:
    """Access token: dev override first, then OAuth store. None if not logged in."""
    override = get_bridge_token_override()
    if override:
        return override
    tokens = get_claude_ai_oauth_tokens()
    return tokens.access_token if tokens else None


def get_bridge_base_url() -> str:
    """Base URL for bridge API: dev override first, then production OAuth config."""
    override = get_bridge_base_url_override()
    if override:
        return override
    return get_oauth_config().BASE_API_URL
