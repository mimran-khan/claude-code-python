"""
Marketplace policy, blocklist, and display helpers.

Migrated from: utils/plugins/marketplaceHelpers.ts (minimal port).
"""

from __future__ import annotations

from typing import Any

from ..settings.settings import get_settings_for_source


def is_local_marketplace_source(source: dict[str, Any]) -> bool:
    return source.get("source") in ("directory", "file")


def get_blocked_marketplaces() -> list[str]:
    policy = get_settings_for_source("policySettings") or {}
    blocked = policy.get("blockedMarketplaces")
    if isinstance(blocked, list):
        return [str(x) for x in blocked]
    return []


def get_strict_known_marketplaces() -> list[str] | None:
    policy = get_settings_for_source("policySettings") or {}
    strict = policy.get("strictKnownMarketplaces")
    if isinstance(strict, list):
        return [str(x) for x in strict]
    return None


def is_source_in_blocklist(_source: dict[str, Any]) -> bool:
    return False


def is_source_allowed_by_policy(_source: dict[str, Any]) -> bool:
    return True


def format_source_for_display(source: dict[str, Any]) -> str:
    st = source.get("source")
    if st == "github" and source.get("repo"):
        return str(source["repo"])
    if st in ("git", "url") and source.get("url"):
        return str(source["url"])
    if st in ("directory", "file") and source.get("path"):
        return str(source["path"])
    return str(source)


__all__ = [
    "format_source_for_display",
    "get_blocked_marketplaces",
    "get_strict_known_marketplaces",
    "is_local_marketplace_source",
    "is_source_allowed_by_policy",
    "is_source_in_blocklist",
]
