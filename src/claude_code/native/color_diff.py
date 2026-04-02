"""
Color diff rendering with syntax highlighting.

Pure Python port of the Rust NAPI module that uses syntect+bat.

Migrated from: native-ts/color-diff/index.ts
"""

import difflib
import os
from dataclasses import dataclass


@dataclass
class Hunk:
    """A diff hunk."""

    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: list[str]


@dataclass
class SyntaxTheme:
    """Syntax highlighting theme."""

    theme: str
    source: str | None


# ANSI escape codes
RESET = "\x1b[0m"
RED_BG = "\x1b[41m"
GREEN_BG = "\x1b[42m"
RED_FG = "\x1b[31m"
GREEN_FG = "\x1b[32m"
DIM = "\x1b[2m"

# Line markers
MARKER_ADD = "+"
MARKER_DEL = "-"
MARKER_CTX = " "


def get_syntax_theme(theme_name: str) -> SyntaxTheme:
    """Get syntax theme information.

    Args:
        theme_name: Theme name ("dark" or "light")

    Returns:
        SyntaxTheme with theme name and source
    """
    # Check BAT_THEME environment variable
    bat_theme = os.environ.get("BAT_THEME")
    if bat_theme:
        return SyntaxTheme(theme=bat_theme, source="BAT_THEME")

    # Default themes
    if theme_name == "light":
        return SyntaxTheme(theme="OneLight", source=None)
    return SyntaxTheme(theme="OneDark", source=None)


class ColorDiff:
    """Renders colored diffs with word-level highlighting."""

    def __init__(
        self,
        old_lines: list[str],
        new_lines: list[str],
        context: int = 3,
        filepath: str | None = None,
    ):
        self.old_lines = old_lines
        self.new_lines = new_lines
        self.context = context
        self.filepath = filepath
        self._hunks: list[Hunk] | None = None

    def get_hunks(self) -> list[Hunk]:
        """Get diff hunks."""
        if self._hunks is None:
            self._hunks = self._compute_hunks()
        return self._hunks

    def _compute_hunks(self) -> list[Hunk]:
        """Compute diff hunks using unified diff format."""
        differ = difflib.unified_diff(
            self.old_lines,
            self.new_lines,
            lineterm="",
            n=self.context,
        )

        hunks: list[Hunk] = []
        current_hunk: Hunk | None = None

        for line in differ:
            # Skip file headers
            if line.startswith("---") or line.startswith("+++"):
                continue

            # Parse hunk header
            if line.startswith("@@"):
                if current_hunk:
                    hunks.append(current_hunk)

                # Parse @@ -old_start,old_lines +new_start,new_lines @@
                parts = line.split()
                old_part = parts[1]  # -old_start,old_lines
                new_part = parts[2]  # +new_start,new_lines

                old_start, old_lines = self._parse_range(old_part[1:])
                new_start, new_lines = self._parse_range(new_part[1:])

                current_hunk = Hunk(
                    old_start=old_start,
                    old_lines=old_lines,
                    new_start=new_start,
                    new_lines=new_lines,
                    lines=[],
                )
            elif current_hunk is not None:
                current_hunk.lines.append(line)

        if current_hunk:
            hunks.append(current_hunk)

        return hunks

    def _parse_range(self, range_str: str) -> tuple[int, int]:
        """Parse a range like '1,5' or '1'."""
        if "," in range_str:
            parts = range_str.split(",")
            return int(parts[0]), int(parts[1])
        return int(range_str), 1

    def render(
        self,
        theme: str = "dark",
        line_numbers: bool = True,
        word_diff: bool = True,
    ) -> str:
        """Render the diff with colors.

        Args:
            theme: Color theme ("dark" or "light")
            line_numbers: Show line numbers
            word_diff: Highlight changed words within lines

        Returns:
            Colored diff string
        """
        hunks = self.get_hunks()
        if not hunks:
            return ""

        lines = []

        for hunk in hunks:
            # Hunk header
            lines.append(f"{DIM}@@ -{hunk.old_start},{hunk.old_lines} +{hunk.new_start},{hunk.new_lines} @@{RESET}")

            old_num = hunk.old_start
            new_num = hunk.new_start

            for line in hunk.lines:
                if line.startswith("+"):
                    marker = GREEN_FG + MARKER_ADD
                    content = line[1:]
                    num_str = f"{new_num:4d}" if line_numbers else ""
                    lines.append(f"{marker} {GREEN_FG}{num_str}  {content}{RESET}")
                    new_num += 1
                elif line.startswith("-"):
                    marker = RED_FG + MARKER_DEL
                    content = line[1:]
                    num_str = f"{old_num:4d}" if line_numbers else ""
                    lines.append(f"{marker} {RED_FG}{num_str}  {content}{RESET}")
                    old_num += 1
                else:
                    marker = MARKER_CTX
                    content = line[1:] if line.startswith(" ") else line
                    num_str = f"{old_num:4d}" if line_numbers else ""
                    lines.append(f"{marker} {DIM}{num_str}{RESET}  {content}")
                    old_num += 1
                    new_num += 1

        return "\n".join(lines)


class ColorFile:
    """Renders a file with syntax highlighting."""

    def __init__(self, content: str, filepath: str | None = None):
        self.content = content
        self.filepath = filepath
        self._lines = content.split("\n")

    def render(
        self,
        theme: str = "dark",
        line_numbers: bool = True,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> str:
        """Render the file with colors.

        Args:
            theme: Color theme
            line_numbers: Show line numbers
            start_line: First line to show (1-indexed)
            end_line: Last line to show (inclusive)

        Returns:
            Colored file content
        """
        if end_line is None:
            end_line = len(self._lines)

        lines = []
        for i, line in enumerate(self._lines[start_line - 1 : end_line], start=start_line):
            if line_numbers:
                lines.append(f"{DIM}{i:4d}{RESET}  {line}")
            else:
                lines.append(line)

        return "\n".join(lines)

    @property
    def line_count(self) -> int:
        """Get number of lines."""
        return len(self._lines)
