"""
Settings utilities module.

Handles loading, validating, and managing Claude Code settings.

Migrated from: utils/settings/*.ts
"""

from . import change_detector, internal_writes, managed_path, mdm, settings_cache
from .constants import (
    SETTING_SOURCES,
    EditableSettingSource,
    SettingSource,
    get_enabled_setting_sources,
    get_setting_source_display_name_capitalized,
    get_setting_source_display_name_lowercase,
    get_setting_source_name,
    get_source_display_name,
    parse_setting_sources_flag,
)
from .settings import (
    get_merged_settings,
    get_settings_file_path_for_source,
    get_settings_for_source,
    get_settings_root_path_for_source,
    has_skip_dangerous_mode_permission_prompt,
    parse_settings_file,
    reset_settings_cache,
    update_settings_for_source,
)
from .types import (
    HooksSettings,
    McpSettings,
    PermissionsSettings,
    SettingsJson,
)
from .validation import (
    ValidationError,
    format_validation_error,
    validate_settings,
)

__all__ = [
    # types
    "SettingsJson",
    "PermissionsSettings",
    "HooksSettings",
    "McpSettings",
    # constants
    "SETTING_SOURCES",
    "SettingSource",
    "EditableSettingSource",
    "get_setting_source_name",
    "get_source_display_name",
    "get_setting_source_display_name_lowercase",
    "get_setting_source_display_name_capitalized",
    "parse_setting_sources_flag",
    "get_enabled_setting_sources",
    # settings
    "get_merged_settings",
    "get_settings_file_path_for_source",
    "get_settings_root_path_for_source",
    "get_settings_for_source",
    "has_skip_dangerous_mode_permission_prompt",
    "parse_settings_file",
    "update_settings_for_source",
    "reset_settings_cache",
    # validation
    "validate_settings",
    "format_validation_error",
    "ValidationError",
    # batch-5 modules
    "change_detector",
    "internal_writes",
    "managed_path",
    "mdm",
    "settings_cache",
]
