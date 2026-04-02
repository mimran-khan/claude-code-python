"""
Eligibility for remote managed settings (auth-aware).

Migrated from: services/remoteManagedSettings/syncCache.ts
"""

from __future__ import annotations

import os

from ...constants.oauth import CLAUDE_AI_INFERENCE_SCOPE
from .sync_cache_state import reset_sync_cache as reset_leaf_cache
from .sync_cache_state import set_eligibility

_cached: bool | None = None


def reset_sync_cache() -> None:
    global _cached
    _cached = None
    reset_leaf_cache()


def is_remote_managed_settings_eligible() -> bool:
    global _cached
    if _cached is not None:
        return _cached

    try:
        from ...utils.model.providers import get_api_provider, is_first_party
    except ImportError:
        _cached = False
        set_eligibility(False)
        return False

    if get_api_provider() != "firstParty" or not is_first_party():
        _cached = False
        set_eligibility(False)
        return False

    base = os.getenv("ANTHROPIC_API_URL", "").strip()
    if base and base.rstrip("/") != "https://api.anthropic.com":
        _cached = False
        set_eligibility(False)
        return False

    if os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "local-agent":
        _cached = False
        set_eligibility(False)
        return False

    if os.environ.get("ANTHROPIC_API_KEY"):
        _cached = True
        set_eligibility(True)
        return True

    try:
        from ..oauth.client import get_claude_ai_oauth_tokens
    except ImportError:
        _cached = False
        set_eligibility(False)
        return False

    tokens = get_claude_ai_oauth_tokens()
    if tokens and tokens.access_token:
        if getattr(tokens, "subscription_type", None) is None:
            _cached = True
            set_eligibility(True)
            return True
        scopes = getattr(tokens, "scopes", None) or []
        st = getattr(tokens, "subscription_type", None)
        if CLAUDE_AI_INFERENCE_SCOPE in scopes and st in ("enterprise", "team"):
            _cached = True
            set_eligibility(True)
            return True

    _cached = False
    set_eligibility(False)
    return False
