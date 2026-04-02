"""
String utilities.

Functions for string manipulation and formatting.

Migrated from: utils/stringUtils.ts (236 lines)
"""

from __future__ import annotations

import re

MAX_STRING_LENGTH = 2**25  # ~32MB


def escape_regexp(s: str) -> str:
    """
    Escape special regex characters in a string.

    Allows the string to be used as a literal pattern in a regex.
    """
    return re.escape(s)


def capitalize(s: str) -> str:
    """
    Uppercase the first character of a string, leaving the rest unchanged.

    Unlike Python's str.capitalize(), this does NOT lowercase
    the remaining characters.

    Examples:
        capitalize('fooBar') → 'FooBar'
        capitalize('hello world') → 'Hello world'
    """
    if not s:
        return s
    return s[0].upper() + s[1:]


def plural(n: int, word: str, plural_word: str | None = None) -> str:
    """
    Return the singular or plural form of a word based on count.

    Args:
        n: Count
        word: Singular form
        plural_word: Plural form (defaults to word + 's')

    Returns:
        The appropriate form
    """
    if plural_word is None:
        plural_word = word + "s"
    return word if n == 1 else plural_word


def first_line_of(s: str) -> str:
    """
    Return the first line of a string without allocating a split array.
    """
    nl = s.find("\n")
    return s if nl == -1 else s[:nl]


def count_char_in_string(s: str, char: str, start: int = 0) -> int:
    """
    Count occurrences of a character in a string.
    """
    return s.count(char, start)


def normalize_full_width_digits(s: str) -> str:
    """
    Normalize full-width (zenkaku) digits to half-width digits.

    Useful for accepting input from Japanese/CJK IMEs.
    """
    result = []
    for ch in s:
        code = ord(ch)
        if 0xFF10 <= code <= 0xFF19:  # ０-９
            result.append(chr(code - 0xFEE0))
        else:
            result.append(ch)
    return "".join(result)


def normalize_full_width_space(s: str) -> str:
    """
    Normalize full-width space to half-width space.

    U+3000 → U+0020
    """
    return s.replace("\u3000", " ")


def safe_join_lines(
    lines: list[str],
    delimiter: str = ",",
    max_size: int = MAX_STRING_LENGTH,
) -> str:
    """
    Safely join an array of strings with a delimiter, truncating if needed.

    Args:
        lines: List of strings to join
        delimiter: Delimiter between strings
        max_size: Maximum size of the result

    Returns:
        The joined string, truncated if necessary
    """
    truncation_marker = "...[truncated]"
    result = ""

    for line in lines:
        delimiter_to_add = delimiter if result else ""
        full_addition = delimiter_to_add + line

        if len(result) + len(full_addition) <= max_size:
            result += full_addition
        else:
            remaining = max_size - len(result) - len(delimiter_to_add) - len(truncation_marker)

            if remaining > 0:
                result += delimiter_to_add + line[:remaining] + truncation_marker
            else:
                result += truncation_marker
            return result

    return result


class EndTruncatingAccumulator:
    """
    A string accumulator that truncates from the end when size limit is exceeded.

    Preserves the beginning of the output.
    """

    def __init__(self, max_size: int = MAX_STRING_LENGTH):
        self._content = ""
        self._is_truncated = False
        self._total_bytes_received = 0
        self._max_size = max_size

    def append(self, text: str) -> None:
        """Append text to the accumulator."""
        self._total_bytes_received += len(text)

        if self._is_truncated:
            return

        remaining = self._max_size - len(self._content)
        if len(text) <= remaining:
            self._content += text
        else:
            self._content += text[:remaining]
            self._is_truncated = True

    @property
    def content(self) -> str:
        """Get the accumulated content."""
        return self._content

    @property
    def is_truncated(self) -> bool:
        """Check if content was truncated."""
        return self._is_truncated

    @property
    def total_bytes_received(self) -> int:
        """Get total bytes received before truncation."""
        return self._total_bytes_received

    def clear(self) -> None:
        """Reset the accumulator."""
        self._content = ""
        self._is_truncated = False
        self._total_bytes_received = 0


class HeadTruncatingAccumulator:
    """
    A string accumulator that truncates from the beginning when size limit is exceeded.

    Preserves the end of the output.
    """

    def __init__(self, max_size: int = MAX_STRING_LENGTH):
        self._content = ""
        self._is_truncated = False
        self._total_bytes_received = 0
        self._max_size = max_size

    def append(self, text: str) -> None:
        """Append text to the accumulator."""
        self._total_bytes_received += len(text)

        new_content = self._content + text
        if len(new_content) > self._max_size:
            excess = len(new_content) - self._max_size
            new_content = new_content[excess:]
            self._is_truncated = True

        self._content = new_content

    @property
    def content(self) -> str:
        """Get the accumulated content."""
        return self._content

    @property
    def is_truncated(self) -> bool:
        """Check if content was truncated."""
        return self._is_truncated

    @property
    def total_bytes_received(self) -> int:
        """Get total bytes received before truncation."""
        return self._total_bytes_received

    def clear(self) -> None:
        """Reset the accumulator."""
        self._content = ""
        self._is_truncated = False
        self._total_bytes_received = 0


def strip_ansi_codes(s: str) -> str:
    """Remove ANSI escape codes from a string."""
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    return ansi_pattern.sub("", s)


def word_wrap(text: str, width: int = 80) -> str:
    """Wrap text to a specified width."""
    import textwrap

    return "\n".join(textwrap.wrap(text, width=width))


def indent_text(text: str, prefix: str = "  ") -> str:
    """Indent each line of text with a prefix."""
    return "\n".join(prefix + line for line in text.split("\n"))


def dedent_text(text: str) -> str:
    """Remove common leading whitespace from each line."""
    import textwrap

    return textwrap.dedent(text)
