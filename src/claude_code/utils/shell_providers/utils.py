"""
Shell utility functions.

Common shell operations.

Migrated from: utils/shell/shellToolUtils.ts + resolveDefaultShell.ts
"""

from __future__ import annotations

import os
import platform
import shutil

from .provider import ShellType


def resolve_default_shell() -> ShellType:
    """
    Resolve the default shell type for the current platform.

    Returns:
        Default ShellType
    """
    # On Windows, prefer PowerShell
    if platform.system() == "Windows":
        from .powershell_provider import is_powershell_available

        if is_powershell_available():
            return "powershell"

    # Default to bash
    return "bash"


def get_shell_path(shell_type: ShellType) -> str | None:
    """
    Get the path to a shell executable.

    Args:
        shell_type: Type of shell

    Returns:
        Path to shell or None
    """
    if shell_type == "bash":
        return shutil.which("bash")

    if shell_type == "powershell":
        # Try pwsh first (PowerShell Core)
        pwsh = shutil.which("pwsh")
        if pwsh:
            return pwsh
        # Fall back to Windows PowerShell
        return shutil.which("powershell")

    return None


def is_interactive_shell() -> bool:
    """
    Check if running in an interactive shell.

    Returns:
        True if interactive
    """
    # Check for TTY
    import sys

    if not sys.stdin.isatty():
        return False

    # Check common non-interactive indicators
    if os.getenv("CI"):
        return False

    return not os.getenv("CLAUDE_CODE_NON_INTERACTIVE")


def build_shell_command(
    command: str,
    shell_type: ShellType = "bash",
    cwd: str | None = None,
) -> list[str]:
    """
    Build a shell command for subprocess execution.

    Args:
        command: Command to run
        shell_type: Type of shell
        cwd: Working directory (included in command if needed)

    Returns:
        Command arguments for subprocess
    """
    shell_path = get_shell_path(shell_type)
    if not shell_path:
        raise ValueError(f"Shell not found: {shell_type}")

    if shell_type == "bash":
        if cwd:
            command = f'cd "{cwd}" && {command}'
        return [shell_path, "-c", command]

    if shell_type == "powershell":
        if cwd:
            command = f'Set-Location "{cwd}"; {command}'
        return [shell_path, "-NoProfile", "-NonInteractive", "-Command", command]

    return [shell_path, "-c", command]


def escape_shell_arg(arg: str, shell_type: ShellType = "bash") -> str:
    """
    Escape an argument for shell execution.

    Args:
        arg: Argument to escape
        shell_type: Target shell

    Returns:
        Escaped argument
    """
    if shell_type == "bash":
        # Use single quotes, escaping any single quotes in the string
        return "'" + arg.replace("'", "'\\''") + "'"

    if shell_type == "powershell":
        # Use single quotes, doubling any single quotes
        return "'" + arg.replace("'", "''") + "'"

    return arg
