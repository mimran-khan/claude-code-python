"""
Permission rules loader.

Functions for loading and managing permission rules from settings files.

Migrated from: utils/permissions/permissionsLoader.ts (297 lines)
"""

from __future__ import annotations

import json
import os
from typing import Any

from ..json_utils import safe_parse_json
from ..log import log_error
from .permission_rule import (
    PermissionBehavior,
    PermissionRule,
    PermissionRuleSource,
)
from .rule_parser import (
    permission_rule_value_from_string,
    permission_rule_value_to_string,
)

# Setting sources
SETTING_SOURCES = [
    "policySettings",
    "flagSettings",
    "userSettings",
    "projectSettings",
    "localSettings",
]

# Editable sources (user can modify)
EDITABLE_SOURCES = [
    "userSettings",
    "projectSettings",
    "localSettings",
]

SUPPORTED_RULE_BEHAVIORS = ["allow", "deny", "ask"]


def should_allow_managed_permission_rules_only() -> bool:
    """
    Check if only managed permission rules should be allowed.

    When enabled, only permission rules from managed settings are respected.
    """
    # This would check the policySettings
    # For now, return False as the default
    return False


def should_show_always_allow_options() -> bool:
    """
    Check if 'always allow' options should be shown in permission prompts.

    Hidden when allowManagedPermissionRulesOnly is enabled.
    """
    return not should_allow_managed_permission_rules_only()


def get_settings_file_path_for_source(source: str) -> str | None:
    """Get the file path for a settings source."""
    from ..cwd import get_cwd
    from ..env_utils import get_claude_config_home_dir

    cwd = get_cwd()
    config_home = get_claude_config_home_dir()

    paths = {
        "userSettings": os.path.join(config_home, "settings.json"),
        "projectSettings": os.path.join(cwd, ".claude", "settings.json"),
        "localSettings": os.path.join(cwd, ".claude", "settings.local.json"),
        "policySettings": os.path.join(config_home, "settings.policy.json"),
        "flagSettings": os.path.join(config_home, "settings.flags.json"),
    }

    return paths.get(source)


def get_settings_for_source(source: str) -> dict[str, Any] | None:
    """Load and parse settings from a source file."""
    file_path = get_settings_file_path_for_source(source)
    if not file_path:
        return None

    try:
        if not os.path.isfile(file_path):
            return None

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        if content.strip() == "":
            return {}

        data = safe_parse_json(content, should_log_error=False)
        return data if isinstance(data, dict) else None
    except Exception as e:
        log_error(e)
        return None


def settings_json_to_rules(
    data: dict[str, Any] | None,
    source: PermissionRuleSource,
) -> list[PermissionRule]:
    """Convert settings JSON to permission rules."""
    if not data or "permissions" not in data:
        return []

    permissions = data["permissions"]
    if not isinstance(permissions, dict):
        return []

    rules: list[PermissionRule] = []

    for behavior in SUPPORTED_RULE_BEHAVIORS:
        behavior_array = permissions.get(behavior, [])
        if isinstance(behavior_array, list):
            for rule_string in behavior_array:
                if isinstance(rule_string, str):
                    rules.append(
                        PermissionRule(
                            source=source,
                            rule_behavior=behavior,  # type: ignore
                            rule_value=permission_rule_value_from_string(rule_string),
                        )
                    )

    return rules


def load_all_permission_rules_from_disk() -> list[PermissionRule]:
    """Load all permission rules from all relevant sources."""
    # If managed rules only mode, just use policy settings
    if should_allow_managed_permission_rules_only():
        return get_permission_rules_for_source("policySettings")

    # Otherwise, load from all sources
    rules: list[PermissionRule] = []

    for source in SETTING_SOURCES:
        rules.extend(get_permission_rules_for_source(source))

    return rules


def get_permission_rules_for_source(source: str) -> list[PermissionRule]:
    """Load permission rules from a specific source."""
    settings_data = get_settings_for_source(source)
    return settings_json_to_rules(settings_data, source)  # type: ignore


def delete_permission_rule_from_settings(
    rule: PermissionRule,
) -> bool:
    """
    Delete a rule from settings.

    Args:
        rule: The rule to delete

    Returns:
        True if the rule was deleted, False otherwise
    """
    # Only allow deleting from editable sources
    if rule.source not in EDITABLE_SOURCES:
        return False

    rule_string = permission_rule_value_to_string(rule.rule_value)
    settings_data = get_settings_for_source(rule.source)

    if not settings_data or "permissions" not in settings_data:
        return False

    permissions = settings_data["permissions"]
    if not isinstance(permissions, dict):
        return False

    behavior_array = permissions.get(rule.rule_behavior, [])
    if not isinstance(behavior_array, list):
        return False

    # Normalize entries for comparison
    def normalize_entry(raw: str) -> str:
        return permission_rule_value_to_string(permission_rule_value_from_string(raw))

    if not any(normalize_entry(raw) == rule_string for raw in behavior_array):
        return False

    try:
        # Update the settings
        updated_permissions = {
            **permissions,
            rule.rule_behavior: [raw for raw in behavior_array if normalize_entry(raw) != rule_string],
        }

        file_path = get_settings_file_path_for_source(rule.source)
        if not file_path:
            return False

        updated_data = {
            **settings_data,
            "permissions": updated_permissions,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2)

        return True
    except Exception as e:
        log_error(e)
        return False


def add_permission_rule_to_settings(
    source: str,
    behavior: PermissionBehavior,
    rule_string: str,
) -> bool:
    """
    Add a rule to settings.

    Args:
        source: The settings source to add to
        behavior: The permission behavior
        rule_string: The rule string to add

    Returns:
        True if the rule was added, False otherwise
    """
    if source not in EDITABLE_SOURCES:
        return False

    file_path = get_settings_file_path_for_source(source)
    if not file_path:
        return False

    try:
        # Load existing settings
        settings_data = get_settings_for_source(source) or {}
        permissions = settings_data.get("permissions", {})

        if not isinstance(permissions, dict):
            permissions = {}

        # Get or create the behavior array
        behavior_array = permissions.get(behavior, [])
        if not isinstance(behavior_array, list):
            behavior_array = []

        # Check if rule already exists
        if rule_string in behavior_array:
            return True

        # Add the rule
        behavior_array.append(rule_string)

        # Update settings
        updated_permissions = {
            **permissions,
            behavior: behavior_array,
        }

        updated_data = {
            **settings_data,
            "permissions": updated_permissions,
        }

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2)

        return True
    except Exception as e:
        log_error(e)
        return False
