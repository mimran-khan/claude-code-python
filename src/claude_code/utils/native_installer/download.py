"""Version resolution for native installer (stub; full GCS/npm parity deferred)."""

from __future__ import annotations


async def get_latest_version(channel_or_version: str) -> str:
    stripped = channel_or_version.strip()
    return stripped if stripped else "0.0.0"
