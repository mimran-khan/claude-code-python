"""
Bash command parsing utilities.

Functions for splitting and analyzing bash commands.

Migrated from: utils/bash/commands.ts (1340 lines) - Core logic
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass

# Control operators that separate commands
CONTROL_OPERATORS = {";", "&&", "||", "|", "&", "|&"}

# File descriptors for standard streams
ALLOWED_FILE_DESCRIPTORS = {"0", "1", "2"}


@dataclass
class OutputRedirection:
    """Represents an output redirection in a bash command."""

    operator: str
    target: str
    fd: str | None = None


@dataclass
class ExtractedRedirections:
    """Result of extracting redirections from a command."""

    command_without_redirections: str
    redirections: list[OutputRedirection]


def generate_placeholders() -> dict[str, str]:
    """
    Generate placeholder strings with random salt to prevent injection attacks.

    The salt prevents malicious commands from containing literal placeholder
    strings that would be replaced during parsing.
    """
    salt = secrets.token_hex(8)
    return {
        "SINGLE_QUOTE": f"__SINGLE_QUOTE_{salt}__",
        "DOUBLE_QUOTE": f"__DOUBLE_QUOTE_{salt}__",
        "NEW_LINE": f"__NEW_LINE_{salt}__",
        "ESCAPED_OPEN_PAREN": f"__ESCAPED_OPEN_PAREN_{salt}__",
        "ESCAPED_CLOSE_PAREN": f"__ESCAPED_CLOSE_PAREN_{salt}__",
    }


def is_static_redirect_target(target: str) -> bool:
    """
    Check if a redirection target is a simple static file path.

    Returns False for targets containing dynamic content (variables,
    command substitutions, globs, shell expansions).
    """
    # Reject targets with whitespace or quotes
    if re.search(r'[\s\'"]', target):
        return False

    # Reject empty string
    if len(target) == 0:
        return False

    # Reject comment-prefixed targets
    if target.startswith("#"):
        return False

    # Reject various dynamic patterns
    if (
        target.startswith("!")  # History expansion
        or target.startswith("=")  # Zsh equals expansion
        or "$" in target  # Variables
        or "`" in target  # Command substitution
        or "*" in target  # Glob patterns
        or "?" in target  # Single-char glob
        or "[" in target  # Character class glob
        or "{" in target  # Brace expansion
        or "~" in target  # Tilde expansion
        or "(" in target  # Process substitution
        or "<" in target  # Process substitution
        or target.startswith("&")  # File descriptor
    ):
        return False

    return True


def is_control_operator(s: str) -> bool:
    """Check if a string is a control operator."""
    return s in CONTROL_OPERATORS


def split_command_with_operators(command: str) -> list[str]:
    """
    Split a bash command into parts by control operators.

    Handles heredocs, quoted strings, and continuation lines.
    Returns a list of command parts.
    """
    # Handle empty or whitespace-only commands
    if not command or not command.strip():
        return []

    # Generate unique placeholders
    placeholders = generate_placeholders()

    # Handle line continuations (odd number of backslashes before newline)
    def handle_continuation(match: re.Match) -> str:
        backslash_count = len(match.group(0)) - 1  # -1 for newline
        if backslash_count % 2 == 1:
            # Odd: line continuation - remove backslash+newline
            return "\\" * (backslash_count - 1)
        else:
            # Even: keep the newline as separator
            return match.group(0)

    processed_command = re.sub(r"\\+\n", handle_continuation, command)

    # Simple tokenization using shlex-like logic
    parts = _tokenize_command(processed_command, placeholders)

    # Restore placeholders
    result = []
    for part in parts:
        if part:
            restored = (
                part.replace(placeholders["SINGLE_QUOTE"], "'")
                .replace(placeholders["DOUBLE_QUOTE"], '"')
                .replace(placeholders["NEW_LINE"], "\n")
                .replace(placeholders["ESCAPED_OPEN_PAREN"], "\\(")
                .replace(placeholders["ESCAPED_CLOSE_PAREN"], "\\)")
            )
            result.append(restored)

    return result


def _tokenize_command(command: str, placeholders: dict[str, str]) -> list[str]:
    """Tokenize a command into parts separated by control operators."""
    parts: list[str] = []
    current = ""
    i = 0
    n = len(command)

    while i < n:
        char = command[i]

        # Handle quotes
        if char in "\"'":
            quote_char = char
            current += char
            i += 1
            while i < n and command[i] != quote_char:
                if command[i] == "\\" and i + 1 < n:
                    current += command[i : i + 2]
                    i += 2
                else:
                    current += command[i]
                    i += 1
            if i < n:
                current += command[i]
                i += 1
            continue

        # Check for control operators
        two_char = command[i : i + 2] if i + 1 < n else ""
        if two_char in ("&&", "||", "|&"):
            if current.strip():
                parts.append(current.strip())
            parts.append(two_char)
            current = ""
            i += 2
            continue

        if char in ";|&":
            if current.strip():
                parts.append(current.strip())
            parts.append(char)
            current = ""
            i += 1
            continue

        # Handle newlines as separators
        if char == "\n":
            if current.strip():
                parts.append(current.strip())
            current = ""
            i += 1
            continue

        current += char
        i += 1

    # Add final part
    if current.strip():
        parts.append(current.strip())

    # Filter to just command parts (not operators)
    result = []
    for part in parts:
        if part and not is_control_operator(part):
            result.append(part)

    return result


def split_command(command: str) -> list[str]:
    """
    Split a command string into individual commands.

    Unlike split_command_with_operators, this returns only the
    command strings without the operators.
    """
    parts = split_command_with_operators(command)
    return [p for p in parts if p and not is_control_operator(p)]


def extract_output_redirections(command: str) -> ExtractedRedirections:
    """
    Extract output redirections from a bash command.

    Returns the command without redirections and a list of the
    extracted redirections.
    """
    redirections: list[OutputRedirection] = []

    # Pattern to match output redirections
    # Matches: >, >>, &>, &>>, 1>, 2>, etc.
    redirect_pattern = re.compile(r"(\d?)(&?>>?)\s*([^\s;|&><]+)")

    def extract_redirection(match: re.Match) -> str:
        fd = match.group(1) or None
        operator = match.group(2)
        target = match.group(3)

        # Only extract static targets
        if is_static_redirect_target(target):
            redirections.append(
                OutputRedirection(
                    operator=operator,
                    target=target,
                    fd=fd,
                )
            )
            return ""
        else:
            # Keep dynamic redirections in command
            return match.group(0)

    command_without = redirect_pattern.sub(extract_redirection, command)

    # Clean up extra whitespace
    command_without = re.sub(r"\s+", " ", command_without).strip()

    return ExtractedRedirections(
        command_without_redirections=command_without,
        redirections=redirections,
    )


def get_first_command(command: str) -> str:
    """Get the first command from a potentially compound command."""
    parts = split_command(command)
    return parts[0] if parts else command


def get_command_name(command: str) -> str | None:
    """
    Extract the command name from a command string.

    Returns None if no command name can be extracted.
    """
    # Skip leading variable assignments
    parts = command.split()
    for part in parts:
        if "=" in part and not part.startswith("="):
            continue
        # This part is the command name
        return part
    return None


def is_pipeline(command: str) -> bool:
    """Check if a command is a pipeline."""
    return "|" in split_command_with_operators(command)


def count_commands(command: str) -> int:
    """Count the number of commands in a compound command."""
    return len(split_command(command))
