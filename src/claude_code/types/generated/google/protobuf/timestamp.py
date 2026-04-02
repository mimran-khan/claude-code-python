"""
Protobuf Timestamp (JSON + datetime helpers).

Migrated from: types/generated/google/protobuf/timestamp.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class Timestamp:
    """Seconds and nanos since Unix epoch (protobuf well-known type)."""

    seconds: int = 0
    nanos: int = 0


def timestamp_from_json(obj: Any) -> Timestamp:
    if not isinstance(obj, dict):
        return Timestamp()
    return Timestamp(
        seconds=int(obj.get("seconds", 0) or 0),
        nanos=int(obj.get("nanos", 0) or 0),
    )


def timestamp_to_json(message: Timestamp) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if message.seconds != 0:
        out["seconds"] = int(round(message.seconds))
    if message.nanos != 0:
        out["nanos"] = int(round(message.nanos))
    return out


def timestamp_to_datetime(t: Timestamp) -> datetime:
    return datetime.fromtimestamp(t.seconds + t.nanos / 1_000_000_000, tz=UTC)


def datetime_to_timestamp(dt: datetime) -> Timestamp:
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    ts = dt.timestamp()
    sec = int(ts)
    nanos = int(round((ts - sec) * 1_000_000_000))
    return Timestamp(seconds=sec, nanos=nanos)


def _parse_iso_z(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def datetime_to_iso_z(dt: datetime) -> str:
    """UTC ISO-8601 with Z suffix (matches JavaScript Date.toISOString())."""
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_flexible_timestamp(obj: Any) -> datetime | None:
    """
    Parse timestamp from JSON the way ts_proto fromJsonTimestamp does:
    datetime, ISO string, or {seconds, nanos} object.
    """
    if obj is None:
        return None
    if isinstance(obj, datetime):
        return obj if obj.tzinfo else obj.replace(tzinfo=UTC)
    if isinstance(obj, str):
        return _parse_iso_z(obj)
    if isinstance(obj, dict):
        return timestamp_to_datetime(timestamp_from_json(obj))
    return None
