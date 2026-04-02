"""
Utility modules for Claude Code.

This package contains various utility functions and helpers used
throughout the application.
"""

# Core utilities
from .cwd import get_cwd, pwd
from .errors import (
    ClaudeError,
    AbortError,
    ShellError,
    ConfigParseError,
    TelemetrySafeError,
    ToolExecutionError,
    PermissionDeniedError,
    is_abort_error,
    to_error,
    error_message,
    is_enoent,
    is_eacces,
    get_errno_code,
    get_errno_path,
)

# Environment utilities
from .env_utils import (
    get_claude_config_home_dir,
    is_env_truthy,
    is_env_defined_falsy,
    is_bare_mode,
    parse_env_vars,
    get_aws_region,
    get_default_vertex_region,
)

from .env import (
    get_global_claude_file,
    detect_terminal,
    detect_package_managers,
    detect_runtimes,
    is_wsl_environment,
    get_platform as get_platform_type,
    is_darwin,
    is_windows,
    is_linux,
    get_shell,
    is_ci_environment,
)

# Path utilities
from .path_utils import (
    expand_path,
    to_relative_path,
    get_directory_for_path,
    contains_path_traversal,
    sanitize_path,
    normalize_path_for_config_key,
    join_paths,
    get_basename,
    get_dirname,
    get_extension,
    is_absolute,
    is_relative,
)

# File utilities
from .file import (
    MAX_OUTPUT_SIZE,
    path_exists,
    read_file_safe,
    read_file_async,
    write_text_content,
    get_file_modification_time,
    detect_file_encoding,
    detect_line_endings,
    ensure_directory,
    remove_file,
    copy_file,
    move_file,
    get_file_size,
    is_file,
    is_directory,
)

# Format utilities
from .format import (
    format_file_size,
    format_seconds_short,
    format_duration,
    format_number,
    format_tokens,
    format_relative_time,
    format_date,
    format_cost,
    format_percentage,
    truncate_string,
    pluralize,
)

# JSON utilities
from .json_utils import (
    safe_parse_json,
    safe_parse_jsonc,
    parse_jsonl,
    parse_jsonl_file,
    safe_json_stringify,
    extract_json_from_text,
    deep_merge,
    safe_get_nested,
)

# Logging utilities
from .log import (
    log_error,
    log_mcp_error,
    log_mcp_debug,
    get_in_memory_errors,
    get_log_display_title,
    date_to_filename,
)

# Debug utilities
from .debug import (
    is_debug_mode,
    enable_debug_logging,
    is_debug_to_stderr,
    get_debug_file_path,
    log_for_debugging,
    log_ant_error,
)

# Platform utilities
from .platform import (
    get_platform,
    Platform,
    SUPPORTED_PLATFORMS,
    get_wsl_version,
    get_linux_distro_info,
    is_macos,
    is_unix_like,
    get_architecture,
    get_python_version,
    get_os_version,
    get_cpu_count,
)

# Git utilities
from .git import (
    find_git_root,
    find_canonical_git_root,
    get_current_branch,
    get_default_branch,
    get_head_sha,
    get_remote_url,
    is_shallow_clone,
    get_git_status,
    get_staged_files,
    get_modified_files,
    get_untracked_files,
    git_diff,
    git_show,
    git_log,
    is_git_ignored,
    git_add,
    git_commit,
)

# String utilities
from .string_utils import (
    escape_regexp,
    capitalize,
    plural,
    first_line_of,
    count_char_in_string,
    normalize_full_width_digits,
    normalize_full_width_space,
    safe_join_lines,
    EndTruncatingAccumulator,
    HeadTruncatingAccumulator,
    strip_ansi_codes,
    word_wrap,
    indent_text,
    dedent_text,
)

# Array utilities
from .array import (
    intersperse,
    count,
    uniq,
    first,
    last,
    chunk,
    flatten,
    group_by,
    partition,
    find,
    find_index,
    compact,
    take,
    drop,
)

# Shell subprocess execution (module name shell_exec — package ``shell`` is TS shell providers)
from .shell_exec import (
    ExecResult,
    ShellConfig,
    exec_command,
    exec_sync,
    exec_file,
    find_suitable_shell,
    which,
    escape_shell_arg,
    join_shell_args,
)

# API utilities
from .api import (
    SystemPromptBlock,
    normalize_tool_input,
    normalize_tool_input_for_api,
    tool_to_api_schema,
    tools_to_api_schemas,
    build_system_prompt_blocks,
    hash_system_prompt,
    estimate_token_count,
    format_tool_result,
    create_user_message as api_create_user_message,
    create_assistant_message as api_create_assistant_message,
    merge_system_prompts,
)

