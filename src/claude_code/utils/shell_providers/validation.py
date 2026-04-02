"""
Shell command validation.

Validate commands for read-only mode.

Migrated from: utils/shell/readOnlyCommandValidation.ts
"""

from __future__ import annotations

import re

# Patterns that indicate potentially destructive commands
DANGEROUS_PATTERNS = [
    # File operations
    r"\brm\b",
    r"\brmdir\b",
    r"\bmv\b",
    r"\bcp\b",
    r"\bmkdir\b",
    r"\btouch\b",
    r"\bchmod\b",
    r"\bchown\b",
    # Editors/writers
    r"\bvim?\b",
    r"\bnano\b",
    r"\bemacs\b",
    r"\bed\b",
    r"\btee\b",
    # Redirections
    r">",
    r">>",
    # Git modifications
    r"\bgit\s+(push|commit|merge|rebase|reset|checkout|add|rm|mv)",
    r"\bgit\s+branch\s+-[dD]",
    # Package managers
    r"\bnpm\s+(install|uninstall|update|publish)",
    r"\bpip\s+(install|uninstall)",
    r"\bbrew\s+(install|uninstall|upgrade)",
    r"\bapt(-get)?\s+(install|remove|purge)",
    r"\byum\s+(install|remove|erase)",
    # System commands
    r"\bsudo\b",
    r"\bsu\b",
    r"\bkill\b",
    r"\bpkill\b",
    r"\bshutdown\b",
    r"\breboot\b",
    # Database modifications
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bTRUNCATE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bCREATE\b",
]

# Safe read-only commands
SAFE_PATTERNS = [
    r"^\s*ls\b",
    r"^\s*cat\b",
    r"^\s*head\b",
    r"^\s*tail\b",
    r"^\s*grep\b",
    r"^\s*find\b",
    r"^\s*which\b",
    r"^\s*whereis\b",
    r"^\s*pwd\b",
    r"^\s*echo\b",
    r"^\s*date\b",
    r"^\s*whoami\b",
    r"^\s*hostname\b",
    r"^\s*uname\b",
    r"^\s*env\b",
    r"^\s*printenv\b",
    r"^\s*wc\b",
    r"^\s*sort\b",
    r"^\s*uniq\b",
    r"^\s*diff\b",
    r"^\s*file\b",
    r"^\s*stat\b",
    r"^\s*du\b",
    r"^\s*df\b",
    r"^\s*ps\b",
    r"^\s*top\b",
    r"^\s*htop\b",
    r"^\s*git\s+(status|log|diff|show|branch|tag|remote|fetch)\b",
    r"^\s*npm\s+(list|ls|view|info|search)\b",
    r"^\s*pip\s+(list|show|freeze)\b",
]


def get_dangerous_patterns() -> list[str]:
    """Get list of dangerous command patterns."""
    return DANGEROUS_PATTERNS.copy()


def is_safe_readonly_command(command: str) -> bool:
    """
    Check if a command is safe for read-only mode.

    Args:
        command: Command to check

    Returns:
        True if safe
    """
    command = command.strip()

    # Check if it matches a safe pattern
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Still check for dangerous patterns in piped commands
            if "|" in command:
                parts = command.split("|")
                # Check subsequent parts for dangerous commands
                for part in parts[1:]:
                    for danger in DANGEROUS_PATTERNS:
                        if re.search(danger, part, re.IGNORECASE):
                            return False
            return True

    return False


def validate_readonly_command(command: str) -> tuple[bool, str | None]:
    """
    Validate a command for read-only mode.

    Args:
        command: Command to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    command = command.strip()

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            return False, f"Command contains restricted pattern: {match.group()}"

    return True, None


def sanitize_command_for_logging(command: str) -> str:
    """
    Sanitize a command for logging (remove sensitive info).

    Args:
        command: Command to sanitize

    Returns:
        Sanitized command
    """
    # Redact common sensitive patterns
    sanitized = command

    # API keys
    sanitized = re.sub(
        r"(api[_-]?key|token|password|secret)[=:]\s*['\"]?[\w-]+['\"]?",
        r"\1=[REDACTED]",
        sanitized,
        flags=re.IGNORECASE,
    )

    # Authorization headers
    sanitized = re.sub(
        r"(Authorization|Bearer)\s*[:\s]+\S+",
        r"\1: [REDACTED]",
        sanitized,
        flags=re.IGNORECASE,
    )

    return sanitized
