"""
Bash command validation.

Validation and security checks for bash commands.

Migrated from: tools/BashTool/bashSecurity.ts + modeValidation.ts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of command validation."""

    is_valid: bool
    is_safe: bool
    message: str | None = None
    warnings: list[str] | None = None


def validate_bash_command(command: str) -> ValidationResult:
    """
    Validate a bash command.

    Returns validation result indicating if the command is valid
    and safe to execute.
    """
    if not command or not command.strip():
        return ValidationResult(
            is_valid=False,
            is_safe=False,
            message="Command cannot be empty",
        )

    # Check for common issues
    warnings = []

    # Check for very long commands
    if len(command) > 10000:
        return ValidationResult(
            is_valid=False,
            is_safe=False,
            message="Command exceeds maximum length",
        )

    # Check for potential issues
    if "rm -rf" in command:
        warnings.append("Contains recursive delete - use with caution")

    if "sudo" in command:
        warnings.append("Contains sudo - may require password")

    # Check if it's safe
    is_safe = is_safe_bash_command(command)

    return ValidationResult(
        is_valid=True,
        is_safe=is_safe,
        warnings=warnings if warnings else None,
    )


def is_safe_bash_command(command: str) -> bool:
    """
    Check if a bash command is safe for auto-execution.

    Returns True if the command is considered safe.
    """
    # List of clearly safe commands
    safe_prefixes = [
        "echo ",
        "cat ",
        "ls ",
        "pwd",
        "cd ",
        "head ",
        "tail ",
        "wc ",
        "grep ",
        "find ",
        "which ",
        "type ",
        "file ",
        "date",
        "whoami",
        "hostname",
        "uname",
    ]

    command_lower = command.lower().strip()

    for prefix in safe_prefixes:
        if command_lower.startswith(prefix):
            return True

    # Check for read-only git commands
    if command_lower.startswith("git "):
        read_only_git = [
            "git status",
            "git log",
            "git diff",
            "git show",
            "git branch",
            "git tag",
            "git remote",
            "git config --get",
            "git rev-parse",
        ]
        for git_cmd in read_only_git:
            if command_lower.startswith(git_cmd):
                return True

    return False


def check_read_only_command(command: str) -> bool:
    """
    Check if a command is a read-only command.

    Read-only commands don't modify the filesystem or state.
    """
    read_only_commands = {
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "ls",
        "dir",
        "pwd",
        "cd",
        "echo",
        "printf",
        "grep",
        "egrep",
        "fgrep",
        "find",
        "locate",
        "which",
        "whereis",
        "type",
        "file",
        "stat",
        "wc",
        "du",
        "df",
        "date",
        "cal",
        "uptime",
        "who",
        "w",
        "whoami",
        "hostname",
        "uname",
        "arch",
        "env",
        "printenv",
        "set",
        "ps",
        "top",
        "htop",
        "pgrep",
        "id",
        "groups",
    }

    # Get first word of command
    first_word = command.strip().split()[0] if command.strip() else ""

    # Strip path if present
    if "/" in first_word:
        first_word = first_word.rsplit("/", 1)[-1]

    return first_word in read_only_commands


def extract_write_targets(command: str) -> list[str]:
    """
    Extract potential write targets from a command.

    Returns a list of paths that may be written to.
    """
    targets = []

    # Look for output redirections
    import re

    # Match > and >> redirections
    redirect_pattern = re.compile(r"(?:>>?)\s*([^\s;|&]+)")

    for match in redirect_pattern.finditer(command):
        target = match.group(1)
        if target and not target.startswith("&"):
            targets.append(target)

    return targets
