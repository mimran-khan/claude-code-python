"""
Ant internal startup timing exit (CLAUDE_CODE_EXIT_AFTER_FIRST_RENDER).

Migrated from: hooks/useAfterFirstRender.ts
"""

from __future__ import annotations

import os
import sys
import time

_T0_PERF = time.perf_counter()


def _env_truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.lower() in {"1", "true", "yes", "on"}


def should_exit_after_first_render_for_ant_benchmark() -> bool:
    return os.environ.get("USER_TYPE") == "ant" and _env_truthy(
        os.environ.get("CLAUDE_CODE_EXIT_AFTER_FIRST_RENDER"),
    )


def write_startup_time_and_exit() -> None:
    """Print elapsed ms since interpreter load to stderr and exit 0 (TS: process.uptime)."""
    ms = round((time.perf_counter() - _T0_PERF) * 1000)
    sys.stderr.write(f"\nStartup time: {ms}ms\n")
    raise SystemExit(0)
