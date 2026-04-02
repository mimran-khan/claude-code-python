"""
Core settings management.

Functions for loading, caching, and updating settings.

Migrated from: utils/settings/settings.ts (1016 lines) - Core logic
"""

from __future__ import annotations

import json
import os
from typing import Any

from ..cwd import get_cwd
from ..env_utils import get_claude_config_home_dir
from ..json_utils import safe_parse_json
from ..log import log_error
from .constants import (
    SettingSource,
    get_enabled_setting_sources,
)
from .validation import ValidationError, validate_settings

# Settings cache
_settings_cache: dict[str, dict[str, Any] | None] = {}
_parsed_file_cache: dict[str, tuple[dict[str, Any] | None, list[ValidationError]]] = {}


def reset_settings_cache() -> None:
    """Reset all settings caches."""
    global _settings_cache, _parsed_file_cache
    _settings_cache.clear()
    _parsed_file_cache.clear()


def get_settings_file_path_for_source(source: SettingSource) -> str | None:
    """
    Get the file path for a settings source.

    Args:
        source: The settings source

    Returns:
        Path to the settings file, or None if not applicable
    """
    cwd = get_cwd()
    config_home = get_claude_config_home_dir()

    paths = {
        "userSettings": os.path.join(config_home, "settings.json"),
        "projectSettings": os.path.join(cwd, ".claude", "settings.json"),
        "localSettings": os.path.join(cwd, ".claude", "settings.local.json"),
        "policySettings": os.path.join(config_home, "managed-settings.json"),
        "flagSettings": None,  # Flag settings are inline, not file-based
    }

    return paths.get(source)


def get_settings_root_path_for_source(source: SettingSource) -> str | None:
    """
    Get the root directory for a settings source.

    Args:
        source: The settings source

    Returns:
        Root directory path, or None if not applicable
    """
    file_path = get_settings_file_path_for_source(source)
    if not file_path:
        return None
    return os.path.dirname(file_path)


def parse_settings_file(path: str) -> tuple[dict[str, Any] | None, list[ValidationError]]:
    """
    Parse a settings file into structured format.

    Args:
        path: Path to the settings file

    Returns:
        Tuple of (parsed settings, validation errors)
    """
    # Check cache
    if path in _parsed_file_cache:
        cached = _parsed_file_cache[path]
        # Clone to prevent mutation
        settings = dict(cached[0]) if cached[0] else None
        return settings, list(cached[1])

    result = _parse_settings_file_uncached(path)
    _parsed_file_cache[path] = result

    # Clone on return
    settings = dict(result[0]) if result[0] else None
    return settings, list(result[1])


def _parse_settings_file_uncached(path: str) -> tuple[dict[str, Any] | None, list[ValidationError]]:
    """Parse settings file without caching."""
    errors: list[ValidationError] = []

    try:
        if not os.path.isfile(path):
            return None, errors

        with open(path, encoding="utf-8") as f:
            content = f.read()

        if content.strip() == "":
            return {}, errors

        data = safe_parse_json(content, should_log_error=False)
        if data is None:
            errors.append(
                ValidationError(
                    path=path,
                    message="Invalid JSON in settings file",
                )
            )
            return None, errors

        if not isinstance(data, dict):
            errors.append(
                ValidationError(
                    path=path,
                    message="Settings file must contain a JSON object",
                )
            )
            return None, errors

        # Validate the settings
        validation_errors = validate_settings(data)
        errors.extend(validation_errors)

        return data, errors

    except FileNotFoundError:
        return None, errors
    except Exception as e:
        errors.append(
            ValidationError(
                path=path,
                message=f"Error reading settings file: {e}",
            )
        )
        log_error(e)
        return None, errors


def get_settings_for_source(source: SettingSource) -> dict[str, Any] | None:
    """
    Load and return settings from a specific source.

    Args:
        source: The settings source to load from

    Returns:
        Parsed settings dict, or None if not found
    """
    # Check cache
    cache_key = source
    if cache_key in _settings_cache:
        cached = _settings_cache[cache_key]
        return dict(cached) if cached else None

    settings = _get_settings_for_source_uncached(source)
    _settings_cache[cache_key] = settings

    return dict(settings) if settings else None


