"""
Shell utilities.

Shell command execution and provider management.

Migrated from: utils/shell/*.ts (10 files)
"""

from .bash_provider import (
    BashProvider,
    create_bash_provider,
)
from .powershell_provider import (
    PowerShellProvider,
    create_powershell_provider,
)
from .provider import (
    DEFAULT_HOOK_SHELL,
    SHELL_TYPES,
    ShellProvider,
    ShellType,
    get_shell_provider,
)
from .utils import (
    build_shell_command,
    get_shell_path,
    is_interactive_shell,
    resolve_default_shell,
)
from .validation import (
    get_dangerous_patterns,
    is_safe_readonly_command,
    validate_readonly_command,
)

__all__ = [
    # Provider
    "ShellType",
    "SHELL_TYPES",
    "DEFAULT_HOOK_SHELL",
    "ShellProvider",
    "get_shell_provider",
    # Bash
    "BashProvider",
    "create_bash_provider",
    # PowerShell
    "PowerShellProvider",
    "create_powershell_provider",
    # Utils
    "resolve_default_shell",
    "get_shell_path",
    "is_interactive_shell",
    "build_shell_command",
    # Validation
    "validate_readonly_command",
    "is_safe_readonly_command",
    "get_dangerous_patterns",
]
