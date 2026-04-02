"""
API usage tracking.

Track API usage and rate limits.

Migrated from: services/api/usage.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class RateLimit:
    """Rate limit information."""

    utilization: float | None = None  # Percentage 0-100
    resets_at: str | None = None  # ISO 8601 timestamp


@dataclass
class ExtraUsage:
    """Extra usage credits information."""

    is_enabled: bool = False
    monthly_limit: float | None = None
    used_credits: float | None = None
    utilization: float | None = None


@dataclass
class Utilization:
    """Usage utilization information."""

    five_hour: RateLimit | None = None
    seven_day: RateLimit | None = None
    seven_day_oauth_apps: RateLimit | None = None
    seven_day_opus: RateLimit | None = None
    seven_day_sonnet: RateLimit | None = None
    extra_usage: ExtraUsage | None = None


async def fetch_utilization() -> Utilization | None:
    """
    Fetch current usage utilization.

    Returns:
        Utilization data or None
    """
    # Requires OAuth
    access_token = os.getenv("CLAUDE_AI_ACCESS_TOKEN")
    if not access_token:
        return None

    try:
        import httpx

        base_url = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com")
        url = f"{base_url}/api/oauth/usage"

        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                data = response.json()
                return _parse_utilization(data)
    except Exception:
        pass

    return None


def _parse_utilization(data: dict[str, Any]) -> Utilization:
    """Parse utilization response."""

    def parse_rate_limit(d: dict | None) -> RateLimit | None:
        if not d:
            return None
        return RateLimit(
            utilization=d.get("utilization"),
            resets_at=d.get("resets_at"),
        )

    def parse_extra_usage(d: dict | None) -> ExtraUsage | None:
        if not d:
            return None
        return ExtraUsage(
            is_enabled=d.get("is_enabled", False),
            monthly_limit=d.get("monthly_limit"),
            used_credits=d.get("used_credits"),
            utilization=d.get("utilization"),
        )

    return Utilization(
        five_hour=parse_rate_limit(data.get("five_hour")),
        seven_day=parse_rate_limit(data.get("seven_day")),
        seven_day_oauth_apps=parse_rate_limit(data.get("seven_day_oauth_apps")),
        seven_day_opus=parse_rate_limit(data.get("seven_day_opus")),
        seven_day_sonnet=parse_rate_limit(data.get("seven_day_sonnet")),
        extra_usage=parse_extra_usage(data.get("extra_usage")),
    )


def format_utilization(util: Utilization) -> str:
    """
    Format utilization for display.

    Args:
        util: Utilization data

    Returns:
        Formatted string
    """
    lines = []

    if util.five_hour and util.five_hour.utilization is not None:
        lines.append(f"5-hour: {util.five_hour.utilization:.1f}%")

    if util.seven_day and util.seven_day.utilization is not None:
        lines.append(f"7-day: {util.seven_day.utilization:.1f}%")

    if util.extra_usage and util.extra_usage.is_enabled and util.extra_usage.used_credits is not None:
        lines.append(f"Extra credits used: ${util.extra_usage.used_credits:.2f}")

    return "\n".join(lines) if lines else "No usage data available"
