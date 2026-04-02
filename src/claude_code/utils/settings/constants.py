"""
Settings constants.

Defines setting sources and related constants.

Migrated from: utils/settings/constants.ts (203 lines)
"""

from __future__ import annotations

from typing import Literal

# All possible sources where settings can come from
# Order matters - later sources override earlier ones
SETTING_SOURCES = [
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
]

SettingSource = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
]

# Editable sources (can be modified by user)
EDITABLE_SETTING_SOURCES = [
    "userSettings",
    "projectSettings",
    "localSettings",
]

EditableSettingSource = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
]


def get_setting_source_name(source: SettingSource) -> str:
    """Get the short name for a setting source."""
    names = {
        "userSettings": "user",
        "projectSettings": "project",
        "localSettings": "project, gitignored",
        "flagSettings": "cli flag",
        "policySettings": "managed",
    }
    return names.get(source, source)


def get_source_display_name(source: str) -> str:
    """
    Get short display name for a setting source (capitalized).

    Used for context/skills UI.
    """
    names = {
        "userSettings": "User",
        "projectSettings": "Project",
        "localSettings": "Local",
        "flagSettings": "Flag",
        "policySettings": "Managed",
        "plugin": "Plugin",
        "built-in": "Built-in",
    }
    return names.get(source, source)


def get_setting_source_display_name_lowercase(source: str) -> str:
    """
    Get display name for a setting source (lowercase).

    Used for inline text.
    """
    names = {
        "userSettings": "user settings",
        "projectSettings": "shared project settings",
        "localSettings": "project local settings",
        "flagSettings": "command line arguments",
        "policySettings": "enterprise managed settings",
        "cliArg": "CLI argument",
        "command": "command configuration",
        "session": "current session",
    }
    return names.get(source, source)


def get_setting_source_display_name_capitalized(source: str) -> str:
    """
    Get display name for a setting source (capitalized).

    Used for UI labels.
    """
    names = {
        "userSettings": "User settings",
        "projectSettings": "Shared project settings",
        "localSettings": "Project local settings",
        "flagSettings": "Command line arguments",
        "policySettings": "Enterprise managed settings",
        "cliArg": "CLI argument",
        "command": "Command configuration",
        "session": "Current session",
    }
    return names.get(source, source)


def parse_setting_sources_flag(flag: str) -> list[SettingSource]:
    """
    Parse the --setting-sources CLI flag into SettingSource array.

    Args:
        flag: Comma-separated string like "user,project,local"

    Returns:
        Array of SettingSource values
    """
    if flag == "":
        return []

    names = [s.strip() for s in flag.split(",")]
    result: list[SettingSource] = []

    for name in names:
        if name == "user":
            result.append("userSettings")
        elif name == "project":
            result.append("projectSettings")
        elif name == "local":
            result.append("localSettings")
        else:
            raise ValueError(f"Invalid setting source: {name}. Valid options are: user, project, local")

    return result


# Default enabled sources (used when no CLI override)
_enabled_sources: list[SettingSource] | None = None


def get_enabled_setting_sources() -> list[SettingSource]:
    """
    Get the currently enabled setting sources.

    Returns default sources if not explicitly set.
    """
    global _enabled_sources
    if _enabled_sources is not None:
        return _enabled_sources

    # Default: all sources
    return list(SETTING_SOURCES)  # type: ignore


def set_enabled_setting_sources(sources: list[SettingSource]) -> None:
    """Set the enabled setting sources."""
    global _enabled_sources
    _enabled_sources = sources


def reset_enabled_setting_sources() -> None:
    """Reset to default setting sources."""
    global _enabled_sources
    _enabled_sources = None


def is_editable_source(source: str) -> bool:
    """Check if a source is editable."""
    return source in EDITABLE_SETTING_SOURCES


def get_editable_sources() -> list[EditableSettingSource]:
    """Get the list of editable setting sources."""
    return list(EDITABLE_SETTING_SOURCES)  # type: ignore
