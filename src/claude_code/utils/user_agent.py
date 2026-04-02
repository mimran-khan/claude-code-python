"""
Minimal User-Agent string for SDK / bridge transports.

Migrated from: utils/userAgent.ts (dependency-free vs full HTTP helpers).
"""

from __future__ import annotations

import os

from .http import VERSION


def get_claude_code_user_agent() -> str:
    """Return ``claude-code/<version>`` using the same version source as ``http.py``."""

    return f"claude-code/{VERSION}"


def get_claude_code_user_agent_from_env() -> str:
    """Prefer explicit ``CLAUDE_CODE_VERSION`` then package default."""

    ver = os.getenv("CLAUDE_CODE_VERSION", VERSION)
    return f"claude-code/{ver}"


__all__ = ["get_claude_code_user_agent", "get_claude_code_user_agent_from_env"]
