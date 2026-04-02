"""
Plugin schemas and validation.

Schema definitions and validation for plugins and marketplaces.

Migrated from: utils/plugins/schemas.ts (1682 lines) - Core types
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

# Plugin scope types
PluginScope = Literal["user", "project", "local", "managed"]

# Marketplace source types
MarketplaceSourceType = Literal["github", "git", "local"]


# Official marketplace names reserved for Anthropic/Claude
ALLOWED_OFFICIAL_MARKETPLACE_NAMES = {
    "claude-code-marketplace",
    "claude-code-plugins",
    "claude-plugins-official",
    "anthropic-marketplace",
    "anthropic-plugins",
    "agent-skills",
    "life-sciences",
    "knowledge-work-plugins",
}

# Marketplaces that should NOT auto-update
NO_AUTO_UPDATE_OFFICIAL_MARKETPLACES = {"knowledge-work-plugins"}

# Official GitHub organization
OFFICIAL_GITHUB_ORG = "anthropics"

# Pattern to detect official name impersonation
BLOCKED_OFFICIAL_NAME_PATTERN = re.compile(
    r"(?:official[^a-z0-9]*(anthropic|claude)|"
    r"(?:anthropic|claude)[^a-z0-9]*official|"
    r"^(?:anthropic|claude)[^a-z0-9]*(marketplace|plugins|official))",
    re.IGNORECASE,
)

# Pattern to detect non-ASCII characters (homograph attacks)
NON_ASCII_PATTERN = re.compile(r"[^\u0020-\u007E]")


@dataclass
class MarketplaceSource:
    """Marketplace source configuration."""

    source: MarketplaceSourceType
    repo: str | None = None
    url: str | None = None
    branch: str | None = None
    path: str | None = None


@dataclass
class PluginManifest:
    """Plugin manifest (plugin.json)."""

    name: str
    version: str
    description: str = ""
    author: str | None = None
    license: str | None = None
    homepage: str | None = None
    repository: str | None = None
    main: str | None = None
    engines: dict[str, str] = field(default_factory=dict)
    dependencies: dict[str, str] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)
    commands: list[dict[str, Any]] = field(default_factory=list)
    hooks: list[dict[str, Any]] = field(default_factory=list)


def is_marketplace_auto_update(
    marketplace_name: str,
    entry: dict[str, Any],
) -> bool:
    """
    Check if auto-update is enabled for a marketplace.

    Uses stored value if set, otherwise defaults based on whether
    it's an official Anthropic marketplace.
    """
    normalized_name = marketplace_name.lower()

    if "autoUpdate" in entry:
        return bool(entry["autoUpdate"])

    return (
        normalized_name in ALLOWED_OFFICIAL_MARKETPLACE_NAMES
        and normalized_name not in NO_AUTO_UPDATE_OFFICIAL_MARKETPLACES
    )


def is_blocked_official_name(name: str) -> bool:
    """
    Check if a marketplace name impersonates an official marketplace.

    Args:
        name: The marketplace name to check

    Returns:
        True if blocked (impersonates official), False if allowed
    """
    # If it's in the allowed list, it's not blocked
    if name.lower() in ALLOWED_OFFICIAL_MARKETPLACE_NAMES:
        return False

    # Block names with non-ASCII characters (homograph attacks)
    if NON_ASCII_PATTERN.search(name):
        return True

    # Check if it matches the blocked pattern
    return bool(BLOCKED_OFFICIAL_NAME_PATTERN.search(name))


def validate_official_name_source(
    name: str,
    source: dict[str, Any],
) -> str | None:
    """
    Validate that a marketplace with a reserved name comes from official source.

    Args:
        name: The marketplace name
        source: The marketplace source configuration

    Returns:
        Error message if validation fails, None if valid
    """
    normalized_name = name.lower()

    # Only validate reserved names
    if normalized_name not in ALLOWED_OFFICIAL_MARKETPLACE_NAMES:
        return None

    source_type = source.get("source", "")

    # Check for GitHub source type
    if source_type == "github":
        repo = source.get("repo", "")
        if not repo.lower().startswith(f"{OFFICIAL_GITHUB_ORG}/"):
            return (
                f"The name '{name}' is reserved for official Anthropic marketplaces. "
                f"Only repositories from 'github.com/{OFFICIAL_GITHUB_ORG}/' can use this name."
            )
        return None

    # Check for git URL source type
    if source_type == "git" and source.get("url"):
        url = source["url"].lower()
        is_https = f"github.com/{OFFICIAL_GITHUB_ORG}/" in url
        is_ssh = f"git@github.com:{OFFICIAL_GITHUB_ORG}/" in url

        if is_https or is_ssh:
            return None

    # Reserved name from non-official source
    return (
        f"The name '{name}' is reserved for official Anthropic marketplaces and cannot be used by third-party sources."
    )


def validate_plugin_name(name: str) -> str | None:
    """
    Validate a plugin name.

    Args:
        name: The plugin name to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not name:
        return "Plugin name cannot be empty"

    if len(name) > 214:
        return "Plugin name too long (max 214 characters)"

    # Must start with lowercase letter or @
    if not re.match(r"^[@a-z]", name):
        return "Plugin name must start with lowercase letter or @"

    # Check for valid characters
    if not re.match(r"^[@a-z0-9][-._a-z0-9]*$", name):
        return "Plugin name contains invalid characters"

    return None
