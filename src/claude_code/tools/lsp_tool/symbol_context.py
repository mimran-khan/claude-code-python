"""
Extract the symbol/word at a cursor position in a source file.

Migrated from: tools/LSPTool/symbolContext.ts
"""

from __future__ import annotations

import re
from pathlib import Path

from ...utils.debug import log_for_debugging
from ...utils.path_utils import expand_path
from ...utils.strings import truncate

_MAX_READ_BYTES = 64 * 1024
_SYMBOL_PATTERN = re.compile(r"[\w$'!]+|[+\-*/%&|^~<>=]+")


def get_symbol_at_position(file_path: str, line: int, character: int) -> str | None:
    """
    Return the token at (line, character), 0-indexed, or None.

    Reads at most the first 64 KiB; if the target line is past that window, returns None.
    """
    try:
        absolute = expand_path(file_path)
        path = Path(absolute)
        with path.open("rb") as f:
            chunk = f.read(_MAX_READ_BYTES)
        content = chunk.decode("utf-8", errors="replace")
        lines = content.split("\n")

        if line < 0 or line >= len(lines):
            return None
        if len(chunk) == _MAX_READ_BYTES and line == len(lines) - 1:
            return None

        line_content = lines[line]
        if character < 0 or character >= len(line_content):
            return None

        for match in _SYMBOL_PATTERN.finditer(line_content):
            start, end = match.start(), match.end()
            if start <= character < end:
                return truncate(match.group(0), 30, break_on_word=False)
        return None
    except OSError as e:
        log_for_debugging(
            f"Symbol extraction failed for {file_path}:{line}:{character}: {e}",
            level="warn",
        )
        return None
    except Exception as e:
        log_for_debugging(
            f"Symbol extraction failed for {file_path}:{line}:{character}: {e!s}",
            level="warn",
        )
        return None


__all__ = ["get_symbol_at_position"]