# Attachment utilities
from .attachments import (
    AttachmentType,
    Attachment,
    FileAttachment,
    ImageAttachment,
    DirectoryAttachment,
    MemoryAttachment,
    TodoAttachment,
    TaskAttachment,
    PlanAttachment,
    McpResourceAttachment,
    HookAttachment,
    memory_header,
    create_file_attachment,
    create_image_attachment,
    create_directory_attachment,
    create_memory_attachment,
    attachment_to_content_block,
    format_attachment_text,
)

# Config utilities
from .config_utils import (
    ProjectConfig,
    GlobalConfig,
    get_claude_config_dir,
    get_global_config_path,
    get_project_config_path,
    get_global_config,
    save_global_config,
    get_current_project_config,
    get_project_config,
    save_current_project_config,
    save_project_config,
    get_memory_path,
    clear_config_cache,
    get_api_key,
    get_model,
)

# Message utilities
from .messages import (
    SystemInitInputs,
    build_system_init_message,
    sdk_compat_tool_name,
    generate_uuid,
    derive_short_message_id,
    create_user_message,
    create_user_interruption_message,
    create_system_message,
    create_assistant_api_error_message,
    create_compact_boundary_message,
    create_microcompact_boundary_message,
    create_tool_use_summary_message,
    create_attachment_message,
    get_messages_after_compact_boundary,
    is_compact_boundary_message,
    get_last_assistant_message,
    get_assistant_message_text,
    normalize_messages_for_api,
    strip_signature_blocks,
    count_tool_use_blocks,
    extract_tool_use_ids,
)

# Sub-modules (lazy loaded to avoid circular imports)
# These are imported as modules, not with from-import to ensure
# proper package structure
from . import permissions
from . import settings
from . import bash
from . import swarm
from . import plugins
from . import model
from . import hooks
from . import telemetry
from . import computer_use
from . import shell_providers
from . import secure_storage
from . import deep_link
from . import suggestions
from . import task
from . import memory
from . import process_input
from . import ultraplan
from . import todo
from . import teleport
from . import sandbox
from . import github
from . import advisor
from . import agent_color_manager
from . import agent_swarms_enabled
from . import auth
from . import auth_portable
from . import base64_utils
from . import binary
from . import browser
from . import bundled_mode
from . import cache_paths
from . import caching
from . import classifier_approvals
from . import classifier_approvals_hook
from . import cleanup
from . import color
from . import commit_attribution
from . import config_constants
from . import compact
from . import completion
from . import config
from . import crypto_shim
from . import error_log_sink
from . import find_executable
from . import git_settings
from . import json_read
from . import keyboard_shortcuts
from . import message_predicates
from . import object_group_by
from . import peer_address
from . import sinks
from . import status_notice_helpers
from . import system_prompt_type
from . import user_agent
from . import with_resolvers
from . import worktree_mode_enabled
from . import command_lifecycle
from . import session_env_vars
from . import auto_mode_denials
from . import immediate_command
from . import extra_usage
from . import zod_to_json_schema
from . import standalone_agent
from . import get_worktree_paths_portable
from . import ink
from . import user_prompt_keywords
from . import words
from . import circular_buffer
from . import stream
from . import content_array

__all__ = [
    # Errors
    "ClaudeError",
    "AbortError",
    "ShellError",
    "ConfigParseError",
    "TelemetrySafeError",
    "is_abort_error",
    "to_error",
    "error_message",
    "is_enoent",
    # Environment
    "get_claude_config_home_dir",
    "is_env_truthy",
    "is_bare_mode",
    "get_platform",
    # Path
    "expand_path",
    "to_relative_path",
    "contains_path_traversal",
    # File
    "path_exists",
    "read_file_safe",
    "write_text_content",
    # Format
    "format_file_size",
    "format_duration",
    "format_number",
    "format_tokens",
    # JSON
    "safe_parse_json",
    "parse_jsonl",
    "safe_json_stringify",
    # Logging
    "log_error",
    "log_for_debugging",
    # Git
    "find_git_root",
    "get_current_branch",
    "get_default_branch",
    "git_diff",
    # String
    "escape_regexp",
    "capitalize",
    "plural",
    # Array
    "intersperse",
    "count",
    "uniq",
    # Shell
    "exec_command",
    "exec_sync",
    "which",
    # Config
    "get_global_config",
    "get_project_config",
    "get_api_key",
    "get_model",
    # Messages
    "SystemInitInputs",
    "build_system_init_message",
    "sdk_compat_tool_name",
    "generate_uuid",
    "create_user_message",
    "create_system_message",
]
