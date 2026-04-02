"""
Report generation for /insights.

Full TS implementation lives in commands/insights.ts; this module provides
async entry points and dataclasses for Python callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .types import (
    AtAGlance,
    DateRange,
    InsightsPayload,
    RemoteCollectionStats,
    UsageReportData,
)


@dataclass
class GenerateUsageReportOptions:
    collect_remote: bool = False


@dataclass
class GenerateUsageReportResult:
    insights: InsightsPayload
    html_path: str
    data: UsageReportData
    remote_stats: RemoteCollectionStats | None = None


async def generate_usage_report(
    options: GenerateUsageReportOptions | None = None,
) -> GenerateUsageReportResult:
    """
    Build usage analytics (placeholder until session storage is wired in Python).

    Callers should replace this with a full port of `generateUsageReport` from TS.
    """
    _ = options
    tmp_html = Path("/tmp/claude-insights-placeholder.html")
    tmp_html.write_text("<html><body>Insights placeholder</body></html>", encoding="utf-8")
    now = datetime.now(UTC).date().isoformat()
    data = UsageReportData(
        total_sessions=0,
        total_messages=0,
        total_duration_hours=0.0,
        git_commits=0,
        date_range=DateRange(start=now, end=now),
    )
    insights = InsightsPayload(
        at_a_glance=AtAGlance(),
        raw={},
    )
    return GenerateUsageReportResult(
        insights=insights,
        html_path=str(tmp_html.resolve()),
        data=data,
        remote_stats=None,
    )


def get_facets_dir() -> str:
    """Parity stub for facets directory path used in insights prompt."""

    return str(Path.home() / ".claude" / "insights-facets")
