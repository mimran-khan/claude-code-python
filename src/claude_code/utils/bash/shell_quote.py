"""
Shell quoting primitives.

Basic shell quoting using shlex.

Migrated from: utils/bash/shellQuote.ts (~100 lines)
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Any


@dataclass
class ParseResult:
    """Result of parsing a shell command."""

    success: bool
    tokens: list[Any]
    error: str | None = None


def quote(args: list[str]) -> str:
    """
    Quote a list of arguments for safe shell execution.

    Similar to shell-quote's quote function.

    Args:
        args: List of arguments to quote

    Returns:
        Properly quoted command string
    """
    quoted_parts = []

    for arg in args:
        # Special handling for operators
        if arg in ("<", ">", ">>", "|", "&&", "||", ";", "&"):
            quoted_parts.append(arg)
        else:
            quoted_parts.append(shlex.quote(arg))

    return " ".join(quoted_parts)


def try_parse_shell_command(
    command: str,
    env_resolver: Any = None,
) -> ParseResult:
    """
    Try to parse a shell command into tokens.

    Args:
        command: The command to parse
        env_resolver: Optional function to resolve environment variables

    Returns:
        ParseResult with success status and tokens
    """
    try:
        # Use shlex for basic tokenization
        lexer = shlex.shlex(command, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ""  # Don't treat # as comments inside strings

        tokens = list(lexer)

        return ParseResult(
            success=True,
            tokens=tokens,
        )
    except ValueError as e:
        return ParseResult(
            success=False,
            tokens=[],
            error=str(e),
        )


def parse_shell_command(command: str) -> list[str]:
    """
    Parse a shell command into tokens.

    Raises ValueError on parse failure.

    Args:
        command: The command to parse

    Returns:
        List of token strings
    """
    result = try_parse_shell_command(command)
    if not result.success:
        raise ValueError(result.error or "Failed to parse command")
    return result.tokens


def escape_for_double_quotes(s: str) -> str:
    """
    Escape a string for use inside double quotes.

    Args:
        s: String to escape

    Returns:
        Escaped string
    """
    # Escape backslash, double quote, dollar sign, and backtick
    result = s.replace("\\", "\\\\")
    result = result.replace('"', '\\"')
    result = result.replace("$", "\\$")
    result = result.replace("`", "\\`")
    return result


def escape_for_single_quotes(s: str) -> str:
    """
    Escape a string for use inside single quotes.

    Single quotes in shell cannot contain single quotes,
    so we close the string, add an escaped single quote,
    and reopen.

    Args:
        s: String to escape

    Returns:
        Escaped string
    """
    return s.replace("'", "'\"'\"'")


def needs_quoting(s: str) -> bool:
    """
    Check if a string needs quoting for shell safety.

    Args:
        s: String to check

    Returns:
        True if the string needs quoting
    """
    # Metacharacters that need quoting
    metacharacters = set(" \t\n|&;<>()$`\\\"'*?[#~=%")
    return any(c in metacharacters for c in s)
