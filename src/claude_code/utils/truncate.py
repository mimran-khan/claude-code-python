"""
Truncation Utilities.

Width-aware truncation and wrapping functions.
"""

from __future__ import annotations

from .string_width import string_width


def truncate_to_width(text: str, max_width: int) -> str:
    """Truncate a string to fit within a maximum display width.

    Appends '…' when truncation occurs.

    Args:
        text: The string to truncate
        max_width: Maximum display width in terminal columns

    Returns:
        The truncated string with ellipsis if needed
    """
    if string_width(text) <= max_width:
        return text
    if max_width <= 1:
        return "…"

    width = 0
    result = []
    for char in text:
        char_width = string_width(char)
        if width + char_width > max_width - 1:
            break
        result.append(char)
        width += char_width

    return "".join(result) + "…"


def truncate_start_to_width(text: str, max_width: int) -> str:
    """Truncate from the start of a string, keeping the tail end.

    Prepends '…' when truncation occurs.

    Args:
        text: The string to truncate
        max_width: Maximum display width in terminal columns

    Returns:
        The truncated string with ellipsis if needed
    """
    if string_width(text) <= max_width:
        return text
    if max_width <= 1:
        return "…"

    chars = list(text)
    width = 0
    start_idx = len(chars)

    for i in range(len(chars) - 1, -1, -1):
        char_width = string_width(chars[i])
        if width + char_width > max_width - 1:
            break
        width += char_width
        start_idx = i

    return "…" + "".join(chars[start_idx:])


def truncate_to_width_no_ellipsis(text: str, max_width: int) -> str:
    """Truncate a string to fit within a maximum display width.

    Does not append ellipsis. Useful when caller adds its own separator.

    Args:
        text: The string to truncate
        max_width: Maximum display width in terminal columns

    Returns:
        The truncated string
    """
    if string_width(text) <= max_width:
        return text
    if max_width <= 0:
        return ""

    width = 0
    result = []
    for char in text:
        char_width = string_width(char)
        if width + char_width > max_width:
            break
        result.append(char)
        width += char_width

    return "".join(result)


def truncate_path_middle(path: str, max_length: int) -> str:
    """Truncate a file path in the middle to preserve directory and filename.

    For example: "src/components/deeply/nested/folder/MyComponent.tsx"
    becomes "src/components/…/MyComponent.tsx" when max_length is 30.

    Args:
        path: The file path to truncate
        max_length: Maximum display width in terminal columns

    Returns:
        The truncated path, or original if it fits
    """
    if string_width(path) <= max_length:
        return path

    if max_length <= 0:
        return "…"

    if max_length < 5:
        return truncate_to_width(path, max_length)

    # Find the filename (last path segment)
    last_slash = path.rfind("/")
    if last_slash >= 0:
        filename = path[last_slash:]
        directory = path[:last_slash]
    else:
        filename = path
        directory = ""

    filename_width = string_width(filename)

    # If filename alone is too long, truncate from start
    if filename_width >= max_length - 1:
        return truncate_start_to_width(path, max_length)

    # Calculate space available for directory prefix
    available_for_dir = max_length - 1 - filename_width

    if available_for_dir <= 0:
        return truncate_start_to_width(filename, max_length)

    truncated_dir = truncate_to_width_no_ellipsis(directory, available_for_dir)
    return truncated_dir + "…" + filename


def truncate(
    text: str,
    max_width: int,
    single_line: bool = False,
) -> str:
    """Truncate a string to fit within a maximum display width.

    Args:
        text: The string to truncate
        max_width: Maximum display width in terminal columns
        single_line: If True, also truncate at first newline

    Returns:
        The truncated string with ellipsis if needed
    """
    result = text

    if single_line:
        first_newline = text.find("\n")
        if first_newline != -1:
            result = text[:first_newline]
            if string_width(result) + 1 > max_width:
                return truncate_to_width(result, max_width)
            return f"{result}…"

    if string_width(result) <= max_width:
        return result

    return truncate_to_width(result, max_width)


def wrap_text(text: str, width: int) -> list[str]:
    """Wrap text to fit within a maximum display width.

    Args:
        text: The text to wrap
        width: Maximum display width per line

    Returns:
        List of wrapped lines
    """
    lines = []
    current_line = []
    current_width = 0

    for char in text:
        char_width = string_width(char)
        if current_width + char_width <= width:
            current_line.append(char)
            current_width += char_width
        else:
            if current_line:
                lines.append("".join(current_line))
            current_line = [char]
            current_width = char_width

    if current_line:
        lines.append("".join(current_line))

    return lines
