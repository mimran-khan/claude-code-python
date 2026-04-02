"""
String Utilities.

Helper functions for string manipulation.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def truncate(
    text: str,
    max_length: int,
    *,
    suffix: str = "...",
    break_on_word: bool = True,
) -> str:
    """Truncate text to a maximum length.

    Args:
        text: The text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated
        break_on_word: If True, break at word boundaries

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    target_length = max_length - len(suffix)

    if target_length <= 0:
        return suffix[:max_length]

    if break_on_word:
        # Find the last space before the target length
        truncated = text[:target_length]
        last_space = truncated.rfind(" ")

        if last_space > target_length // 2:
            truncated = truncated[:last_space]

        return truncated.rstrip() + suffix

    return text[:target_length] + suffix


def plural(count: int, singular: str, plural_form: str | None = None) -> str:
    """Return singular or plural form based on count.

    Args:
        count: The count
        singular: Singular form
        plural_form: Plural form (defaults to singular + 's')

    Returns:
        Appropriate form for the count
    """
    if count == 1:
        return f"{count} {singular}"

    return f"{count} {plural_form or singular + 's'}"


def capitalize(text: str) -> str:
    """Capitalize the first letter of text.

    Args:
        text: The text to capitalize

    Returns:
        Text with first letter capitalized
    """
    if not text:
        return text
    return text[0].upper() + text[1:]


def to_snake_case(text: str) -> str:
    """Convert text to snake_case.

    Args:
        text: The text to convert

    Returns:
        Text in snake_case
    """
    # Handle camelCase and PascalCase
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    text = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", text)

    # Handle hyphens and spaces
    text = text.replace("-", "_").replace(" ", "_")

    return text.lower()


def to_camel_case(text: str) -> str:
    """Convert text to camelCase.

    Args:
        text: The text to convert

    Returns:
        Text in camelCase
    """
    # Split on underscores, hyphens, and spaces
    words = re.split(r"[_\-\s]+", text)

    if not words:
        return text

    # First word stays lowercase, rest are capitalized
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def to_pascal_case(text: str) -> str:
    """Convert text to PascalCase.

    Args:
        text: The text to convert

    Returns:
        Text in PascalCase
    """
    # Split on underscores, hyphens, and spaces
    words = re.split(r"[_\-\s]+", text)
    return "".join(w.capitalize() for w in words)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text.

    Args:
        text: The text to process

    Returns:
        Text with ANSI codes removed
    """
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_pattern.sub("", text)


def indent(text: str, prefix: str = "  ") -> str:
    """Indent each line of text.

    Args:
        text: The text to indent
        prefix: Prefix to add to each line

    Returns:
        Indented text
    """
    lines = text.split("\n")
    return "\n".join(prefix + line if line else line for line in lines)


def dedent(text: str) -> str:
    """Remove common leading whitespace from lines.

    Args:
        text: The text to dedent

    Returns:
        Dedented text
    """
    import textwrap

    return textwrap.dedent(text)


def wrap(text: str, width: int = 80) -> str:
    """Wrap text to specified width.

    Args:
        text: The text to wrap
        width: Maximum line width

    Returns:
        Wrapped text
    """
    import textwrap

    return textwrap.fill(text, width=width)


def escape_xml(text: str) -> str:
    """Escape XML special characters.

    Args:
        text: The text to escape

    Returns:
        Text with XML special characters escaped
    """
    replacements = [
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        ('"', "&quot;"),
        ("'", "&apos;"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def unescape_xml(text: str) -> str:
    """Unescape XML special characters.

    Args:
        text: The text to unescape

    Returns:
        Text with XML entities expanded
    """
    replacements = [
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
        ("&apos;", "'"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def split_lines(text: str, *, keep_ends: bool = False) -> list[str]:
    """Split text into lines.

    Args:
        text: The text to split
        keep_ends: If True, keep line endings

    Returns:
        List of lines
    """
    if keep_ends:
        return text.splitlines(keepends=True)
    return text.splitlines()


def join_lines(lines: Sequence[str], *, ending: str = "\n") -> str:
    """Join lines with a line ending.

    Args:
        lines: Lines to join
        ending: Line ending to use

    Returns:
        Joined text
    """
    return ending.join(lines)


def is_empty_or_whitespace(text: str) -> bool:
    """Check if text is empty or only whitespace.

    Args:
        text: The text to check

    Returns:
        True if empty or whitespace only
    """
    return not text or text.isspace()
