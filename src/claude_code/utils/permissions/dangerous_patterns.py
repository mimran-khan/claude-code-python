"""
Dangerous pattern lists for shell-tool allow-rule prefixes.

An allow rule like `Bash(python:*)` or `PowerShell(node:*)` lets the model
run arbitrary code via that interpreter, bypassing the auto-mode classifier.
These lists feed the is_dangerous_bash_permission and related predicates.

Migrated from: utils/permissions/dangerousPatterns.ts (81 lines)
"""

from __future__ import annotations

import os

# Cross-platform code-execution entry points present on both Unix and Windows
CROSS_PLATFORM_CODE_EXEC = [
    # Interpreters
    "python",
    "python3",
    "python2",
    "node",
    "deno",
    "tsx",
    "ruby",
    "perl",
    "php",
    "lua",
    # Package runners
    "npx",
    "bunx",
    "npm run",
    "yarn run",
    "pnpm run",
    "bun run",
    # Shells reachable from both (Git Bash / WSL on Windows, native on Unix)
    "bash",
    "sh",
    # Remote arbitrary-command wrapper (native OpenSSH on Win10+)
    "ssh",
]


def get_dangerous_bash_patterns() -> list[str]:
    """
    Get the list of dangerous bash patterns.

    These patterns represent commands that can execute arbitrary code
    and should not be auto-allowed.
    """
    patterns = [
        *CROSS_PLATFORM_CODE_EXEC,
        "zsh",
        "fish",
        "eval",
        "exec",
        "env",
        "xargs",
        "sudo",
    ]

    # Additional patterns for internal use
    if os.getenv("USER_TYPE") == "ant":
        patterns.extend(
            [
                "fa run",
                "coo",
                "gh",
                "gh api",
                "curl",
                "wget",
                "git",
                "kubectl",
                "aws",
                "gcloud",
                "gsutil",
            ]
        )

    return patterns


def get_dangerous_powershell_patterns() -> list[str]:
    """
    Get the list of dangerous PowerShell patterns.

    These patterns represent commands that can execute arbitrary code
    and should not be auto-allowed.
    """
    return [
        *CROSS_PLATFORM_CODE_EXEC,
        # PowerShell-specific
        "powershell",
        "pwsh",
        "Invoke-Expression",
        "iex",
        "Invoke-Command",
        "icm",
        "Start-Process",
        "Invoke-WebRequest",
        "iwr",
        "Invoke-RestMethod",
        "irm",
    ]


def is_dangerous_bash_permission(rule_content: str | None) -> bool:
    """
    Check if a bash permission rule content represents a dangerous pattern.

    Args:
        rule_content: The content part of a permission rule

    Returns:
        True if the pattern is dangerous
    """
    if not rule_content:
        return False

    dangerous_patterns = get_dangerous_bash_patterns()
    rule_lower = rule_content.lower()

    for pattern in dangerous_patterns:
        pattern_lower = pattern.lower()

        # Exact match
        if rule_lower == pattern_lower:
            return True

        # Pattern with wildcard suffix
        if rule_lower.startswith(pattern_lower + ":"):
            return True
        if rule_lower.startswith(pattern_lower + " "):
            return True
        if rule_lower == pattern_lower + "*":
            return True

    return False


def is_dangerous_powershell_permission(rule_content: str | None) -> bool:
    """
    Check if a PowerShell permission rule content represents a dangerous pattern.

    Args:
        rule_content: The content part of a permission rule

    Returns:
        True if the pattern is dangerous
    """
    if not rule_content:
        return False

    dangerous_patterns = get_dangerous_powershell_patterns()
    rule_lower = rule_content.lower()

    for pattern in dangerous_patterns:
        pattern_lower = pattern.lower()

        # Exact match
        if rule_lower == pattern_lower:
            return True

        # Pattern with wildcard suffix
        if rule_lower.startswith(pattern_lower + ":"):
            return True
        if rule_lower.startswith(pattern_lower + " "):
            return True
        if rule_lower == pattern_lower + "*":
            return True

    return False
