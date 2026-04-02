"""
Constants for the official Anthropic plugins marketplace.

Migrated from: utils/plugins/officialMarketplace.ts
"""

from __future__ import annotations

from typing import Any, Final

# Registered name in known_marketplaces.json
OFFICIAL_MARKETPLACE_NAME: Final[str] = "claude-plugins-official"

# Source used when auto-installing / reconciling the official marketplace
OFFICIAL_MARKETPLACE_SOURCE: Final[dict[str, Any]] = {
    "source": "github",
    "repo": "anthropics/claude-plugins-official",
}

__all__ = [
    "OFFICIAL_MARKETPLACE_NAME",
    "OFFICIAL_MARKETPLACE_SOURCE",
]
