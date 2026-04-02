"""Types for /insights usage reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AtAGlance:
    """High-level summary block for the insights prompt."""

    pass


@dataclass
class DateRange:
    start: str = ""
    end: str = ""


@dataclass
class InsightsPayload:
    at_a_glance: AtAGlance = field(default_factory=AtAGlance)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class RemoteHostStat:
    name: str = ""
    session_count: int = 0


@dataclass
class RemoteCollectionStats:
    total_copied: int = 0
    hosts: list[RemoteHostStat] = field(default_factory=list)


@dataclass
class UsageReportData:
    total_sessions: int = 0
    total_sessions_scanned: int = 0
    total_messages: int = 0
    total_duration_hours: float = 0.0
    git_commits: int = 0
    date_range: DateRange = field(default_factory=DateRange)