def _get_settings_for_source_uncached(source: SettingSource) -> dict[str, Any] | None:
    """Load settings without caching."""
    file_path = get_settings_file_path_for_source(source)
    if not file_path:
        return None

    settings, _ = parse_settings_file(file_path)
    return settings


def get_merged_settings() -> dict[str, Any]:
    """
    Get merged settings from all enabled sources.

    Later sources override earlier ones in the merge order.

    Returns:
        Merged settings dictionary
    """
    merged: dict[str, Any] = {}

    for source in get_enabled_setting_sources():
        settings = get_settings_for_source(source)
        if settings:
            merged = _merge_settings(merged, settings)

    return merged


def _merge_settings(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Merge two settings dictionaries.

    Arrays are concatenated, objects are deeply merged,
    primitives are overwritten.
    """
    result = dict(base)

    for key, value in override.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = _merge_settings(result[key], value)
        elif isinstance(value, list) and isinstance(result[key], list):
            result[key] = result[key] + value
        else:
            result[key] = value

    return result


def update_settings_for_source(
    source: SettingSource,
    updates: dict[str, Any],
) -> bool:
    """
    Update settings for a specific source.

    Args:
        source: The settings source to update
        updates: The updates to apply

    Returns:
        True if successful, False otherwise
    """
    from .constants import EDITABLE_SETTING_SOURCES

    # Only allow updating editable sources
    if source not in EDITABLE_SETTING_SOURCES:
        return False

    file_path = get_settings_file_path_for_source(source)
    if not file_path:
        return False

    try:
        # Load existing settings
        existing = get_settings_for_source(source) or {}

        # Merge updates
        merged = _merge_settings(existing, updates)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)

        # Invalidate cache
        if source in _settings_cache:
            del _settings_cache[source]
        if file_path in _parsed_file_cache:
            del _parsed_file_cache[file_path]

        return True

    except Exception as e:
        log_error(e)
        return False


def get_permission_rules_from_settings(
    source: SettingSource,
) -> dict[str, list[str]]:
    """
    Get permission rules from settings.

    Returns:
        Dict with 'allow', 'deny', 'ask' keys containing rule lists
    """
    settings = get_settings_for_source(source)
    if not settings or "permissions" not in settings:
        return {"allow": [], "deny": [], "ask": []}

    permissions = settings["permissions"]
    if not isinstance(permissions, dict):
        return {"allow": [], "deny": [], "ask": []}

    return {
        "allow": permissions.get("allow", []),
        "deny": permissions.get("deny", []),
        "ask": permissions.get("ask", []),
    }


def get_hooks_from_settings(source: SettingSource) -> list[dict[str, Any]]:
    """Get hooks configuration from settings."""
    settings = get_settings_for_source(source)
    if not settings or "hooks" not in settings:
        return []

    hooks = settings["hooks"]
    if isinstance(hooks, list):
        return hooks
    return []


def get_mcp_servers_from_settings(source: SettingSource) -> dict[str, dict[str, Any]]:
    """Get MCP server configurations from settings."""
    settings = get_settings_for_source(source)
    if not settings or "mcpServers" not in settings:
        return {}

    servers = settings["mcpServers"]
    if isinstance(servers, dict):
        return servers
    return {}


def has_skip_dangerous_mode_permission_prompt() -> bool:
    """
    True if any trusted settings source accepted bypass-permissions dialog.

    ``projectSettings`` is excluded (TS parity — malicious project RCE risk).
    """
    for source in (
        "userSettings",
        "localSettings",
        "flagSettings",
        "policySettings",
    ):
        s = get_settings_for_source(source) or {}
        if s.get("skipDangerousModePermissionPrompt"):
            return True
    return False


def get_env_from_settings(source: SettingSource) -> dict[str, str]:
    """Get environment variables from settings."""
    settings = get_settings_for_source(source)
    if not settings or "env" not in settings:
        return {}

    env = settings["env"]
    if isinstance(env, dict):
        return {k: str(v) for k, v in env.items()}
    return {}
