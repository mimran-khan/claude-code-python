"""Track in-process settings writes for watcher echo suppression. Migrated from: utils/settings/internalWrites.ts"""

from __future__ import annotations

import time

_timestamps: dict[str, float] = {}


def mark_internal_write(path: str) -> None:
    _timestamps[path] = time.time() * 1000


def consume_internal_write(path: str, window_ms: float) -> bool:
    ts = _timestamps.get(path)
    if ts is not None and time.time() * 1000 - ts < window_ms:
        del _timestamps[path]
        return True
    return False


def clear_internal_writes() -> None:
    _timestamps.clear()
