"""
Shell quoting utilities.

Functions for properly quoting shell commands.

Migrated from: utils/bash/shellQuoting.ts (129 lines)
"""

from __future__ import annotations

import re

from .shell_quote import quote


def contains_heredoc(command: str) -> bool:
    """
    Detect if a command contains a heredoc pattern.

    Matches patterns like: <<EOF, <<'EOF', <<"EOF", <<-EOF, etc.
    """
    # Check for bit-shift operators first and exclude them
    if (
        re.search(r"\d\s*<<\s*\d", command)
        or re.search(r"\[\[\s*\d+\s*<<\s*\d+\s*\]\]", command)
        or re.search(r"\$\(\(.*<<.*\)\)", command)
    ):
        return False

    # Check for heredoc patterns
    heredoc_regex = re.compile(r"<<-?\s*(?:(['\"]?)(\w+)\1|\\(\w+))")
    return bool(heredoc_regex.search(command))


def contains_multiline_string(command: str) -> bool:
    """Detect if a command contains multiline strings in quotes."""
    # Check for strings with actual newlines
    single_quote_multiline = re.compile(r"'(?:[^'\\]|\\.)*\n(?:[^'\\]|\\.)*'")
    double_quote_multiline = re.compile(r'"(?:[^"\\]|\\.)*\n(?:[^"\\]|\\.)*"')

    return bool(single_quote_multiline.search(command) or double_quote_multiline.search(command))


def quote_shell_command(
    command: str,
    add_stdin_redirect: bool = True,
) -> str:
    """
    Quote a shell command appropriately.

    Preserves heredocs and multiline strings.

    Args:
        command: The command to quote
        add_stdin_redirect: Whether to add < /dev/null

    Returns:
        The properly quoted command
    """
    # Handle heredocs and multiline strings specially
    if contains_heredoc(command) or contains_multiline_string(command):
        # For heredocs and multiline strings, use single quotes
        # and escape only single quotes in the command
        escaped = command.replace("'", "'\"'\"'")
        quoted = f"'{escaped}'"

        # Don't add stdin redirect for heredocs
        if contains_heredoc(command):
            return quoted

        # For multiline strings without heredocs, add stdin redirect if needed
        return f"{quoted} < /dev/null" if add_stdin_redirect else quoted

    # For regular commands, use shell quoting
    if add_stdin_redirect:
        return quote([command, "<", "/dev/null"])

    return quote([command])


def has_stdin_redirect(command: str) -> bool:
    """
    Detect if a command already has a stdin redirect.

    Matches patterns like: < file, </path/to/file, < /dev/null
    But not <<EOF (heredoc) or <( (process substitution)
    """
    # Look for < followed by whitespace and a filename/path
    # Negative lookahead to exclude: <<, <(
    pattern = re.compile(r"(?:^|[\s;&|])<(?![<(])\s*\S+")
    return bool(pattern.search(command))


def should_add_stdin_redirect(command: str) -> bool:
    """
    Check if stdin redirect should be added to a command.

    Returns True if stdin redirect can be safely added.
    """
    # Don't add stdin redirect for heredocs
    if contains_heredoc(command):
        return False

    # Don't add if command already has one
    if has_stdin_redirect(command):
        return False

    # For other commands, stdin redirect is generally safe
    return True


# Pattern to match Windows CMD-style >nul redirects
NUL_REDIRECT_REGEX = re.compile(r"(\d?&?>+\s*)[Nn][Uu][Ll](?=\s|$|[|&;)\n])")


def rewrite_windows_null_redirect(command: str) -> str:
    """
    Rewrite Windows CMD-style >nul redirects to POSIX /dev/null.

    The model occasionally hallucinates Windows CMD syntax even though
    our bash shell is always POSIX. This prevents creation of literal
    files named "nul" which are problematic on Windows.

    Matches: >nul, > NUL, 2>nul, &>nul, >>nul (case-insensitive)
    Does NOT match: >null, >nullable, >nul.txt
    """
    return NUL_REDIRECT_REGEX.sub(r"\1/dev/null", command)
