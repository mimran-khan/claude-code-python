"""
Ultraplan keyword detection.

Migrated from: utils/ultraplan/keyword.ts
"""

import re
from dataclasses import dataclass


@dataclass
class TriggerPosition:
    """Position of a trigger keyword."""

    word: str
    start: int
    end: int


OPEN_TO_CLOSE = {
    "`": "`",
    '"': '"',
    "<": ">",
    "{": "}",
    "[": "]",
    "(": ")",
    "'": "'",
}


def _is_word_char(ch: str | None) -> bool:
    """Check if character is a word character."""
    if not ch:
        return False
    return bool(re.match(r"[\w]", ch, re.UNICODE))


def _find_keyword_trigger_positions(text: str, keyword: str) -> list[TriggerPosition]:
    """Find keyword positions, skipping false positives.

    Skips occurrences inside:
    - Paired delimiters (backticks, quotes, brackets, etc.)
    - Path/identifier contexts (preceded/followed by /, \\, -)
    - Followed by ? (questions about the feature)
    - Slash command input
    """
    # Quick check
    pattern = re.compile(keyword, re.IGNORECASE)
    if not pattern.search(text):
        return []

    # Slash commands don't trigger
    if text.startswith("/"):
        return []

    # Find quoted ranges to exclude
    quoted_ranges: list[tuple[int, int]] = []
    open_quote: str | None = None
    open_at = 0

    for i, ch in enumerate(text):
        if open_quote:
            # Handle nested brackets
            if open_quote == "[" and ch == "[":
                open_at = i
                continue

            # Check for closing delimiter
            if ch != OPEN_TO_CLOSE.get(open_quote):
                continue

            # Single quote special case
            if open_quote == "'" and i + 1 < len(text) and _is_word_char(text[i + 1]):
                continue

            quoted_ranges.append((open_at, i + 1))
            open_quote = None

        else:
            # Check for opening delimiter
            if (
                ch == "<"
                and i + 1 < len(text)
                and re.match(r"[a-zA-Z/]", text[i + 1])
                or ch == "'"
                and not _is_word_char(text[i - 1] if i > 0 else None)
                or ch in OPEN_TO_CLOSE
                and ch not in ("<", "'")
            ):
                open_quote = ch
                open_at = i

    # Find word matches
    positions: list[TriggerPosition] = []
    word_re = re.compile(rf"\b{keyword}\b", re.IGNORECASE)

    for match in word_re.finditer(text):
        start = match.start()
        end = match.end()

        # Skip if inside quoted range
        if any(start >= r[0] and start < r[1] for r in quoted_ranges):
            continue

        # Check context
        before = text[start - 1] if start > 0 else None
        after = text[end] if end < len(text) else None

        # Skip path/identifier contexts
        if before in ("/", "\\", "-"):
            continue
        if after in ("/", "\\", "-", "?"):
            continue
        if after == "." and end + 1 < len(text) and _is_word_char(text[end + 1]):
            continue

        positions.append(
            TriggerPosition(
                word=match.group(0),
                start=start,
                end=end,
            )
        )

    return positions


def find_ultraplan_trigger_positions(text: str) -> list[TriggerPosition]:
    """Find ultraplan keyword positions."""
    return _find_keyword_trigger_positions(text, "ultraplan")


def find_ultrareview_trigger_positions(text: str) -> list[TriggerPosition]:
    """Find ultrareview keyword positions."""
    return _find_keyword_trigger_positions(text, "ultrareview")


def has_ultraplan_keyword(text: str) -> bool:
    """Check if text contains triggerable ultraplan keyword."""
    return len(find_ultraplan_trigger_positions(text)) > 0


def has_ultrareview_keyword(text: str) -> bool:
    """Check if text contains triggerable ultrareview keyword."""
    return len(find_ultrareview_trigger_positions(text)) > 0


def replace_ultraplan_keyword(text: str) -> str:
    """Replace first ultraplan with plan.

    "please ultraplan this" -> "please plan this"
    Preserves casing of the "plan" suffix.
    """
    positions = find_ultraplan_trigger_positions(text)
    if not positions:
        return text

    trigger = positions[0]
    before = text[: trigger.start]
    after = text[trigger.end :]

    # Check if result would be empty
    if not (before + after).strip():
        return ""

    # Extract "plan" part with original casing
    plan_part = trigger.word[len("ultra") :]  # "plan", "Plan", etc.

    return before + plan_part + after
