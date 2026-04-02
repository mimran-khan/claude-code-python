"""Common constants and utilities."""

import os
from datetime import datetime
from functools import cache


def get_local_iso_date() -> str:
    """Get the local date in ISO format (YYYY-MM-DD).

    Checks for CLAUDE_CODE_OVERRIDE_DATE environment variable first.
    """
    override = os.environ.get("CLAUDE_CODE_OVERRIDE_DATE")
    if override:
        return override

    now = datetime.now()
    return now.strftime("%Y-%m-%d")


@cache
def get_session_start_date() -> str:
    """Get the session start date (memoized for prompt-cache stability).

    Captures the date once at session start.
    """
    return get_local_iso_date()


def get_local_month_year() -> str:
    """Get 'Month YYYY' (e.g., 'February 2026') in user's local timezone.

    Changes monthly, not daily — used in tool prompts to minimize cache busting.
    """
    override = os.environ.get("CLAUDE_CODE_OVERRIDE_DATE")
    date = datetime.fromisoformat(override) if override else datetime.now()
    return date.strftime("%B %Y")
