"""Cleanup result types and filename date parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CleanupResult:
    messages: int = 0
    errors: int = 0


def add_cleanup_results(a: CleanupResult, b: CleanupResult) -> CleanupResult:
    return CleanupResult(messages=a.messages + b.messages, errors=a.errors + b.errors)


_ts_re = re.compile(r"T(\d{2})-(\d{2})-(\d{2})-(\d{3})Z")


def convert_file_name_to_date(filename: str) -> object:
    """Parse log-style filenames into a datetime-compatible value (ISO subset)."""
    from datetime import datetime

    base = filename.split(".")[0]
    iso_str = _ts_re.sub(r"T\1:\2:\3.\4Z", base)
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min
