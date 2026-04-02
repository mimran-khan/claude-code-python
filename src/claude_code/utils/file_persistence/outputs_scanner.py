"""
Scan session outputs directory for files modified after turn start.

Migrated from: utils/filePersistence/outputsScanner.ts
"""

from __future__ import annotations

import os

from ..debug import log_for_debugging
from .types import EnvironmentKind, TurnStartTime


def log_debug(message: str) -> None:
    log_for_debugging(f"[file-persistence] {message}")


def get_environment_kind() -> EnvironmentKind | None:
    kind = os.getenv("CLAUDE_CODE_ENVIRONMENT_KIND")
    if kind in ("byoc", "anthropic_cloud"):
        return kind  # type: ignore[return-value]
    return None


async def find_modified_files(turn_start_time: TurnStartTime, outputs_dir: str) -> list[str]:
    modified: list[str] = []
    try:
        for root, _dirs, files in os.walk(outputs_dir):
            for name in files:
                fp = os.path.join(root, name)
                try:
                    if os.path.islink(fp):
                        continue
                    if not os.path.isfile(fp):
                        continue
                    mtime_ms = os.path.getmtime(fp) * 1000.0
                    if mtime_ms >= turn_start_time:
                        modified.append(fp)
                except OSError:
                    continue
    except OSError:
        log_debug("Outputs directory missing or inaccessible")
        return []
    if not modified:
        log_debug("No modified files since turn start")
    else:
        log_debug(f"Found {len(modified)} modified files since turn start")
    return modified
