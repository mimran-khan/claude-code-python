"""
Brief chat timestamp labels (migrated from ``utils/formatBriefTimestamp.ts``).

Uses local wall-clock semantics; POSIX ``LC_*`` tags are mapped to a BCP-47 tag
when valid (for future locale-aware formatting). Display uses fixed English
patterns equivalent to the TS scales (same calendar day / within 6 days / older).
"""

from __future__ import annotations

import os
import re
from datetime import datetime


def _parse_iso(iso_string: str) -> datetime | None:
    s = iso_string.strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _to_naive_local(d: datetime) -> datetime:
    if d.tzinfo is not None:
        return d.astimezone().replace(tzinfo=None)
    return d


def _start_of_day(d: datetime) -> datetime:
    return datetime(d.year, d.month, d.day)


def _fmt_time_12h(d: datetime) -> str:
    h12 = d.hour % 12 or 12
    ampm = "AM" if d.hour < 12 else "PM"
    return f"{h12}:{d.minute:02d} {ampm}"


def locale_tag_from_env() -> str | None:
    """Derive BCP-47 tag from ``LC_ALL`` / ``LC_TIME`` / ``LANG`` (TS parity)."""
    raw = os.environ.get("LC_ALL") or os.environ.get("LC_TIME") or os.environ.get("LANG") or ""
    if not raw or raw in ("C", "POSIX"):
        return None
    base = raw.split(".")[0].split("@")[0]
    if not base:
        return None
    tag = base.replace("_", "-")
    if re.fullmatch(r"[A-Za-z]{2,3}(-[A-Za-z0-9]+)*", tag):
        return tag
    return None


def format_brief_timestamp(iso_string: str, now: datetime | None = None) -> str:
    d = _parse_iso(iso_string)
    if d is None:
        return ""
    d_local = _to_naive_local(d)
    now_local = _to_naive_local(now) if now else datetime.now()

    day_diff = (_start_of_day(now_local) - _start_of_day(d_local)).total_seconds()
    days_ago = round(day_diff / 86_400.0)

    if days_ago == 0:
        return _fmt_time_12h(d_local)
    if 0 < days_ago < 7:
        return f"{d_local:%A}, {_fmt_time_12h(d_local)}"
    return f"{d_local:%A, %b %d}, {_fmt_time_12h(d_local)}"


__all__ = ["format_brief_timestamp", "locale_tag_from_env"]
