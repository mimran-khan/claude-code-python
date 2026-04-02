"""
Parse `git log` pretty-format output into structured records.

Migrated from: utils/gitLogParser.ts (source not present; supports common %H|%an|%ae|%at|%s formats).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class GitLogEntry:
    """One commit line from a formatted git log."""

    sha: str
    author_name: str
    author_email: str
    committed_at: datetime
    subject: str


def parse_git_log_line(line: str, *, delimiter: str = "|") -> GitLogEntry | None:
    """
    Parse a single line from `git log --pretty=format:'%H|%an|%ae|%at|%s'`.

    %at is unix epoch seconds.
    """
    parts = line.strip().split(delimiter, 4)
    if len(parts) < 5:
        return None
    sha, an, ae, at_raw, subject = parts
    try:
        ts = int(at_raw)
        dt = datetime.fromtimestamp(ts, tz=UTC)
    except (ValueError, OSError):
        return None
    if len(sha) not in (40, 64):
        return None
    return GitLogEntry(
        sha=sha,
        author_name=an,
        author_email=ae,
        committed_at=dt,
        subject=subject,
    )


def parse_git_log_output(text: str, *, delimiter: str = "|") -> list[GitLogEntry]:
    """Parse multi-line git log output."""
    out: list[GitLogEntry] = []
    for line in text.splitlines():
        entry = parse_git_log_line(line, delimiter=delimiter)
        if entry:
            out.append(entry)
    return out
