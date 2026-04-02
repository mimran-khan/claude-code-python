"""
Bash Tool (core.tool).

Migrated from: tools/BashTool/*.ts
"""

from .bash_command_helpers import list_compound_subcommands, segment_bash_command
from .bash_security import bash_command_is_safe_async_deprecated, bash_command_is_safe_deprecated
from .bash_tool import (
    DEFAULT_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
    BashTool,
    BashToolOutput,
    execute_bash,
)
from .bash_utils import (
    build_image_tool_result,
    is_image_output,
    parse_data_uri,
    strip_empty_lines,
)
from .command_semantics import CommandResultView, get_command_semantic, interpret_command_result
from .comment_label import extract_bash_comment_label
from .constants import BASH_TOOL_NAME
from .destructive_command_warning import get_destructive_command_warning
from .mode_validation import (
    ModeCheckResult,
    PermissionMode,
    check_permission_mode,
    get_auto_allowed_commands,
)
from .path_validation import (
    PathCommand,
    expand_tilde,
    format_directory_list,
    is_path_allowed,
    resolve_and_check_path,
)

# Legacy helpers (optional); may still be imported by older modules.
from .permissions import check_bash_permissions
from .read_only_validation import bash_segment_appears_read_only, is_read_only_bash_command
from .sed_edit_parser import SedEditInfo, is_sed_in_place_edit, parse_sed_edit_command
from .sed_validation import is_line_printing_command, sed_command_is_allowed_by_allowlist
from .should_use_sandbox import SandboxInput, should_use_sandbox
from .validation import is_safe_bash_command, validate_bash_command

__all__ = [
    "BASH_TOOL_NAME",
    "BashTool",
    "BashToolOutput",
    "DEFAULT_TIMEOUT_MS",
    "MAX_TIMEOUT_MS",
    "CommandResultView",
    "ModeCheckResult",
    "PathCommand",
    "PermissionMode",
    "SandboxInput",
    "SedEditInfo",
    "bash_command_is_safe_async_deprecated",
    "bash_command_is_safe_deprecated",
    "bash_segment_appears_read_only",
    "build_image_tool_result",
    "check_bash_permissions",
    "check_permission_mode",
    "execute_bash",
    "expand_tilde",
    "extract_bash_comment_label",
    "format_directory_list",
    "get_auto_allowed_commands",
    "get_command_semantic",
    "get_destructive_command_warning",
    "interpret_command_result",
    "is_image_output",
    "is_line_printing_command",
    "is_path_allowed",
    "is_read_only_bash_command",
    "is_safe_bash_command",
    "is_sed_in_place_edit",
    "list_compound_subcommands",
    "parse_data_uri",
    "parse_sed_edit_command",
    "resolve_and_check_path",
    "sed_command_is_allowed_by_allowlist",
    "segment_bash_command",
    "should_use_sandbox",
    "strip_empty_lines",
    "validate_bash_command",
]
