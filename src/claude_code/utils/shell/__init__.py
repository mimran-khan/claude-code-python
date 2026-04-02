"""
Shell provider utilities (Bash / PowerShell).

Migrated from: ``ClaudeCodeLeaked/utils/shell/*.ts``

Top-level ``utils/Shell.ts`` execution helpers live in
:mod:`claude_code.utils.shell_exec` (import that module for ``exec`` / cwd helpers).
"""

from __future__ import annotations

from .bash_provider import BashProvider, create_bash_shell_provider
from .output_limits import (
    BASH_MAX_OUTPUT_DEFAULT,
    BASH_MAX_OUTPUT_UPPER_LIMIT,
    get_max_output_length,
)
from .powershell_detection import (
    PowerShellEdition,
    find_powershell,
    get_cached_powershell_path,
    get_cached_powershell_path_sync,
    get_powershell_edition,
    reset_powershell_cache,
)
from .powershell_provider import (
    PowerShellProvider,
    build_powershell_args,
    create_powershell_provider,
)
from .prefix import (
    CommandPrefixResult,
    CommandSubcommandPrefixResult,
    PrefixExtractorConfig,
    create_command_prefix_extractor,
    create_subcommand_prefix_extractor,
)
from .read_only_validation import (
    DOCKER_READ_ONLY_COMMANDS,
    EXTERNAL_READONLY_COMMANDS,
    FLAG_PATTERN,
    GH_READ_ONLY_COMMANDS,
    GIT_READ_ONLY_COMMANDS,
    PYRIGHT_READ_ONLY_COMMANDS,
    RIPGREP_READ_ONLY_COMMANDS,
    ExternalCommandConfig,
    FlagArgType,
    contains_vulnerable_unc_path,
    validate_flag_argument,
    validate_flags,
)
from .resolve_default_shell import resolve_default_shell
from .shell_provider import (
    DEFAULT_HOOK_SHELL,
    SHELL_TYPES,
    ExecBuildResult,
    ExecCommandOpts,
    ShellProvider,
    ShellType,
)
from .shell_tool_utils import (
    SHELL_TOOL_NAMES,
    is_powershell_tool_enabled,
    run_shell_provider_command,
)
from .spec_prefix import DEPTH_RULES, build_prefix

__all__ = [
    "BASH_MAX_OUTPUT_DEFAULT",
    "BASH_MAX_OUTPUT_UPPER_LIMIT",
    "BashProvider",
    "CommandPrefixResult",
    "CommandSubcommandPrefixResult",
    "DEFAULT_HOOK_SHELL",
    "DEPTH_RULES",
    "DOCKER_READ_ONLY_COMMANDS",
    "ExecBuildResult",
    "ExecCommandOpts",
    "EXTERNAL_READONLY_COMMANDS",
    "ExternalCommandConfig",
    "FLAG_PATTERN",
    "FlagArgType",
    "GH_READ_ONLY_COMMANDS",
    "GIT_READ_ONLY_COMMANDS",
    "PowerShellEdition",
    "PowerShellProvider",
    "PrefixExtractorConfig",
    "PYRIGHT_READ_ONLY_COMMANDS",
    "RIPGREP_READ_ONLY_COMMANDS",
    "SHELL_TOOL_NAMES",
    "SHELL_TYPES",
    "ShellProvider",
    "ShellType",
    "build_powershell_args",
    "build_prefix",
    "contains_vulnerable_unc_path",
    "create_bash_shell_provider",
    "create_command_prefix_extractor",
    "create_powershell_provider",
    "create_subcommand_prefix_extractor",
    "find_powershell",
    "get_cached_powershell_path",
    "get_cached_powershell_path_sync",
    "get_max_output_length",
    "get_powershell_edition",
    "is_powershell_tool_enabled",
    "reset_powershell_cache",
    "resolve_default_shell",
    "run_shell_provider_command",
    "validate_flag_argument",
    "validate_flags",
]
