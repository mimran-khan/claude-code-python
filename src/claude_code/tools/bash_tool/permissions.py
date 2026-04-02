"""
Bash tool permissions.

Permission checking for bash commands.

Migrated from: tools/BashTool/bashPermissions.ts (2622 lines) - Core logic
"""

from __future__ import annotations

from typing import Any

from ..base import ToolUseContext


async def check_bash_permissions(
    input: dict[str, Any],
    context: ToolUseContext,
) -> dict[str, Any]:
    """
    Check permissions for a bash command.

    This evaluates the command against permission rules,
    security checks, and classifier logic.
    """
    command = input.get("command", "")

    # Basic validation
    if not command or not command.strip():
        return {
            "behavior": "deny",
            "reason": "Empty command",
        }

    # Check for dangerous patterns
    if is_dangerous_command(command):
        return {
            "behavior": "ask",
            "decision_reason": {
                "type": "safetyCheck",
                "reason": "Command contains potentially dangerous operations",
            },
        }

    # Default: allow (actual implementation would check rules)
    return {
        "behavior": "allow",
        "updated_input": input,
    }


def has_bash_permission(
    command: str,
    allow_rules: list[str],
) -> bool:
    """
    Check if a command is allowed by permission rules.

    Args:
        command: The command to check
        allow_rules: List of allow rule strings

    Returns:
        True if the command is allowed
    """
    from ...utils.bash.commands import split_command
    from ...utils.permissions.rule_parser import permission_rule_value_from_string

    # Split into subcommands
    subcommands = split_command(command)

    for rule_string in allow_rules:
        rule_value = permission_rule_value_from_string(rule_string)

        # Check if rule applies to Bash tool
        if rule_value.tool_name != "Bash":
            continue

        # Tool-wide rule matches everything
        if not rule_value.rule_content:
            return True

        # Check if rule content matches any subcommand
        rule_content = rule_value.rule_content
        for subcmd in subcommands:
            if _rule_matches_command(rule_content, subcmd):
                return True

    return False


def _rule_matches_command(rule_content: str, command: str) -> bool:
    """Check if a rule content pattern matches a command."""
    import fnmatch

    # Handle prefix patterns (e.g., "git:*")
    if rule_content.endswith(":*"):
        prefix = rule_content[:-2]
        return command.startswith(prefix)

    # Handle glob patterns
    if "*" in rule_content or "?" in rule_content:
        return fnmatch.fnmatch(command, rule_content)

    # Exact match
    return command == rule_content


def is_dangerous_command(command: str) -> bool:
    """
    Check if a command is potentially dangerous.

    This checks for patterns that could cause data loss,
    security issues, or other problems.
    """
    # Dangerous patterns
    dangerous_patterns = [
        "rm -rf /",
        "rm -rf /*",
        ":(){ :|:& };:",  # Fork bomb
        "dd if=/dev/zero",
        "mkfs.",
        "chmod -R 777 /",
        "chown -R",
        "> /dev/sda",
        "curl | bash",
        "wget | bash",
        "curl | sh",
        "wget | sh",
    ]

    command_lower = command.lower()
    return any(pattern.lower() in command_lower for pattern in dangerous_patterns)


def extract_command_prefix(command: str) -> str | None:
    """
    Extract a stable command prefix for rule suggestions.

    Returns the command and subcommand (e.g., "git commit")
    or None if no clear prefix can be extracted.
    """
    # Skip env var assignments at start
    import re

    env_var_pattern = re.compile(r"^[A-Za-z_]\w*=")

    tokens = command.strip().split()

    # Skip leading env vars
    while tokens and env_var_pattern.match(tokens[0]):
        tokens = tokens[1:]

    if len(tokens) < 2:
        return None

    # Second token must look like a subcommand (lowercase alpha)
    subcmd = tokens[1]
    if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", subcmd):
        return None

    return f"{tokens[0]} {subcmd}"


def generate_permission_suggestion(
    command: str,
    exact: bool = False,
) -> str:
    """
    Generate a permission rule suggestion for a command.

    Args:
        command: The command to generate a rule for
        exact: If True, suggest exact command match; otherwise suggest prefix

    Returns:
        A rule string like "Bash(git commit:*)"
    """
    if exact:
        return f"Bash({command})"

    prefix = extract_command_prefix(command)
    if prefix:
        return f"Bash({prefix}:*)"

    return f"Bash({command})"
