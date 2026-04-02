"""
Forward IDE ``log_event`` MCP notifications to analytics.

Migrated from: hooks/useIdeLogging.ts
"""

from __future__ import annotations

from collections.abc import Callable, Mapping


def forward_ide_log_notification(
    params: Mapping[str, object],
    log_event: Callable[[str, dict[str, bool | int | float | None]], None],
) -> None:
    raw = params.get("eventName")
    name = str(raw) if raw is not None else ""
    data = params.get("eventData")
    payload: dict[str, bool | int | float | None] = {}
    if isinstance(data, Mapping):
        for k, v in data.items():
            if isinstance(v, (bool, int, float)) or v is None:
                payload[str(k)] = v
    log_event(f"tengu_ide_{name}", payload)
