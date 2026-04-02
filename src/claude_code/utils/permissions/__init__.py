"""
Permission utilities module.

Handles permission checking, rules, modes, and filesystem access control.

Migrated from: utils/permissions/*.ts
"""

from .bash_classifier import (
    PROMPT_PREFIX,
    ClassifierBehavior,
    ClassifierResult,
    classify_bash_command,
    is_classifier_permissions_enabled,
)
from .dangerous_patterns import (
    CROSS_PLATFORM_CODE_EXEC,
    get_dangerous_bash_patterns,
    get_dangerous_powershell_patterns,
    is_dangerous_bash_permission,
    is_dangerous_powershell_permission,
)
from .denial_tracking import (
    DENIAL_LIMITS,
    DenialLimits,
    DenialTrackingState,
    create_denial_tracking_state,
    record_denial,
    record_success,
    should_fallback_to_prompting,
)
from .filesystem import (
    DANGEROUS_DIRECTORIES,
    DANGEROUS_FILES,
    get_file_read_ignore_patterns,
    is_claude_settings_path,
    is_dangerous_directory,
    is_dangerous_file,
    matching_rule_for_input,
    normalize_case_for_comparison,
    normalize_patterns_to_path,
    path_in_allowed_working_path,
    path_in_working_path,
)
from .path_validation import (
    FileOperationType,
    PathCheckResult,
    ResolvedPathCheckResult,
    expand_tilde,
    format_directory_list,
    get_glob_base_directory,
    is_path_allowed,
    resolve_and_check_path,
)
from .permission_mode import (
    EXTERNAL_PERMISSION_MODES,
    PERMISSION_MODES,
    ExternalPermissionMode,
    PermissionMode,
    is_external_permission_mode,
    permission_mode_color,
    permission_mode_symbol,
    permission_mode_title,
)
from .permission_result import (
    PermissionAllowDecision,
    PermissionAskDecision,
    PermissionDecision,
    PermissionDenyDecision,
    PermissionResult,
)
from .permission_rule import (
    PermissionBehavior,
    PermissionRule,
    PermissionRuleSource,
    PermissionRuleValue,
    get_rule_behavior_description,
)
from .permissions import (
    check_tool_permission,
    create_permission_request_message,
    format_permission_rules_for_display,
    get_allow_rules,
    get_ask_rules,
    get_deny_rules,
)
from .permissions_loader import (
    add_permission_rule_to_settings,
    delete_permission_rule_from_settings,
    get_permission_rules_for_source,
    load_all_permission_rules_from_disk,
    should_allow_managed_permission_rules_only,
    should_show_always_allow_options,
)
from .rule_parser import (
    escape_rule_content,
    get_legacy_tool_names,
    normalize_legacy_tool_name,
    permission_rule_value_from_string,
    permission_rule_value_to_string,
    unescape_rule_content,
)

__all__ = [
    # permission_mode
    "PermissionMode",
    "ExternalPermissionMode",
    "PERMISSION_MODES",
    "EXTERNAL_PERMISSION_MODES",
    "permission_mode_title",
    "permission_mode_symbol",
    "permission_mode_color",
    "is_external_permission_mode",
    # permission_rule
    "PermissionBehavior",
    "PermissionRule",
    "PermissionRuleValue",
    "PermissionRuleSource",
    "get_rule_behavior_description",
    # permission_result
    "PermissionAllowDecision",
    "PermissionAskDecision",
    "PermissionDenyDecision",
    "PermissionDecision",
    "PermissionResult",
    # rule_parser
    "escape_rule_content",
    "unescape_rule_content",
    "permission_rule_value_from_string",
    "permission_rule_value_to_string",
    "normalize_legacy_tool_name",
    "get_legacy_tool_names",
    # filesystem
    "DANGEROUS_FILES",
    "DANGEROUS_DIRECTORIES",
    "normalize_case_for_comparison",
    "is_claude_settings_path",
    "is_dangerous_file",
    "is_dangerous_directory",
    "path_in_working_path",
    "path_in_allowed_working_path",
    "matching_rule_for_input",
    "get_file_read_ignore_patterns",
    "normalize_patterns_to_path",
    # permissions
    "check_tool_permission",
    "get_allow_rules",
    "get_deny_rules",
    "get_ask_rules",
    "create_permission_request_message",
    "format_permission_rules_for_display",
    # permissions_loader
    "load_all_permission_rules_from_disk",
    "get_permission_rules_for_source",
    "should_allow_managed_permission_rules_only",
    "should_show_always_allow_options",
    "add_permission_rule_to_settings",
    "delete_permission_rule_from_settings",
    # path_validation
    "PathCheckResult",
    "ResolvedPathCheckResult",
    "FileOperationType",
    "is_path_allowed",
    "resolve_and_check_path",
    "format_directory_list",
    "get_glob_base_directory",
    "expand_tilde",
    # denial_tracking
    "DenialTrackingState",
    "DenialLimits",
    "DENIAL_LIMITS",
    "create_denial_tracking_state",
    "record_denial",
    "record_success",
    "should_fallback_to_prompting",
    # dangerous_patterns
    "CROSS_PLATFORM_CODE_EXEC",
    "get_dangerous_bash_patterns",
    "get_dangerous_powershell_patterns",
    "is_dangerous_bash_permission",
    "is_dangerous_powershell_permission",
    # bash_classifier
    "ClassifierResult",
    "ClassifierBehavior",
    "PROMPT_PREFIX",
    "is_classifier_permissions_enabled",
    "classify_bash_command",
]
